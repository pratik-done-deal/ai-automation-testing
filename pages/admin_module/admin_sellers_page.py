import re

from playwright.sync_api import expect

from constants import ADMIN_SELLERS_PATH, StarSellerCopy as Ssc
from locators.admin import star_seller_locators as L
from pages.shared.base_page import BasePage


class AdminSellersPage(BasePage):
    """Admin Sellers list: /admin/seller (WrappedWithFilters). Star sellers show "⭐️" after the S-id
    (SellerDataModel.js:84). The search (magnifier) searches inside the open tab; a searchString in
    the URL would drop the tab's filter and show "Verified Sellers" instead."""

    def open_tab(self, tab):
        self.open(ADMIN_SELLERS_PATH)
        self.page.locator(L.TAB).filter(has_text=re.compile(rf"^\s*{re.escape(tab)}\s*$")).first.click()
        self.page.wait_for_load_state("networkidle")
        return self

    def search(self, text):
        box = self.page.locator(L.SELLER_SEARCH_INPUT)
        if not box.count() or not box.first.is_visible():
            self.page.locator(L.SELLER_SEARCH_TOGGLE).first.click()
        box.first.fill(text)
        box.first.press("Enter")
        self.page.wait_for_load_state("networkidle")
        return self

    def open_star_sellers(self, search):
        return self.open_tab(Ssc.STAR_SELLERS_TAB).search(search)

    def has_row(self, sid):
        """After a search: True when the seller's row is listed, False on "No Results Found"."""
        row = self.page.locator(L.SELLER_ROWS).filter(has_text=re.compile(rf"{re.escape(sid)}(?!\d)"))
        expect(row.first.or_(self.page.get_by_text(Ssc.NO_RESULTS, exact=True))).to_be_visible(timeout=20_000)
        return row.count() > 0

    def row(self, sid):
        # The name and S-id render run together ("Google LLCS6742⭐️"), so no word boundary before the S.
        row = self.page.locator(L.SELLER_ROWS).filter(has_text=re.compile(rf"{re.escape(sid)}(?!\d)")).first
        expect(row).to_be_visible(timeout=20_000)
        return row

    def view_cue_card(self, sid, uid):
        """Click the row's Actions "View"; the cue card (/admin/notes/<uid>) opens in a new tab, returned."""
        link = self.row(sid).locator(L.ROW_VIEW).filter(has_text=Ssc.VIEW)
        expect(link).to_have_attribute("href", re.compile(rf"/notes/{re.escape(uid)}$"))
        with self.page.context.expect_page(timeout=30_000) as new_tab:
            link.click()
        tab = new_tab.value
        tab.wait_for_load_state("domcontentloaded")
        return tab
