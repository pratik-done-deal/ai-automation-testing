"""Hot-lead flows (hot-lead-engagement-visibility, S6-S8): a dedicated buyer lead acts, the scheduler
runs, the admin checks Investor Leads.

Spec: specs/features/hot-lead-engagement-visibility/test-cases.md, section 6. Destructive and slow:
  * every case needs its own never-hot buyer lead (DD_HLE_* in .env, keyed by case) and uses it up for
    14 days; used links and uids go to run_state/hle.json and are refused next time;
  * never auth/buyer.json: POC deep links open logged out, S6-01 uses DD_HLE_BUYER_STATE;
  * QA has no scheduler trigger, so the admin polls "Hot Leads" every 30 s for up to
    DD_HLE_HOT_POLL_SECONDS (one 5 min cycle + buffer). To pay that wait once, not per case, the buyer
    side of every selected case runs first (fixture `buyer_steps`), then the tests check in order.
    Negative cases wait out the full window before checking.

Pending: only the S8 cases. A short view that stays "not hot" is the new rule; the positive S6/S7
outcomes (interest or a 90 s view makes the lead hot) hold on today's logic too, so they run as
normal tests. Avoid running near midnight IST, the backend's "today" (answer 8).
"""
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime

import pytest
from playwright.sync_api import expect

from config import settings
from constants import HotLeadEngagementCopy as Hle
from pages.admin_module.admin_leads_page import AdminLeadsPage
from pages.admin_module.admin_unverified_deals_page import METRIC_RE, AdminUnverifiedDealsPage, metric_count, metric_text
from pages.buyer_module.buyer_cue_card_page import BuyerCueCardPage
from utils.flows import express_interest_on
from utils.hle_data import fresh_company_uid, lead_name, poc_links, require_hle_buyer_state, teaser_link
from utils.run_state import save_hle_use
from utils.sessions import new_anonymous_page, new_role_page

pytestmark = [pytest.mark.destructive, pytest.mark.slow]

# Test case -> the case whose buyer step it checks.
BUYER_STEP_OF = {"S6-01": "S6-01", "S6-02": "S6-01", "S7-01": "S7-01", "S7-02": "S7-02", "S7-03": "S7-03",
                 "S7-04": "S7-01", "S7-05": "S7-01", "S8-01": "S8-01", "S8-02": "S8-01", "S8-03": "S8-03"}
PASSED = set()   # cases later cases build on ("Given S7-01 passed")


@dataclass
class BuyerStep:
    case: str
    lead: str = ""
    done_at: float = 0.0        # time.monotonic() when the last POC left the page
    tracked: bool = True        # every time-tracking request was seen on leaving
    skip: str = ""
    error: str = ""


def _case_of(test_name):
    match = re.match(r"test_s(\d+)_(\d+)_", test_name)
    return f"S{match.group(1)}-{match.group(2)}" if match else None


def _used(case, lead):
    return {"case": case, "lead": lead, "at": datetime.now().isoformat(timespec="seconds")}


def _view(browser, step, link, seconds, deep_link=True):
    """One POC opens a link logged out, keeps it in front for `seconds`, then navigates away."""
    ctx, page = new_anonymous_page(browser)
    try:
        cue_card = BuyerCueCardPage(page)
        if deep_link:
            cue_card.open_deep_link(link)
        else:
            cue_card.open_link(link)
        save_hle_use(link, _used(step.case, step.lead))
        step.tracked &= cue_card.dwell(seconds).leave()
    finally:
        ctx.close()


def _express_interest(browser, step):
    """The S6-01 POC expresses interest within 30 s of opening a fresh company, then leaves."""
    require_hle_buyer_state(step.case)
    uid = fresh_company_uid(step.case)
    ctx, page = new_role_page(browser, "hle_buyer")
    try:
        cue_card = BuyerCueCardPage(page).open_cue_card(uid)
        save_hle_use(uid, _used(step.case, step.lead))
        assert cue_card.can_express_interest(), f"{uid}: the HLE buyer already expressed interest here"
        express_interest_on(cue_card, uid)
        step.tracked &= cue_card.leave()
    finally:
        ctx.close()


def _run_buyer_step(browser, case):
    step = BuyerStep(case)
    try:
        step.lead = lead_name(case)
        # Read every value first: a missing one skips the case before any lead is used.
        if case == "S6-01":
            _express_interest(browser, step)
        elif case == "S7-01":
            link, = poc_links(case)
            _view(browser, step, link, 90)
        elif case == "S7-02":
            _view(browser, step, teaser_link(case), 90, deep_link=False)
        elif case == "S7-03":
            poc_a, poc_b = poc_links(case, 2)
            _view(browser, step, poc_b, 20)
            _view(browser, step, poc_a, 90)
        elif case == "S8-01":
            link, = poc_links(case)
            _view(browser, step, link, 20)
        elif case == "S8-03":
            poc_a, poc_b = poc_links(case, 2)
            _view(browser, step, poc_a, 40)
            _view(browser, step, poc_b, 40)
        step.done_at = time.monotonic()
    except pytest.skip.Exception as exc:
        step.skip = str(exc.msg)
    except Exception as exc:  # reported by every test that needs this step
        step.error = f"{type(exc).__name__}: {exc}"
    sys.__stdout__.write(f"\n  HLE buyer step {case}: {step.skip or step.error or 'done'}"
                         f"{'' if step.tracked else ' (no time-tracking request seen on leaving)'}\n")
    return step


@pytest.fixture(scope="module")
def buyer_steps(request, browser, _admin_module_context):
    """Buyer side of every selected case, run before any admin check (needs the admin session first,
    so a missing auth/admin.json skips the file before any lead is used)."""
    wanted = []
    for item in request.session.items:
        case = BUYER_STEP_OF.get(_case_of(item.name)) if getattr(item, "module", None) is request.module else None
        if case and case not in wanted:
            wanted.append(case)
    return {case: _run_buyer_step(browser, case) for case in wanted}


def _step(buyer_steps, case):
    step = buyer_steps[BUYER_STEP_OF[case]]
    if step.skip:
        pytest.skip(step.skip)
    if step.error:
        pytest.fail(f"buyer step of {step.case} failed: {step.error}")
    return step


def _require_passed(case):
    if case not in PASSED:
        pytest.skip(f"needs {case} to have passed in this run")


def _wait_until_hot(leads, step):
    """Poll "Hot Leads" every 30 s until the lead is listed or the window after the buyer step ends."""
    deadline = step.done_at + settings.hle_hot_poll_seconds
    while not leads.is_listed_as_hot(step.lead):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        leads.page.wait_for_timeout(min(30.0, remaining) * 1000)
    return True


def _wait_full_window(leads, step):
    remaining = step.done_at + settings.hle_hot_poll_seconds - time.monotonic()
    if remaining > 0:
        leads.page.wait_for_timeout(remaining * 1000)


def _not_hot_message(step):
    return (f"{step.lead!r} is not under Hot Leads {settings.hle_hot_poll_seconds}s after the buyer step"
            + ("" if step.tracked else "; note: no time-tracking request was seen when the POC left"))


# ================================================================== S6: express interest makes the lead hot

def test_s6_01_express_interest_with_a_short_view_makes_the_lead_hot(buyer_steps, admin_module_page):
    """HLE-01, HLE-08, HLE-11 (S6-01): a fresh lead whose POC expressed interest within 30 s turns hot."""
    step = _step(buyer_steps, "S6-01")
    assert _wait_until_hot(AdminLeadsPage(admin_module_page), step), _not_hot_message(step)
    PASSED.add("S6-01")


def test_s6_02_lead_row_shows_the_hot_lead_icon(buyer_steps, admin_module_page):
    """HLE-01 (S6-02): with the toggles off, the S6-01 lead's icon tooltip reads "Hot Lead"."""
    step = _step(buyer_steps, "S6-02")
    _require_passed("S6-01")
    leads = AdminLeadsPage(admin_module_page).open_investor_leads(search=step.lead)
    row = leads.lead_row(step.lead).first
    expect(row).to_be_visible()
    assert leads.tooltip_of(leads.hot_icon(row).first) == Hle.HOT_LEAD_TOOLTIP


# ================================================================== S7: 1+ min of viewing makes the lead hot

def test_s7_01_90_seconds_on_the_cue_card_makes_the_lead_hot(buyer_steps, admin_module_page):
    """HLE-05 (S7-01): 90 s on the cue card (no Express Interest) makes a fresh lead hot."""
    step = _step(buyer_steps, "S7-01")
    assert _wait_until_hot(AdminLeadsPage(admin_module_page), step), _not_hot_message(step)
    PASSED.add("S7-01")


def test_s7_02_90_seconds_on_the_unlocked_teaser_makes_the_lead_hot(buyer_steps, admin_module_page):
    """HLE-06 (S7-02): 90 s on an unlocked investment teaser makes a fresh lead hot."""
    step = _step(buyer_steps, "S7-02")
    assert _wait_until_hot(AdminLeadsPage(admin_module_page), step), _not_hot_message(step)


def test_s7_03_one_poc_over_a_minute_is_enough(buyer_steps, admin_module_page):
    """HLE-10 (S7-03): POC B views 20 s, POC A 90 s: the lead turns hot on POC A alone."""
    step = _step(buyer_steps, "S7-03")
    assert _wait_until_hot(AdminLeadsPage(admin_module_page), step), _not_hot_message(step)


def test_s7_04_the_view_shows_on_the_unverified_deals_row(buyer_steps, admin_module_page):
    """HLE-16 (S7-04): the S7-01 lead's Unverified Deals row reads "<views ≥ 1> / <time>" in "CC Views / Time"."""
    step = _step(buyer_steps, "S7-04")
    _require_passed("S7-01")
    deals = AdminUnverifiedDealsPage(admin_module_page).open_unverified(search=step.lead)
    row = deals.rows_for_lead(step.lead).first
    expect(row).to_be_visible()
    text = metric_text(deals.cc_cell(row))
    assert METRIC_RE.match(text) and metric_count(text) >= 1, f"CC cell for {step.lead!r} reads {text!r}"
    PASSED.add("S7-04")


def test_s7_05_the_drill_down_lists_the_poc_who_viewed(buyer_steps, admin_module_page):
    """HLE-23 (S7-05): the S7-01 row's drill-down lists POC A with CC Views ≥ 1.

    The lead is fresh and only POC A viewed, so POC A is the one POC row with cue-card views.
    """
    step = _step(buyer_steps, "S7-05")
    _require_passed("S7-04")
    deals = AdminUnverifiedDealsPage(admin_module_page).open_unverified(search=step.lead)
    rows = deals.open_drill_down(deals.cc_cell(deals.rows_for_lead(step.lead).first)).values_by_header()
    viewed = [row for row in rows if (row.get(Hle.CC_VIEWS) or "").isdigit() and int(row[Hle.CC_VIEWS]) >= 1]
    assert len(viewed) == 1, f"expected POC A as the only POC with CC Views >= 1: {rows}"


# ================================================================== S8: short views keep the lead not hot

@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s8_01_20_seconds_on_the_cue_card_does_not_make_the_lead_hot(buyer_steps, admin_module_page):
    """HLE-04 (S8-01): after a 20 s view and a full scheduler window, the lead is not under Hot Leads."""
    step = _step(buyer_steps, "S8-01")
    leads = AdminLeadsPage(admin_module_page)
    _wait_full_window(leads, step)
    assert not leads.is_listed_as_hot(step.lead), f"{step.lead!r} turned hot on a 20 s view"
    PASSED.add("S8-01")


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s8_02_shallow_view_lead_has_no_hot_lead_icon(buyer_steps, admin_module_page):
    """HLE-04 (S8-02): with the toggles off, the S8-01 lead's row has no flame icon."""
    step = _step(buyer_steps, "S8-02")
    _require_passed("S8-01")
    leads = AdminLeadsPage(admin_module_page).open_investor_leads(search=step.lead)
    row = leads.lead_row(step.lead).first
    expect(row).to_be_visible()
    expect(leads.hot_icon(row)).to_have_count(0)


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s8_03_two_pocs_at_40_seconds_do_not_add_up_to_hot(buyer_steps, admin_module_page):
    """HLE-10 (S8-03): POC A and POC B view 40 s each (80 s combined): the lead is not under Hot Leads."""
    step = _step(buyer_steps, "S8-03")
    leads = AdminLeadsPage(admin_module_page)
    _wait_full_window(leads, step)
    assert not leads.is_listed_as_hot(step.lead), f"{step.lead!r} turned hot on 2 x 40 s views"
