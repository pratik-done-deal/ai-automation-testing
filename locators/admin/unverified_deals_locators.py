"""Selectors for Admin Deals > Unverified Deals (/admin/deals, tab "Unverified Deals").

Confirmed in the JSX (hot-lead-engagement-visibility):
  * tabs are `div.tab-item` with an onClick, not role=tab (CommonComponent/BuyerCommon/CustomTabs);
  * the listing is an MUI <table> in `.custom-table-grid-container` (Component/CustomTableGrid), inside
    `.buyer-deals-container` (HOC/DataTabsWithFilter). The drill-down modal renders the same grid in a
    portal, so the page table is always scoped to `.buyer-deals-container`;
  * an engagement cell with a drill-down holds `<span role="button">` with the metric as its text
    (DealsLink/index.jsx); a cell without one is plain text ("-", "0 / 0 sec"). Figma adds an
    "N members" pill under the metric (not built yet).
"""
import re

TAB = "div.tab-item"
TABLE = ".buyer-deals-container .custom-table-grid-container table"
HEADER_CELLS = f"{TABLE} thead th"
ROWS = f"{TABLE} tbody tr:has(td)"
CELLS = "td"

DRILL_DOWN_LINK = "[role='button']"
MEMBERS_PILL = re.compile(r"\d+\s+members?", re.I)   # hot-lead-engagement-visibility: Figma 43508:119587
