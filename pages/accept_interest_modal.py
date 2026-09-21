import re

from playwright.sync_api import expect

from constants import DOC_LABELS, PITCHDECK, Copy
from pages.base_page import BasePage

SELLER_ACTION_API = "deal/seller"
UPLOAD_API = "document/user/upload"


def seller_label(doc_type):
    # IntroductionSetupModal spells the deck "Pitch Deck"; every other row uses DATAROOM_KEY_LABEL_MAP.
    return Copy.SELLER_PITCH_DECK_LABEL if doc_type == PITCHDECK else DOC_LABELS[doc_type]


class AcceptInterestModal(BasePage):
    """Seller accept flow: IntroductionSetupModal."""

    def wait_until_open(self):
        expect(self.page.get_by_role("button", name=re.compile(r"^(Accept|Accepting…)$")).last).to_be_visible(timeout=20_000)
        self.page.wait_for_load_state("networkidle")

    @property
    def investor_message(self):
        return self.page.get_by_text(Copy.INVESTOR_MESSAGE).locator("xpath=following-sibling::p[1]")

    @property
    def requested_section(self):
        return self.page.locator("section").filter(has_text=Copy.INVESTOR_WANTS_TO_DISCUSS).first

    def requested_row(self, doc_type):
        return self.requested_section.locator("div").filter(
            has=self.page.get_by_text(seller_label(doc_type), exact=True)
        ).last

    def requested_row_labels(self):
        found = []
        for doc_type in DOC_LABELS:
            if self.requested_section.get_by_text(seller_label(doc_type), exact=True).count():
                found.append(doc_type)
        return found

    def upload_into_row(self, doc_type, file_path):
        row = self.requested_row(doc_type)
        with self.page.expect_response(lambda r: UPLOAD_API in r.url, timeout=60_000):
            with self.page.expect_file_chooser() as chooser:
                row.get_by_role("button", name=re.compile(r"^Upload")).click()
            chooser.value.set_files(file_path)

    def remove_attachment(self, doc_type):
        self.requested_row(doc_type).get_by_title("Remove").click()

    @property
    def slot_options(self):
        return self.page.get_by_role("radio")

    def choose_slot(self, index=0):
        self.slot_options.nth(index).click()

    @property
    def accept_button(self):
        return self.page.get_by_role("button", name=Copy.ACCEPT, exact=True).last

    @property
    def cancel_button(self):
        return self.page.get_by_role("button", name=Copy.CANCEL, exact=True).last

    def accept_and_capture(self):
        with self.page.expect_request(lambda r: r.url.rstrip("/").endswith(SELLER_ACTION_API)) as req:
            self.accept_button.click()
        return req.value.post_data_json
