import re

import pytest
from playwright.sync_api import expect

from constants import Copy, share_toggle_label
from pages.seller_module.accept_interest_modal import DOCUMENT_QUERY_API, AcceptInterestModal
from pages.shared.base_page import BasePage

DEALS_QUERY_API = "deal/query"


class SellerDealsPage(BasePage):
    """Seller My Deals: /deals/:companyId? (SellerDealsAndInvestors, SHOW_SELLER_DASHBOARD_REVAMP)."""

    def open_deals(self, company_id: str = "", tab: str = Copy.INTEREST_RECEIVED_TAB, deal_id=None):
        """Open the deals page on `tab`; `self.deals` holds that tab's deal/query rows in display order.

        With `deal_id` the tables are filtered to that deal (`?dealId=`, SellerDealsTab.js:16,30).
        """
        responses = []
        self.page.on("response", lambda r: DEALS_QUERY_API in r.url and responses.append(r))
        # companyId is optional in the route; without it the seller lands on their own company.
        path = f"deals/{company_id}" if company_id else "deals"
        self.open(f"{path}?dealId={deal_id}" if deal_id else path)
        # Clicking the tab that is already selected sends nothing (SellerDealsTable.handleTabClick).
        self.page.get_by_role("button", name=tab, exact=True).first.click()  # DealsTabs.js
        self.page.wait_for_load_state("networkidle")
        self.deals = []
        if responses:
            body = responses[-1].json()
            self.deals = ((body.get("data") or {}).get("elements")) or []
        return self

    # --- Interest Received ---

    def _accept_cta(self, scope):
        # Accept / Reject in the table are <div onClick>, not buttons (SellerDealsAction.js:34-35).
        return scope.locator("div.cursor-pointer").filter(has_text=re.compile(r"^\s*Accept\s*$"))

    def rows(self):
        return self.page.locator("table tbody tr").filter(has=self._accept_cta(self.page))

    def row_for_deal(self, deal_id):
        """The Interest Received row for `deal_id`, matched by its position in the deal/query rows."""
        ids = [d.get("id") for d in self.deals]
        if int(deal_id) not in ids:
            pytest.skip(f"Deal {deal_id} is not in this seller's Interest Received (already accepted, or "
                        "the saved seller session belongs to another company)")
        row = self.rows().nth(ids.index(int(deal_id)))
        expect(row).to_be_visible(timeout=20_000)
        return row

    def _open_accept(self, row) -> AcceptInterestModal:
        with self.page.expect_response(lambda r: DOCUMENT_QUERY_API in r.url, timeout=30_000) as docs:
            self._accept_cta(row).first.click()
        modal = AcceptInterestModal(self.page)
        modal.documents_payload = docs.value.json()
        modal.wait_until_open()
        self.page.wait_for_load_state("networkidle")  # seller slots load in parallel
        return modal

    def open_accept_for_deal(self, deal_id) -> AcceptInterestModal:
        return self._open_accept(self.row_for_deal(deal_id))

    def first_row_accept(self) -> AcceptInterestModal:
        if self.rows().count() == 0:
            pytest.skip("Seller has no rows in Interest Received to open")
        return self._open_accept(self.rows().first)

    def deal_ids_listed(self):
        return [d.get("id") for d in self.deals]

    # --- Active Deals: manage shared documents (ManageDocsCell / ManageSharedDocsModal) ---

    def active_row_for_deal(self, deal_id):
        row = self.page.locator("table tbody tr").filter(has_text=re.compile(rf"\bD{deal_id}\b")).first
        expect(row).to_be_visible(timeout=20_000)
        return row

    def open_manage_docs(self, deal_id):
        button = self.active_row_for_deal(deal_id).get_by_role(
            "button", name=re.compile(r"(Share documents|\d+ of \d+ documents? shared)"))
        button.click()
        expect(self.page.get_by_role("button", name=re.compile(rf"^({Copy.SAVE_EDITS}|Saving…)$"))).to_be_visible()

    def share_toggle(self, file_name):
        return self.page.get_by_role("switch", name=share_toggle_label(file_name))

    def save_share_edits(self):
        """Click Save edits; returns the document/deal/share request body."""
        with self.page.expect_request(lambda r: "document/deal/share" in r.url, timeout=30_000) as req:
            self.page.get_by_role("button", name=Copy.SAVE_EDITS).click()
        return req.value.post_data_json
