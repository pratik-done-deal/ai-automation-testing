import re
from urllib.parse import quote

from playwright.sync_api import expect

from constants import INVESTOR_LEADS_PATH, HotLeadEngagementCopy as Hle
from locators.admin import leads_locators as L
from pages.shared.base_page import BasePage


def _posted(response, pattern):
    return bool(re.search(pattern, response.request.post_data or ""))


# The switches add {filterKey:"hotLead", operation:"notExpired"|"expired"} to POST lead/query
# (HOC/WrappedWithFilters/index.js:224-237). "expired" is matched whole, as it is inside "notExpired".
HOT_QUERY = r'"operation"\s*:\s*"notExpired"'
EXPIRED_QUERY = r'"operation"\s*:\s*"expired"'


class AdminLeadsPage(BasePage):
    """Admin Leads: /admin/leads (LeadContainer on WrappedWithFilters). Investor Leads is tabIndex=1."""

    LIST_API = re.compile(r"lead/query")

    def _list_response(self, pattern=None):
        return self.page.expect_response(
            lambda r: self.LIST_API.search(r.url) and (pattern is None or _posted(r, pattern)), timeout=30_000)

    def open_investor_leads(self, search=""):
        """Investor Leads with both switches off, optionally narrowed by the listing's search string."""
        path = INVESTOR_LEADS_PATH + (f"&searchString={quote(search)}" if search else "")
        with self._list_response() as res:
            self.open(path)
        self.last_list_url = res.value.url
        expect(self.hot_switch).to_be_visible(timeout=15_000)
        return self

    def open_tab(self, label):
        with self._list_response() as res:
            self.page.locator(L.TAB).filter(has_text=re.compile(rf"^\s*{re.escape(label)}\s*$")).click()
        self.last_list_url = res.value.url
        self.page.wait_for_load_state("networkidle")
        return self

    # --- switches ---

    def switch(self, label):
        return self.page.locator(L.SWITCH_LABEL).filter(has=self.page.get_by_text(label, exact=True))

    @property
    def hot_switch(self):
        return self.switch(Hle.HOT_LEADS)

    @property
    def expired_switch(self):
        return self.switch(Hle.EXPIRED_HOT_LEADS)

    @staticmethod
    def is_on(switch):
        return switch.locator(L.SWITCH_INPUT).is_checked()

    def _flip(self, switch, pattern):
        with self._list_response(pattern) as res:
            switch.locator(L.SWITCH_CONTROL).click()
        self.last_list_url = res.value.url
        self.page.wait_for_load_state("networkidle")
        return self

    def turn_on_hot(self):
        return self._flip(self.hot_switch, HOT_QUERY)

    def turn_on_expired(self):
        return self._flip(self.expired_switch, EXPIRED_QUERY)

    @property
    def expiring_pill(self):
        return self.hot_switch.locator(L.EXPIRING_PILL).filter(has_text=Hle.EXPIRING_THIS_WEEK)

    # --- rows ---

    @property
    def rows(self):
        return self.page.locator(L.ROWS)

    def row_list(self):
        return [self.rows.nth(i) for i in range(self.rows.count())]

    def lead_row(self, name):
        return self.rows.filter(has_text=name)

    @staticmethod
    def hot_icon(row):
        return row.locator(L.HOT_ICON)

    @staticmethod
    def expired_icon(row):
        return row.locator(L.EXPIRED_HOT_ICON)

    def tooltip_of(self, icon):
        """Hover a row icon and return its MUI tooltip text."""
        self.page.mouse.move(0, 0)   # drop the previous row's tooltip first
        icon.hover()
        tooltip = self.page.locator(L.TOOLTIP).last
        expect(tooltip).to_be_visible(timeout=5_000)
        return tooltip.inner_text().strip()

    def is_listed_as_hot(self, name):
        """Investor Leads searched for `name`, Hot Leads on: is the lead listed?

        The search must reach the hot-lead request, or a lead missing from page 1 would read as "not hot".
        """
        self.open_investor_leads(search=name).turn_on_hot()
        if "searchString=" not in self.last_list_url:
            # Not an AssertionError: a pending "stays not hot" test must not read this as an expected failure.
            raise RuntimeError(f"the Hot Leads request dropped the search ({self.last_list_url}); "
                               f"can't isolate {name!r}")
        return self.lead_row(name).count() > 0
