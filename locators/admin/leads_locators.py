"""Selectors for Admin Leads (/admin/leads): tabs, the Hot Leads / Expired Hot Leads switches, lead rows.

Confirmed in the JSX (src/Container/LeadContainer/index.js, leadTableModel.js):
  * each switch is an MUI FormControlLabel (<label>) whose label holds a <span> with the text; the
    "Expired Hot Leads" label also contains the words "Hot Leads", so labels are matched on the exact
    span text;
  * the "<n> Expiring this week" pill is a `div.rounded-2xl` inside the Hot Leads label;
  * the row icons are sprite <svg><use href="...sprite.svg#hotBuyerIcon"></svg> (CustomIcon) wrapped
    in an MUI Tooltip titled "Hot Lead" / "Expired Hot Lead". The toggles' own flame is an inline
    path, never a sprite <use>.
"""
TAB = "div.tab-item"
SWITCH_LABEL = "label.MuiFormControlLabel-root"
SWITCH_INPUT = "input[type='checkbox']"
SWITCH_CONTROL = ".MuiSwitch-root"
EXPIRING_PILL = "div.rounded-2xl"

TABLE = ".custom-table-grid-container table"
ROWS = f"{TABLE} tbody tr:has(td)"
HOT_ICON = "svg:has(use[href$='#hotBuyerIcon'])"
EXPIRED_HOT_ICON = "svg:has(use[href$='#expiredHotBuyerIcon'])"
TOOLTIP = "[role='tooltip']"
