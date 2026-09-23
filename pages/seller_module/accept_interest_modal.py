import re

from playwright.sync_api import expect

from constants import DOC_LABELS, ENGAGEMENT_LETTER_DOC_TYPE, PITCHDECK, Copy, files_in_data_room, remove_attached_label
from pages.shared.base_page import BasePage

SELLER_ACTION_API = "deal/seller"
DEAL_SHARE_API = "document/deal/share"
DOCUMENT_QUERY_API = "document/query"
UPLOAD_API = "document/user/upload"
SELLER_SLOTS_API = "meeting/slots/seller"


def seller_label(doc_type):
    # IntroductionSetupModal.js:102 spells the deck "Pitch Deck"; other rows use DATAROOM_KEY_LABEL_MAP.
    return Copy.SELLER_PITCH_DECK_LABEL if doc_type == PITCHDECK else DOC_LABELS[doc_type]


LABEL_TO_TYPE = {seller_label(t): t for t in DOC_LABELS}


def _ends_with(path):
    return lambda r: r.url.split("?")[0].rstrip("/").endswith(path)


def files_by_type(document_query_payload):
    """What the modal lists per row: document/query userDocMap minus engagement letters (utils.js:86-105)."""
    user_doc_map = ((document_query_payload or {}).get("data") or {}).get("userDocMap") or {}
    files = {}
    for doc_type, docs in user_doc_map.items():
        if doc_type == ENGAGEMENT_LETTER_DOC_TYPE:
            continue
        kept = [d for d in (docs or []) if not re.match(r"^signed_.+_EL\.pdf$", d.get("fileName") or "", re.I)]
        if kept:
            files[doc_type] = kept
    return files


class AcceptInterestModal(BasePage):
    """Seller accept flow: IntroductionSetupModal ("Accept investor interest?")."""

    documents_payload = None  # document/query response the modal was built from

    def wait_until_open(self):
        expect(self.page.get_by_role("heading", name=Copy.ACCEPT_MODAL_TITLE)).to_be_visible(timeout=20_000)

    @property
    def heading(self):
        return self.page.get_by_role("heading", name=Copy.ACCEPT_MODAL_TITLE)

    @property
    def identity_line(self):
        return self.page.get_by_text(re.compile(rf"^{Copy.IDENTITY_REVEALED} .+ over email\.$"))

    @property
    def investor_message(self):
        return self.page.get_by_text(Copy.INVESTOR_MESSAGE, exact=True).locator("xpath=following-sibling::p[1]")

    # --- "The investor would like to discuss" section ---

    @property
    def requested_section(self):
        return self.page.locator("section").filter(has_text=Copy.INVESTOR_WANTS_TO_DISCUSS).first

    @property
    def counter(self):
        # Attached rows / total rows, e.g. "1/3" (IntroductionSetupModal.js:267-269).
        return self.requested_section.get_by_text(re.compile(r"^\d+/\d+$"))

    def rows(self):
        # Each RequestedDocumentRow is a direct child of the rows column (IntroductionSetupModal.js:271).
        return self.requested_section.locator("div.flex-col.gap-3 > div")

    @staticmethod
    def _label_box(row):
        return row.locator("div.min-w-0 > div").first

    @staticmethod
    def _status_box(row):
        return row.locator("div.min-w-0 > div").nth(1)

    def row_labels(self):
        """Row labels in display order, without the required marker ("Pitch Deck *" -> "Pitch Deck")."""
        expect(self.rows().first).to_be_visible(timeout=15_000)
        return [re.sub(r"\s*\*\s*$", "", self._label_box(r).inner_text().strip()) for r in self.rows().all()]

    def requested_row_types(self):
        return [LABEL_TO_TYPE.get(label, label) for label in self.row_labels()]

    def requested_row(self, doc_type):
        label = re.escape(seller_label(doc_type))
        return self.rows().filter(
            has=self.page.locator("div.min-w-0 > div").filter(has_text=re.compile(rf"^\s*{label}(\s*\*)?\s*$"))
        ).first

    def row_is_required(self, doc_type) -> bool:
        return self._label_box(self.requested_row(doc_type)).inner_text().strip().endswith("*")

    def row_status(self, doc_type) -> str:
        return self._status_box(self.requested_row(doc_type)).inner_text().strip()

    def expected_status(self, doc_type) -> str:
        """Status line RequestedDocumentRow should show before anything is attached (:42-46)."""
        count = len(files_by_type(self.documents_payload).get(doc_type, []))
        return files_in_data_room(count) if count else Copy.NOT_UPLOADED_YET

    def row_button(self, doc_type, name):
        return self.requested_row(doc_type).get_by_role("button", name=name, exact=True)

    def remove_button(self, doc_type):
        return self.requested_row(doc_type).get_by_role("button", name=remove_attached_label(seller_label(doc_type)))

    def attach_first_file(self, doc_type):
        """Open the row's Attach menu (MUI Menu portal) and pick its first file; returns the file name."""
        self.row_button(doc_type, Copy.ATTACH).click()
        item = self.page.get_by_role("menuitem").first
        expect(item).to_be_visible()
        name = item.inner_text().strip()
        item.click()
        expect(self.page.get_by_role("menu")).to_have_count(0)
        return name

    def upload_into_row(self, doc_type, file_path):
        """Upload through the row's hidden file input; returns the upload request's raw body."""
        row = self.requested_row(doc_type)
        with self.page.expect_response(lambda r: UPLOAD_API in r.url, timeout=60_000) as res:
            row.locator("input[type='file']").set_input_files(str(file_path))
        return res.value.request.post_data_buffer or b""

    @property
    def pitch_deck_error(self):
        return self.requested_section.get_by_text(re.compile(rf"^{Copy.PITCH_DECK_MANDATORY}"))

    # --- timeslots ---

    @property
    def slot_options(self):
        return self.page.get_by_role("radio")

    def choose_slot(self, index=0):
        self.slot_options.nth(index).click()

    # --- CTAs ---

    @property
    def accept_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^(Accept|Accepting…)$")).last

    @property
    def cancel_button(self):
        return self.page.get_by_role("button", name=Copy.CANCEL, exact=True).last

    @property
    def close_icon(self):
        return self.page.get_by_role("button", name="Close", exact=True).last

    def accept_and_capture(self):
        """Click Accept and return the deal/seller request body."""
        with self.page.expect_request(_ends_with(SELLER_ACTION_API)) as req:
            self.accept_button.click()
        return req.value.post_data_json

    def wait_until_closed(self):
        expect(self.heading).to_have_count(0, timeout=20_000)
