import re

from playwright.sync_api import expect

from constants import Copy
from pages.accept_interest_modal import AcceptInterestModal
from pages.base_page import BasePage


class SellerDealsPage(BasePage):
    """Seller My Deals: /deals/:companyId?  (Interest Received tab)."""

    def open_deals(self, company_id: str = ""):
        # companyId is optional in the route; without it the seller lands on their own company.
        self.open(f"deals/{company_id}" if company_id else "deals")
        self.page.get_by_text(Copy.INTEREST_RECEIVED_TAB, exact=True).first.click()
        return self

    def rows(self):
        return self.page.locator("table tbody tr, [role='row']").filter(
            has=self.page.get_by_role("button", name=Copy.ACCEPT, exact=True)
        )

    def row_for(self, buyer_text: str = ""):
        # Without a buyer name, the newest interest (first row) is the one the run just created.
        row = (self.rows().filter(has_text=buyer_text) if buyer_text else self.rows()).first
        expect(row).to_be_visible(timeout=20_000)
        return row

    def open_accept(self, buyer_text: str = "") -> AcceptInterestModal:
        self.row_for(buyer_text).get_by_role("button", name=Copy.ACCEPT, exact=True).click()
        modal = AcceptInterestModal(self.page)
        modal.wait_until_open()
        return modal

    def first_row_accept(self) -> AcceptInterestModal:
        self.rows().first.get_by_role("button", name=Copy.ACCEPT, exact=True).click()
        modal = AcceptInterestModal(self.page)
        modal.wait_until_open()
        return modal

    def row_count_matching(self, text) -> int:
        return self.rows().filter(has_text=re.compile(re.escape(text))).count()
