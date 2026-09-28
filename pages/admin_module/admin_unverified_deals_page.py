import re
from urllib.parse import quote

from playwright.sync_api import expect

from constants import UNVERIFIED_DEALS_PATH, HotLeadEngagementCopy as Hle
from locators.admin import unverified_deals_locators as L
from pages.admin_module.engagement_modal import EngagementModal
from pages.shared.base_page import BasePage

# "<views> / <time>". The app formats seconds as "N min", "N min N sec" or "N sec" (seconds may
# carry decimals, formatDurationFromSeconds); Figma writes "22min". Values are never recalculated.
TIME = r"\d+\s?min(?:\s\d+(?:\.\d+)?\s?sec)?|\d+(?:\.\d+)?\s?sec"
TIME_RE = re.compile(rf"^(?:{TIME})$")
METRIC_RE = re.compile(rf"^(\d+)\s*/\s*(?:{TIME})$")
NOT_YET_VIEWED_RE = re.compile(re.escape(Hle.NOT_YET_VIEWED), re.I)


def squash(text):
    return " ".join((text or "").split())


def metric_text(cell):
    """The metric line of an engagement cell, without Figma's "N members" pill line under it."""
    lines = [line.strip() for line in cell.inner_text().splitlines() if line.strip()]
    return lines[0] if lines else ""


def metric_count(text):
    """Views in "<views> / <time>", or None when the cell shows no count."""
    match = re.match(r"^\s*(\d+)\s*/", text or "")
    return int(match.group(1)) if match else None


def is_empty_metric(text):
    """No engagement: today's "-", the new "not yet viewed", or a zero count ("0 / 0 sec")."""
    return text in ("", Hle.EMPTY_METRIC) or bool(NOT_YET_VIEWED_RE.search(text)) or metric_count(text) == 0


class AdminUnverifiedDealsPage(BasePage):
    """Admin Deals > Unverified Deals: /admin/deals?tabIndex=2&key=Unverified%20Deals (AdminUnverifiedLeadTableModel)."""

    LIST_API = re.compile(r"deal/unverified-deals")

    def open_unverified(self, search=""):
        """Open the tab (optionally searched) and wait for its deal/unverified-deals page 1."""
        path = UNVERIFIED_DEALS_PATH + (f"&searchString={quote(search)}" if search else "")
        with self.page.expect_response(lambda r: self.LIST_API.search(r.url), timeout=30_000):
            self.open(path)
        expect(self.page.locator(L.HEADER_CELLS).first).to_be_visible(timeout=15_000)
        return self

    @property
    def table(self):
        return self.page.locator(L.TABLE)

    def header_texts(self):
        return [squash(text) for text in self.page.locator(L.HEADER_CELLS).all_inner_texts()]

    def column(self, header):
        headers = self.header_texts()
        assert header in headers, f"no {header!r} column; headers are {headers}"
        return headers.index(header)

    @property
    def rows(self):
        return self.page.locator(L.ROWS)

    def row_list(self):
        return [self.rows.nth(i) for i in range(self.rows.count())]

    def cell(self, row, header):
        return row.locator(L.CELLS).nth(self.column(header))

    def cc_cell(self, row):
        return self.cell(row, Hle.CC_HEADER)

    def doc_cell(self, row):
        return self.cell(row, Hle.DOC_HEADER)

    def first_row(self, predicate):
        """The first row on this page for which predicate(row) is true, or None."""
        return next((row for row in self.row_list() if predicate(row)), None)

    def rows_for_lead(self, lead_name):
        return self.rows.filter(has_text=lead_name)

    @staticmethod
    def drill_down_entry(cell):
        """Today the metric itself (<span role=button>); Figma's "N members" pill once it ships."""
        return cell.locator(L.DRILL_DOWN_LINK).or_(cell.get_by_text(L.MEMBERS_PILL)).first

    def has_drill_down(self, cell):
        return cell.locator(L.DRILL_DOWN_LINK).count() > 0 or cell.get_by_text(L.MEMBERS_PILL).count() > 0

    def open_drill_down(self, cell) -> EngagementModal:
        self.drill_down_entry(cell).click()
        return EngagementModal(self.page).wait_open()
