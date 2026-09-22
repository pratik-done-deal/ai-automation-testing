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
        # SuccessView.js:171 - the lavender box holding the title, hint and the option chips.
        return self.page.locator("div.rounded-xl").filter(has_text=Copy.DOC_REQUEST_TITLE).first

    def doc_option(self, doc_type):
        # Chips are <button type="button"> whose only text is the label (SuccessView.js:182-194).
        return self.doc_section.get_by_role("button", name=DOC_LABELS[doc_type], exact=True)

    def doc_option_labels(self):
        """Chip labels in display order."""
        expect(self.doc_section.get_by_role("button").first).to_be_visible()
        return [t.strip() for t in self.doc_section.get_by_role("button").all_inner_texts()]

    def is_selected(self, doc_type) -> bool:
        # The selected state is only the MUI CheckIcon inside the checkbox square (no aria-pressed).
        return self.doc_option(doc_type).locator("svg[data-testid='CheckIcon']").count() > 0

    def toggle(self, *doc_types):
        for doc_type in doc_types:
            self.doc_option(doc_type).click()

    def category_group(self, heading):
        """DR-04 (not built): the box under a category heading inside the doc section."""
        return self.doc_section.locator("div").filter(
            has=self.page.get_by_text(heading, exact=True)
        ).last

    # --- note (editable only when step 1 did not make it mandatory) ---

    @property
    def note_textarea(self):
        return self.page.locator("textarea:not([aria-hidden='true'])")

    def note_shared_text(self):
        """The read-only note under "Note shared with the founder:" (mandatory-note flow)."""
        return self.page.get_by_text(Copy.NOTE_SHARED).locator("xpath=following-sibling::div[1]")

    # --- CTAs ---

    @property
    def close_button(self):
        return self.page.get_by_role("button", name=Copy.CLOSE, exact=True)

    @property
    def cancel_button(self):
        return self.page.get_by_role("button", name=Copy.CANCEL, exact=True).last

    @property
    def primary_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^(Send request \(\d+\)|Submit)$"))

    @property
    def add_team_member(self):
        # A clickable <div>, not a button (SuccessView.js:201).
        return self.page.get_by_text(Copy.ADD_TEAM_MEMBER, exact=True)

    def proposed_slot_lines(self):
        block = self.page.get_by_text(Copy.PROPOSED_SLOTS).locator("xpath=following-sibling::div[1]")
        return [t.strip() for t in block.locator("div").all_inner_texts()]

    def submit_and_capture(self):
        """Click the primary CTA and return (request_json, response_json) of the update call."""
        with self.page.expect_response(lambda r: UPDATE_INTEREST_API in r.url, timeout=30_000) as res_info:
            self.primary_button.click()
        return res_info.value.request.post_data_json, res_info.value.json()

    def wait_until_closed(self):
        expect(self.title).to_have_count(0, timeout=15_000)
