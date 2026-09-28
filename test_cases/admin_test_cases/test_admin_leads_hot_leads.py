"""Investor Leads / Company Leads hot-lead toggles (hot-lead-engagement-visibility, S5 and S9-01).

Spec: specs/features/hot-lead-engagement-visibility/test-cases.md. The feature changes only which
leads the backend marks hot, never the toggles, so everything here already works on QA and runs as
a normal test. Read-only: one admin context for the file, existing QA data, nothing changed.
"""
import re

import pytest
from playwright.sync_api import expect

from constants import HotLeadEngagementCopy as Hle
from pages.admin_module.admin_leads_page import AdminLeadsPage


@pytest.fixture
def leads(admin_module_page):
    return AdminLeadsPage(admin_module_page).open_investor_leads()


def _rows_or_skip(leads, need):
    rows = leads.row_list()
    if not rows:
        pytest.skip(f"needs {need} on QA")
    return rows


# ================================================================== S5: Investor Leads toggles

@pytest.mark.smoke
def test_s5_01_hot_leads_toggle_shows_only_hot_leads(leads):
    """HLE-15 (S5-01): with "Hot Leads" on, every Investor Leads row shows the flame icon."""
    rows = _rows_or_skip(leads.turn_on_hot(), "at least one hot buyer lead")
    missing = [i for i, row in enumerate(rows, start=1) if not leads.hot_icon(row).count()]
    assert not missing, f"rows without the flame icon: {missing}"


def test_s5_02_turning_on_hot_leads_reveals_expired_hot_leads(leads):
    """HLE-15 (S5-02): the "Expired Hot Leads" switch appears only once "Hot Leads" is on."""
    expect(leads.expired_switch).to_have_count(0)
    leads.turn_on_hot()
    expect(leads.expired_switch).to_be_visible()


def test_s5_03_the_two_toggles_are_mutually_exclusive(leads):
    """HLE-15 (S5-03): turning on "Expired Hot Leads" switches "Hot Leads" off."""
    leads.turn_on_hot().turn_on_expired()
    expect(leads.expired_switch.locator("input")).to_be_checked()
    expect(leads.hot_switch.locator("input")).not_to_be_checked()


def test_s5_04_expired_hot_leads_shows_only_expired_leads(leads):
    """HLE-15 (S5-04): with "Expired Hot Leads" on, every row's icon tooltip reads "Expired Hot Lead"."""
    rows = _rows_or_skip(leads.turn_on_hot().turn_on_expired(), "at least one expired-hot buyer lead")
    tooltips = [leads.tooltip_of(leads.expired_icon(row).first) if leads.expired_icon(row).count() else None
                for row in rows]
    wrong = [(i, text) for i, text in enumerate(tooltips, start=1) if text != Hle.EXPIRED_HOT_LEAD_TOOLTIP]
    assert not wrong, f"rows whose icon tooltip isn't {Hle.EXPIRED_HOT_LEAD_TOOLTIP!r} (row, tooltip): {wrong}"


def test_s5_05_changing_tab_resets_both_toggles(leads):
    """HLE-15 (S5-05): after Company Leads and back, "Hot Leads" is off and "Expired Hot Leads" hidden."""
    leads.turn_on_hot()
    leads.open_tab(Hle.COMPANY_LEADS_TAB).open_tab(Hle.INVESTOR_LEADS_TAB)
    expect(leads.hot_switch.locator("input")).not_to_be_checked()
    expect(leads.expired_switch).to_have_count(0)


def test_s5_06_flame_icon_tooltip_reads_hot_lead(leads):
    """HLE-15 (S5-06): hovering the first hot row's flame icon shows "Hot Lead"."""
    rows = _rows_or_skip(leads.turn_on_hot(), "at least one hot buyer lead")
    assert leads.tooltip_of(leads.hot_icon(rows[0]).first) == Hle.HOT_LEAD_TOOLTIP


def test_s5_07_expiring_this_week_pill_copy(leads):
    """HLE-15 (S5-07): the pill next to "Hot Leads" reads "<n> Expiring this week" with n ≥ 1."""
    if not leads.expiring_pill.count():
        pytest.skip("needs a hot buyer lead expiring within 7 days (the pill is hidden at 0)")
    text = " ".join(leads.expiring_pill.first.inner_text().split())
    match = re.fullmatch(rf"(\d+) {Hle.EXPIRING_THIS_WEEK}", text)
    assert match and int(match.group(1)) >= 1, text


# ================================================================== S9: seller leads unchanged

def test_s9_01_company_leads_hot_toggle_still_lists_hot_seller_leads(leads):
    """HLE-09 (S9-01): Company Leads with "Hot Leads" on lists at least one row, each with the flame icon."""
    leads.open_tab(Hle.COMPANY_LEADS_TAB).turn_on_hot()
    rows = leads.row_list()
    assert rows, "Company Leads lists no hot seller lead"
    missing = [i for i, row in enumerate(rows, start=1) if not leads.hot_icon(row).count()]
    assert not missing, f"rows without the flame icon: {missing}"
