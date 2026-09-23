import re
import sys

import pytest
from playwright.sync_api import expect

from config import settings
from pages.shared.base_page import BasePage
from pages.buyer_module.buyer_cue_card_page import BuyerCueCardPage

CUE_CARD_HREF = re.compile(r"buyer/cue-card/([^/?#]+)")


class CueCardLoadError(Exception):
    """A listing whose cue card data didn't load; `cue_card.page` is the (still open) tab."""

    def __init__(self, cue_card, reason):
        super().__init__(reason)
        self.cue_card = cue_card


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
        """Click that card's View Listing and return the cue card opened in the new tab.

        Raises CueCardLoadError (with the tab still open) when the card's data request fails or
        never arrives, so callers can skip that company.
        """
        link = self.page.locator(f"a[href*='buyer/cue-card/{uid}']").filter(has_text="View Listing").first
        link.scroll_into_view_if_needed()
        context = self.page.context
        responses = []

        def on_response(response):
            if BuyerCueCardPage.CUE_CARD_API.search(response.url):
                responses.append(response)

        context.on("response", on_response)  # registered before the click: the tab fetches at once
        try:
            with context.expect_page() as new_tab:
                link.click()
            tab = new_tab.value
            for _ in range(40):  # up to ~20s
                if any(r.frame.page == tab for r in responses):
                    break
                tab.wait_for_timeout(500)
        finally:
            context.remove_listener("response", on_response)

        cue_card = BuyerCueCardPage(tab)
        response = next((r for r in responses if r.frame.page == tab), None)
        if response is None:
            raise CueCardLoadError(cue_card, f"no company/cue/card/fetch request within 20s (tab at {tab.url})")
        if not response.ok:
            raise CueCardLoadError(cue_card, f"company/cue/card/fetch returned HTTP {response.status}")
        tab.wait_for_load_state("networkidle")
        cue_card.cue_card_payload = response.json()
        return cue_card

    def back_to_browse(self, cue_card: BuyerCueCardPage):
        cue_card.page.close()
        self.page.bring_to_front()

    def open_next_fresh_listing(self, skip: set):
        """Open listings in turn until one still offers Express Interest; returns (uid, cue_card).

        Every uid opened is added to `skip`, so a company is never offered twice. Companies the buyer
        already expressed interest in are closed again and passed over.
        """
        for _ in range(settings.browse_max_cards):
            uid = next((u for u in self.listing_uids() if u not in skip), None)
            if uid is None:
                if not self.load_more():
                    break
                continue
            skip.add(uid)
            try:
                cue_card = self.open_listing(uid)
            except CueCardLoadError as error:
                sys.__stdout__.write(f"\n  skipped {uid}: {error}\n")
                self.back_to_browse(error.cue_card)
                continue
            if cue_card.can_express_interest():
                return uid, cue_card
            self.back_to_browse(cue_card)
        pytest.skip(f"No company on /buyer/browse still offers Express Interest (skipped {len(skip)}); "
                    "raise DD_BROWSE_MAX_CARDS or reset the buyer's deals")
