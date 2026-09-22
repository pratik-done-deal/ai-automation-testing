import re

from playwright.sync_api import expect

from constants import DOC_LABELS, Copy
from pages.base_page import BasePage
from pages.express_interest_modal import ExpressInterestModal
from utils.api_client import find_key


class BuyerCueCardPage(BasePage):
    """Buyer detailed cue card: /buyer/cue-card/:uid"""

    # /buyer/cue-card/:uid renders NewCueCard with customApiUrl=ENDPOINT.CUECARD.fetch() (CuecardContainer).
    CUE_CARD_API = re.compile(r"company/cue/card/fetch(\?|$)")

    def open_cue_card(self, uid: str, query: str = ""):
        try:
            with self.page.expect_response(lambda r: self.CUE_CARD_API.search(r.url), timeout=30_000) as res:
                self.open(f"buyer/cue-card/{uid}{query}")
        except Exception as exc:
            raise AssertionError(f"No company/cue/card/fetch response within 30s after opening cue card {uid} "
                                 f"(page is now {self.page.url})") from exc
        response = res.value
        if not response.ok:
            raise AssertionError(f"company/cue/card/fetch for {uid} returned HTTP {response.status}: "
                                 f"{response.text()[:300]}")
        self.cue_card_payload = response.json()
        return self

    @property
    def requested_documents(self):
        """`requestedDocuments` from the cue card fetch: [{docType, fulfilled}]."""
        return find_key(self.cue_card_payload or {}, "requestedDocuments") or []

    @property
    def deal_status(self):
        return ((self.cue_card_payload or {}).get("data") or {}).get("dealStatus")

    @property
    def note_mandatory(self) -> bool:
        """Company outside the buyer's preferences: the founder note is required (actionHelper.js:52)."""
        return bool(find_key(self.cue_card_payload or {}, "expressNoteIsMandatory"))

    @property
    def title(self) -> str:
        # Same field NewCueCard uses for the document title (res.data.title), e.g. "S6604 : Fintech > Payments".
        data = (self.cue_card_payload or {}).get("data") or {}
        return data.get("title") or self.page.title()

    # --- right rail actions (BuyerActionsCard.js) ---

    @property
    def express_interest_button(self):
        # A <div>, not a <button>; its text also carries "54/200 deals used", so match by class.
        return self.page.locator(".express-interest-cta").first

    @property
    def expressed_interest_button(self):
        return self.page.get_by_text(re.compile(r"^(Expressed Interest|Connected with Founder)$")).first

    def can_express_interest(self) -> bool:
        """False when the buyer already expressed interest (PostInterestActions renders instead)."""
        try:
            self.express_interest_button.or_(self.expressed_interest_button).first.wait_for(timeout=15_000)
        except Exception:
            return False
        return self.express_interest_button.is_visible()

    def click_express_interest(self) -> ExpressInterestModal:
        self.express_interest_button.click()
        # On the buyer's last free deal a "Send Interest" confirmation comes first (ConfirmExpressModal).
        send_interest = self.page.get_by_role("button", name="Send Interest")
        modal = ExpressInterestModal(self.page)
        expect(send_interest.or_(modal.slot_label).first).to_be_visible(timeout=15_000)
        if send_interest.is_visible():
            send_interest.click()
        modal.wait_until_open()
        return modal

    # --- "You flagged for the intro call" card (RequestedDocuments.js) ---

    @property
    def flagged_card(self):
        # .last = the innermost matching box (ancestors come first in document order).
        return self.page.locator("div.rounded-2xl").filter(
            has=self.page.get_by_role("heading", name=Copy.FLAGGED_TITLE)
        ).last

    def flagged_chips(self):
        # Chips use Tailwind's "!rounded-full" (important modifier), so match on the wrapping flex-wrap row.
        return self.flagged_card.locator("div.flex-wrap > div")

    def flagged_chip(self, doc_type: str):
        return self.flagged_chips().filter(has_text=DOC_LABELS[doc_type]).first

    def flagged_labels(self):
        expect(self.flagged_chips().first).to_be_visible(timeout=15_000)
        return [t.strip() for t in self.flagged_chips().locator("span").all_inner_texts()]

    def chip_is_fulfilled(self, doc_type: str) -> bool:
        # Fulfilled chips render the green SharedIcon (circle fill #12B76A); pending chips the purple doc icon.
        return self.flagged_chip(doc_type).locator("circle[fill='#12B76A']").count() > 0

    def flagged_card_controls(self):
        """Anything on the flagged card a buyer could use to change the request (there should be none)."""
        return self.flagged_card.locator("button, input, textarea, select, [role='button'], .cursor-pointer")

    def expect_no_flagged_card(self):
        # Wait for the right rail first, so "absent" is not just "not rendered yet".
        expect(self.express_interest_button.or_(self.expressed_interest_button).first).to_be_visible(timeout=15_000)
        expect(self.page.get_by_text(Copy.FLAGGED_TITLE)).to_have_count(0)
