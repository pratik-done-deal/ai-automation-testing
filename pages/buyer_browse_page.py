import re

import pytest
from playwright.sync_api import expect

from config import settings
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
            cue_card = self.open_listing(uid)
            if cue_card.can_express_interest():
                return uid, cue_card
            self.back_to_browse(cue_card)
        pytest.skip(f"No company on /buyer/browse still offers Express Interest (skipped {len(skip)}); "
                    "raise DD_BROWSE_MAX_CARDS or reset the buyer's deals")

    def open_journey_card(self, used: set, outside_pref: bool, limit: int):
        """Open listings until one matches `outside_pref`; returns (uid, cue_card, modal) with the
        Express Interest modal open, or None. The tab stays open for the rest of the session.

        A card of the other kind met on the way is kept (not closed) for the next call.
        """
        self.seen = getattr(self, "seen", set(used))
        self.parked = getattr(self, "parked", {})
        if outside_pref in self.parked:
            uid, cue_card, modal = self.parked.pop(outside_pref)
            used.add(uid)
            return uid, cue_card, modal
        for _ in range(limit):
            uid, cue_card = self.open_next_fresh_listing(self.seen)
            modal = cue_card.click_express_interest()
            # The Figma warning banner isn't built; the mandatory note is the only sign in the app.
            is_outside = cue_card.note_mandatory or modal.note_label.count() > 0
            if is_outside == outside_pref:
                used.add(uid)
                return uid, cue_card, modal
            if is_outside not in self.parked:
                self.parked[is_outside] = (uid, cue_card, modal)
            else:
                self.back_to_browse(cue_card)
        return None
