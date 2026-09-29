import re

from playwright.sync_api import expect

from constants import StarSellerCopy as Ssc
from locators.admin import star_seller_locators as L
from pages.admin_module.additional_details_modal import is_admin_save
from pages.shared.base_page import BasePage
from utils.sessions import track_listener

STAR_RE = re.compile(Ssc.STAR_WORD, re.I)
UPLOAD_ERROR_RE = re.compile(r"error|fail|went wrong|try again", re.I)
PDF_RULE_RE = re.compile(r"pdf", re.I)


class CompanyObjectiveModal(BasePage):
    """"Edit Company's Objective" (CompanyObjectiveModal: "Primary Objective*" CustomSelect, Cancel, Confirm).

    Confirm saves (PUT company/update/admin) and reloads the page. star-seller-fundraising: for a star
    seller, picking an objective whose document is missing from the cue card (investment teaser for
    Acquisition, pitch deck for Funding) shows, right away and below the dropdown, a message that mentions
    "star" and names the document, then a "<document> Required [Upload]" box, and disables Confirm. After
    an upload the box shows "<file> / Added to the data room" and Confirm is enabled again.
    """

    def wait_open(self):
        expect(self.root).to_be_visible(timeout=15_000)
        return self

    @property
    def root(self):
        return self.page.locator(L.MODAL).filter(has_text=Ssc.OBJECTIVE_TITLE)

    def select_primary(self, label):
        self.root.locator(L.OBJECTIVE_DROPDOWN).first.click()
        self.root.locator(L.OBJECTIVE_OPTION).filter(has_text=re.compile(rf"^\s*{label}\s*$")).first.click()
        return self

    @property
    def confirm_button(self):
        return self.root.get_by_role("button", name=Ssc.CONFIRM, exact=True)

    def expect_confirm_disabled(self):
        expect(self.confirm_button).to_be_disabled(timeout=10_000)

    def expect_confirm_enabled(self):
        expect(self.confirm_button).to_be_enabled(timeout=10_000)

    def confirm(self):
        """Click Confirm. Returns True when the save request went out (the page then reloads);
        False, without clicking, while Confirm is disabled."""
        if self.confirm_button.is_disabled():
            return False
        saves = []
        track_listener(self.page, "response", lambda r: saves.append(r) if is_admin_save(r) else None)
        self.confirm_button.click()
        self.page.wait_for_timeout(2_000)
        self.page.wait_for_load_state("networkidle")
        return bool(saves)

    def confirm_and_save(self):
        with self.page.expect_response(is_admin_save, timeout=30_000):
            self.confirm_button.click()
        self.page.wait_for_load_state("networkidle")

    def cancel(self):
        self.root.get_by_role("button", name=Ssc.CANCEL, exact=True).click()
        expect(self.root).to_have_count(0)

    # --- the star-seller message and its upload option ---

    @property
    def star_message(self):
        """Text in the modal (or a snackbar) that mentions "star"; the modal has no other "star" copy."""
        return self.page.locator(L.SNACKBAR).filter(has_text=STAR_RE).or_(self.root.get_by_text(STAR_RE))

    def expect_star_message(self):
        message = self.star_message.last
        expect(message).to_be_visible(timeout=10_000)
        return message, " ".join(message.inner_text().split())

    def expect_no_star_message(self):
        expect(self.star_message).to_have_count(0)

    @property
    def upload_option(self):
        """The "Upload" button of the prompt's "<document> Required" box (not the message, which also says "Upload")."""
        return self.root.locator(L.UPLOAD_OPTION).filter(has_text=re.compile(rf"^\s*{Ssc.UPLOAD}\s*$")).first

    @property
    def required_tag(self):
        return self.root.get_by_text(Ssc.REQUIRED_TAG, exact=True)

    @property
    def uploaded_file(self):
        """The box that replaces the prompt after an upload: "<file name>" over "Added to the data room"."""
        return self.root.get_by_text(Ssc.ADDED_TO_DATA_ROOM, exact=True).locator("xpath=..")

    def expect_uploaded(self):
        """After an upload: the star message is gone, the file box shows, Confirm is enabled. Returns the box text."""
        expect(self.star_message).to_have_count(0, timeout=30_000)
        expect(self.uploaded_file).to_be_visible(timeout=15_000)
        self.expect_confirm_enabled()
        return " ".join(self.uploaded_file.inner_text().split())

    @property
    def file_input(self):
        return self.root.locator(L.FILE_INPUT).first

    def upload(self, path):
        expect(self.file_input).to_have_count(1, timeout=10_000)
        self.file_input.set_input_files(str(path))
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def upload_error(self):
        return self.page.locator(L.SNACKBAR).filter(has_text=UPLOAD_ERROR_RE).or_(
            self.root.get_by_text(UPLOAD_ERROR_RE))

    @property
    def pdf_rule_message(self):
        """A message naming PDF after a wrong file type (the static helper text doesn't count)."""
        rule = re.compile(r"(only|allowed|supported|accepted|invalid|format|type)[^.]*pdf|pdf[^.]*(only|allowed|"
                          r"supported|accepted)", re.I)
        return self.page.locator(L.SNACKBAR).filter(has_text=PDF_RULE_RE).or_(self.root.get_by_text(rule))
