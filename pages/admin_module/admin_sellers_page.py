import re
from urllib.parse import quote

from playwright.sync_api import expect

from constants import ADMIN_SELLERS_PATH, StarSellerCopy as Ssc
from locators.admin import star_seller_locators as L
from pages.shared.base_page import BasePage


class AdminSellersPage(BasePage):
    """Admin Sellers list: /admin/seller (WrappedWithFilters). Star sellers show "⭐️" after the S-id
    (SellerDataModel.js:84)."""

    def open_star_sellers(self, search):
        self.open(ADMIN_SELLERS_PATH)
        self.page.locator(L.TAB).filter(has_text=re.compile(rf"^\s*{Ssc.STAR_SELLERS_TAB}\s*$")).first.click()
        self.page.wait_for_load_state("networkidle")
        # The listing reads searchString from the URL, as Admin Leads does; it searches seller names.
        url = self.page.url
        self.page.goto(url + ("&" if "?" in url else "?") + f"searchString={quote(search)}")
        self.page.wait_for_load_state("networkidle")
        return self

    def row(self, sid):
        row = self.page.locator(L.SELLER_ROWS).filter(has_text=re.compile(rf"\b{re.escape(sid)}\b")).first
        expect(row).to_be_visible(timeout=20_000)
        return row
