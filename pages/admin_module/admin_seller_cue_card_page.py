import re

import pytest

from playwright.sync_api import Error as PlaywrightError, expect

from constants import StarSellerCopy as Ssc
from locators.admin import star_seller_locators as L
from pages.admin_module.additional_details_modal import AdditionalDetailsModal
from pages.admin_module.admin_sellers_page import AdminSellersPage
from pages.admin_module.company_objective_modal import CompanyObjectiveModal
from pages.admin_module.cue_card_edit_modal import CueCardEditModal
from pages.shared.base_page import BasePage

DELETE_DOC_API = "document/delete"
UPLOAD_DOC_API = "document/user/upload"   # ENDPOINT.DOCUMENT.upload, used by the Data Room upload modal


class AdminSellerCueCardPage(BasePage):
    """Admin / biz user seller cue card: /admin/notes/<uid>, "Cue card" tab (SellerNotesContainer > NewCueCard).

    The right rail holds "Company's Objective" and "Additional details for this seller"; both open
    their modal from an "Edit" button and save with PUT company/update/admin, then reload the page.

    open_seller gets there like a user: Sellers > "Star Sellers" / "Non Star Sellers" > search the
    S-id > Actions "View". The cue card opens in a new tab and `self.page` moves to it; the list
    stays open in the tab the page object was made with.
    """

    def __init__(self, page):
        super().__init__(page)
        self.list_page = page

    def open_seller(self, uid):
        from utils.ssf_browse import describe   # read-only: the seller's S-id and star flag
        facts = describe(uid)
        tab = Ssc.STAR_SELLERS_TAB if facts["star"] else Ssc.NON_STAR_SELLERS_TAB
        sellers = AdminSellersPage(self.list_page).open_tab(tab).search(facts["sid"])
        if not sellers.has_row(facts["sid"]):
            # A biz user sees only their own sellers; a seller from an earlier admin case may not be one.
            pytest.skip(f"{facts['sid']} is not in this user's \"{tab}\" list, so it can't be opened from there")
        if self.page is not self.list_page:
            self.page.close()
        self.page = sellers.view_cue_card(facts["sid"], uid)
        self.uid = uid
        return self._wait_loaded()

    def _wait_loaded(self):
        expect(self.block(Ssc.ADDITIONAL_DETAILS_BLOCK)).to_be_visible(timeout=30_000)
        self.page.wait_for_load_state("networkidle")
        return self

    def reload(self):
        """Reload the cue card tab. Saves (objective, additional details) make the app reload the page
        itself; if that reload is still going, ours is aborted (net::ERR_ABORTED), which is harmless:
        the page is being reloaded either way."""
        self.page.wait_for_load_state("networkidle")
        try:
            self.page.reload()
        except PlaywrightError as error:
            if "ERR_ABORTED" not in str(error):
                raise
            self.page.wait_for_load_state("load")
        return self._wait_loaded()

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
        """Delete every file in the Data Room "Pitchdeck" subsection. Returns (deleted, left).

        Stops at the first file the app refuses to delete (e.g. "This document has already been
        shared with the buyer and can't be deleted"), so a refused delete can't loop forever."""
        files = self.page.locator(L.DATA_ROOM_SUBSECTION).filter(
            has=self.page.get_by_text(Ssc.DATA_ROOM_PITCHDECK, exact=True)).locator(L.DATA_ROOM_FILE)
        deleted = 0
        while files.count():
            before = files.count()
            with self.page.expect_response(lambda r: DELETE_DOC_API in r.url, timeout=30_000):
                files.first.locator(L.DATA_ROOM_DELETE).click()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1_000)  # the list re-renders after updateCuecardRefresh
            if files.count() >= before:
                break
            deleted += 1
        return deleted, files.count()

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
