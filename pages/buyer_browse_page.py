import re

from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.buyer_cue_card_page import BuyerCueCardPage

CUE_CARD_HREF = re.compile(r"buyer/cue-card/([^/?#]+)")


class BuyerBrowsePage(BasePage):
    """Buyer Browse Companies: /buyer/browse - grid of mini cue cards with a 'View Listing' link each.

    'View Listing' is an <a target="_blank"> (BuyerListCard), so each listing opens in a new tab.
    """

    def open_browse(self):
        self.open("buyer/browse")
        expect(self.view_listing_links().first).to_be_visible(timeout=30_000)
        return self

    def view_listing_links(self):
        return self.page.locator("a").filter(has_text=re.compile(r"^\s*View Listing\s*$"))

    def listing_uids(self):
        uids = []
        for href in self.view_listing_links().evaluate_all("els => els.map(e => e.getAttribute('href') || '')"):
            match = CUE_CARD_HREF.search(href)
            if match and match.group(1) not in uids:
                uids.append(match.group(1))
        return uids

    def load_more(self) -> bool:
        """Scroll to the bottom to trigger the next page of cards; True if new cards appeared."""
        before = self.view_listing_links().count()
        self.page.mouse.wheel(0, 20_000)
        self.page.wait_for_timeout(2_500)
        self.page.wait_for_load_state("networkidle")
        return self.view_listing_links().count() > before

    def open_listing(self, uid: str) -> BuyerCueCardPage:
        """Click that card's View Listing and return the cue card opened in the new tab."""
        link = self.page.locator(f"a[href*='buyer/cue-card/{uid}']").filter(has_text="View Listing").first
        link.scroll_into_view_if_needed()
        context = self.page.context
        with context.expect_page() as new_tab:
            with context.expect_event("response", lambda r: BuyerCueCardPage.CUE_CARD_API.search(r.url) and r.ok,
                                      timeout=30_000) as cue_card_response:
                link.click()
        tab = new_tab.value
        tab.wait_for_load_state("networkidle")
        cue_card = BuyerCueCardPage(tab)
        cue_card.cue_card_payload = cue_card_response.value.json()
        return cue_card

    def back_to_browse(self, cue_card: BuyerCueCardPage):
        cue_card.page.close()
        self.page.bring_to_front()
