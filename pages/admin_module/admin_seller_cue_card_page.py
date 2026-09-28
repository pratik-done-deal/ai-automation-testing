import re

from playwright.sync_api import expect

from constants import ADMIN_SELLER_NOTES_PATH, StarSellerCopy as Ssc
from locators.admin import star_seller_locators as L
from pages.admin_module.additional_details_modal import AdditionalDetailsModal
from pages.admin_module.company_objective_modal import CompanyObjectiveModal
from pages.admin_module.cue_card_edit_modal import CueCardEditModal
from pages.shared.base_page import BasePage

DELETE_DOC_API = "document/delete"
UPLOAD_DOC_API = "document/user/upload"   # ENDPOINT.DOCUMENT.upload, used by the Data Room upload modal


class AdminSellerCueCardPage(BasePage):
    """Admin / biz user seller cue card: /admin/notes/<uid>, "Cue card" tab (SellerNotesContainer > NewCueCard).

    The right rail holds "Company's Objective" and "Additional details for this seller"; both open
    their modal from an "Edit" button and save with PUT company/update/admin, then reload the page.
    """

    def open_seller(self, uid):
        self.uid = uid
        self.open(ADMIN_SELLER_NOTES_PATH.format(uid=uid))
        expect(self.block(Ssc.ADDITIONAL_DETAILS_BLOCK)).to_be_visible(timeout=30_000)
        return self

    def reload(self):
        return self.open_seller(self.uid)

    def seller_heading(self):
        """("S5133", "test company") from the page heading "S5133: test company"."""
        heading = self.page.locator("h1").filter(has_text=re.compile(r"^S\d+:")).first
        expect(heading).to_be_visible(timeout=15_000)
        sid, name = heading.inner_text().split(":", 1)
        return sid.strip(), name.strip()

    # --- rail blocks ---

    def block(self, title):
        return self.page.locator(L.H6).filter(has_text=re.compile(rf"^\s*{re.escape(title)}\s*$")).locator("xpath=..")

    def _block_text(self, title):
        block = self.block(title)
        expect(block).to_be_visible(timeout=15_000)
        return " ".join(block.inner_text().split())

    def star_value(self):
        """"Yes", "No", or None when star was never set (AdditionalFieldDetails renders no "Star:" row)."""
        match = re.search(r"\bStar:\s*(Yes|No)\b", self._block_text(Ssc.ADDITIONAL_DETAILS_BLOCK))
        return match.group(1) if match else None

    def additional_detail_value(self, label):
        """The chip text after "<label>:" in the additional details block ("" when the row isn't shown)."""
        row = self.block(Ssc.ADDITIONAL_DETAILS_BLOCK).locator("div.flex").filter(
            has=self.page.get_by_text(re.compile(rf"^\s*{re.escape(label)}:\s*$")))
        if not row.count():
            return ""
        return " ".join(row.last.inner_text().split()).split(":", 1)[1].strip()

    def primary_objective(self):
        """"Funding" / "Acquisition" from "Primary: <objective> | Secondary: ..." (lower-case in the DOM)."""
        match = re.search(r"Primary:\s*(\w+)", self._block_text(Ssc.OBJECTIVE_BLOCK))
        return match.group(1).capitalize() if match else None

    def open_additional_details(self):
        self.block(Ssc.ADDITIONAL_DETAILS_BLOCK).get_by_role(
            "button", name=re.compile(rf"^({Ssc.EDIT}|{Ssc.ADD})$")).click()
        return AdditionalDetailsModal(self.page).wait_open()

    def open_objective(self):
        self.block(Ssc.OBJECTIVE_BLOCK).get_by_role("button", name=Ssc.EDIT, exact=True).click()
        return CompanyObjectiveModal(self.page).wait_open()

    def open_cue_card_edit(self):
        self.page.get_by_role("button", name=Ssc.EDIT_CUE_CARD, exact=True).click()
        return CueCardEditModal(self.page).wait_open()

    def pitch_deck_files(self):
        """File names listed under "Pitch Deck" in "Important Documents" (CuecardPitchDeck)."""
        label = self.page.get_by_text(Ssc.PITCH_DECK_LIST_LABEL, exact=True)
        if not label.count():
            return []
        files = label.first.locator("xpath=following-sibling::div[1]").locator("span")
        return [name.strip() for name in files.all_inner_texts() if name.strip()]

    def cue_card_visible(self):
        return self.block(Ssc.OBJECTIVE_BLOCK).is_visible()

    # --- Data Room tab ---

    def open_data_room(self):
        self.page.locator(L.TAB).filter(has_text=re.compile(rf"^\s*{Ssc.DATA_ROOM_TAB}\s*$")).first.click()
        self.page.wait_for_load_state("networkidle")
        return self

    def delete_all_pitch_decks(self):
        """Delete every file in the Data Room "Pitchdeck" subsection. Returns how many were deleted."""
        section = self.page.locator(L.DATA_ROOM_SUBSECTION).filter(
            has=self.page.get_by_text(Ssc.DATA_ROOM_PITCHDECK, exact=True))
        deleted = 0
        while section.count() and section.first.locator(L.DATA_ROOM_FILE).count():
            with self.page.expect_response(lambda r: DELETE_DOC_API in r.url, timeout=30_000):
                section.first.locator(L.DATA_ROOM_FILE).first.locator(L.DATA_ROOM_DELETE).click()
            deleted += 1
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1_000)  # the list re-renders after updateCuecardRefresh
        return deleted

    def upload_pitch_deck(self, path):
        """Data Room > "Upload Document" > "Pitch Deck" > the PDF (DocumentUploadModal)."""
        self.page.get_by_role("button", name=Ssc.UPLOAD_DOCUMENT).click()
        modal = self.page.locator(L.MODAL).filter(has_text=Ssc.SELECT_DOCUMENT_TYPE)
        expect(modal).to_be_visible(timeout=10_000)
        modal.locator(L.OBJECTIVE_DROPDOWN).first.click()
        modal.locator(L.OBJECTIVE_OPTION).filter(has_text=re.compile(rf"^\s*{Ssc.PITCH_DECK_LIST_LABEL}\s*$")).first.click()
        with self.page.expect_response(lambda r: UPLOAD_DOC_API in r.url, timeout=60_000):
            modal.locator(L.FILE_INPUT).first.set_input_files(str(path))
        expect(modal).to_have_count(0, timeout=15_000)
        return self
