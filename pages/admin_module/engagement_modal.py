import re

from playwright.sync_api import expect

from constants import HotLeadEngagementCopy as Hle
from locators.admin import engagement_modal_locators as L
from pages.shared.base_page import BasePage

TITLE_WITH_BUYER_ID = re.compile(r"^Engagement for B\d+$")   # hot-lead-engagement-visibility: Figma 43651:131869


class EngagementModal(BasePage):
    """Per-POC engagement drill-down opened from an Unverified Deals engagement cell (DealsLink)."""

    @property
    def root(self):
        return self.page.locator(L.MODAL).last

    def wait_open(self):
        expect(self.root).to_be_visible(timeout=15_000)
        return self

    @property
    def title(self):
        return self.root.get_by_text(L.TITLE).first

    def title_text(self):
        expect(self.title).to_be_visible()
        return self.title.inner_text().strip()

    def header_texts(self):
        return [" ".join(t.split()) for t in self.root.locator(L.HEADER_CELLS).all_inner_texts()]

    @property
    def rows(self):
        return self.root.locator(L.ROWS)

    def row_values(self):
        """[[cell text, ...] per POC row], read once the first row is visible."""
        expect(self.rows.first).to_be_visible()
        return [[" ".join(t.split()) for t in self.rows.nth(i).locator(L.CELLS).all_inner_texts()]
                for i in range(self.rows.count())]

    def values_by_header(self):
        headers = self.header_texts()
        return [dict(zip(headers, values)) for values in self.row_values()]

    def rows_with_primary_chip(self):
        chip = self.page.locator(L.PRIMARY_CHIP).filter(has_text=Hle.PRIMARY_CHIP).or_(
            self.page.get_by_text(Hle.PRIMARY_CHIP, exact=True))
        return self.rows.filter(has=chip)

    @property
    def error_message(self):
        return self.root.get_by_text(Hle.LOAD_ERROR)

    @property
    def close_button(self):
        return self.root.get_by_role("button", name=Hle.CLOSE, exact=True)

    def close(self):
        self.close_button.click()
        expect(self.page.locator(L.MODAL)).to_have_count(0)

    def expect_closed(self):
        expect(self.page.locator(L.MODAL)).to_have_count(0)
