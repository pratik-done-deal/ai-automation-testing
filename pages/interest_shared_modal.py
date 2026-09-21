import re

from playwright.sync_api import expect

from constants import DOC_LABELS, Copy
from pages.base_page import BasePage

UPDATE_INTEREST_API = "deal/capture/interest/update"


class InterestSharedModal(BasePage):
    """Step 2 of the buyer flow: SuccessView with the one-time document request."""

    def wait_until_open(self):
        expect(self.page.get_by_text(Copy.SUCCESS_TITLE)).to_be_visible(timeout=30_000)

    @property
    def title(self):
        return self.page.get_by_text(Copy.SUCCESS_TITLE)

    @property
    def doc_section(self):
        return self.page.locator("div.rounded-xl").filter(has_text=Copy.DOC_REQUEST_TITLE).first

    def doc_option(self, doc_type):
        return self.doc_section.get_by_role("button", name=DOC_LABELS[doc_type], exact=True)

    def doc_option_labels(self):
        return [t.strip() for t in self.doc_section.get_by_role("button").all_inner_texts()]

    def is_selected(self, doc_type) -> bool:
        # Selected options render a MUI CheckIcon inside the checkbox square.
        return self.doc_option(doc_type).locator("svg[data-testid='CheckIcon']").count() > 0

    def toggle(self, *doc_types):
        for doc_type in doc_types:
            self.doc_option(doc_type).click()

    @property
    def close_button(self):
        return self.page.get_by_role("button", name=Copy.CLOSE, exact=True)

    @property
    def cancel_button(self):
        return self.page.get_by_role("button", name=Copy.CANCEL, exact=True).last

    @property
    def primary_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^(Send request \(\d+\)|Submit)$"))

    def proposed_slot_lines(self):
        block = self.page.get_by_text(Copy.PROPOSED_SLOTS).locator("xpath=following-sibling::div[1]")
        return [t.strip() for t in block.locator("div").all_inner_texts()]

    def submit_and_capture(self):
        """Click the primary CTA and return (request_json, response_json) of the update call."""
        with self.page.expect_request(lambda r: UPDATE_INTEREST_API in r.url) as req_info:
            with self.page.expect_response(lambda r: UPDATE_INTEREST_API in r.url) as res_info:
                self.primary_button.click()
        return req_info.value.post_data_json, res_info.value.json()

    def wait_until_closed(self):
        expect(self.title).to_have_count(0, timeout=15_000)
