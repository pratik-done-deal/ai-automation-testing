"""Unverified Deals engagement columns and drill-down (hot-lead-engagement-visibility, S1-S4).

Spec: specs/features/hot-lead-engagement-visibility/test-cases.md. Figma 43508:119587 (table),
43651:131869 (drill-down). One admin context for the file; every test opens the tab itself and reads
existing QA data (rows are found by cell content, never by deal id). Only S2-05 changes data: it
opens one dedicated POC link.

What already works on QA runs as a normal test: the CC / Doc headers, the metric cells, the
drill-down opening, its rows and Close. What the Figma / PRD end state changes is marked
pending_feature: "not yet viewed" (today "-"), the Figma header set ("Deal Status", "Actions"),
"POC Name" (today "POC Email"), "Engagement for B<id>" (today D<dealId>), the Primary chip and the
drill-down error state.
"""
import re
import time
from datetime import datetime

import pytest
from playwright.sync_api import expect

from constants import HotLeadEngagementCopy as Hle
from pages.admin_module.admin_unverified_deals_page import (
    METRIC_RE, NOT_YET_VIEWED_RE, TIME_RE, AdminUnverifiedDealsPage, is_empty_metric, metric_count, metric_text,
)
from pages.admin_module.engagement_modal import TITLE_WITH_BUYER_ID, EngagementModal
from pages.buyer_module.buyer_cue_card_page import BuyerCueCardPage
from utils.hle_data import lead_name, poc_links
from utils.network import failure_body, mock_json
from utils.run_state import save_hle_use
from utils.sessions import new_anonymous_page, track_listener



@pytest.fixture
def deals(admin_module_page):
    return AdminUnverifiedDealsPage(admin_module_page).open_unverified()


def _count(cell):
    return metric_count(metric_text(cell)) or 0


def _row_with_views(deals, cell_of, need):
    row = deals.first_row(lambda r: _count(cell_of(r)) >= 1)
    if row is None:
        pytest.skip(f"needs {need} on Unverified Deals page 1")
    return row


def _row_without_cc_views(deals):
    row = deals.first_row(lambda r: is_empty_metric(metric_text(deals.cc_cell(r))))
    if row is None:
        pytest.skip("needs an Unverified Deals row with no cue-card views on page 1")
    return row


def _first_drill_down_cell(deals):
    row = deals.first_row(lambda r: deals.has_drill_down(deals.cc_cell(r)))
    if row is None:
        pytest.skip('needs an Unverified Deals row with a drill-down entry in "CC Views / Time" on page 1')
    return deals.cc_cell(row)


# ================================================================== S1: engagement columns

@pytest.mark.smoke
def test_s1_01_engagement_column_headers_are_shown(deals):
    """HLE-19, HLE-16, HLE-17 (S1-01): the header row has "CC Views / Time" and "Doc Views / Time"."""
    headers = deals.header_texts()
    assert Hle.CC_HEADER in headers, headers
    assert Hle.DOC_HEADER in headers, headers


@pytest.mark.smoke
def test_s1_02_row_with_cue_card_views_shows_count_and_time(deals):
    """HLE-16 (S1-02): a row with cue-card views reads "<views ≥ 1> / <time>" in minute/second format."""
    row = _row_with_views(deals, deals.cc_cell, "a row with cue-card views")
    text = metric_text(deals.cc_cell(row))
    assert METRIC_RE.match(text), f"CC cell {text!r} is not '<views> / <time>'"
    assert metric_count(text) >= 1, text


def test_s1_03_row_with_teaser_views_shows_doc_count_and_time(deals):
    """HLE-17 (S1-03): a row with teaser views reads "<views ≥ 1> / <time>" in "Doc Views / Time"."""
    row = _row_with_views(deals, deals.doc_cell, "a row with doc (teaser) views")
    text = metric_text(deals.doc_cell(row))
    assert METRIC_RE.match(text), f"Doc cell {text!r} is not '<views> / <time>'"
    assert metric_count(text) >= 1, text


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s1_04_full_header_set_matches_figma(deals):
    """HLE-19 (S1-04): the headers read, in order, as in Figma ("Deal Status", "Actions"; today "Status", "Action")."""
    assert deals.header_texts() == Hle.FIGMA_UNVERIFIED_HEADERS


# ================================================================== S2: no engagement yet

@pytest.mark.smoke
@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s2_01_empty_cc_cell_shows_not_yet_viewed(deals):
    """HLE-20 (S2-01): a row with no cue-card views shows "not yet viewed" in "CC Views / Time" (today "-")."""
    text = metric_text(deals.cc_cell(_row_without_cc_views(deals)))
    assert NOT_YET_VIEWED_RE.search(text), f"empty CC cell reads {text!r}"


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s2_02_empty_doc_cell_shows_its_own_not_yet_viewed(deals):
    """HLE-20 (S2-02): with cue-card views but no doc views, the Doc cell alone shows "not yet viewed"."""
    row = deals.first_row(lambda r: _count(deals.cc_cell(r)) >= 1
                          and is_empty_metric(metric_text(deals.doc_cell(r))))
    if row is None:
        pytest.skip("needs a row with cue-card views and no doc views on Unverified Deals page 1")
    assert METRIC_RE.match(metric_text(deals.cc_cell(row)))
    doc = metric_text(deals.doc_cell(row))
    assert NOT_YET_VIEWED_RE.search(doc), f"empty Doc cell reads {doc!r}"


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s2_03_no_engagement_cell_shows_a_dash(deals):
    """HLE-20, HLE-14 (S2-03): no "CC" or "Doc" cell on page 1 is "-", blank or a bare "0"."""
    rows = deals.row_list()
    if not rows:
        pytest.skip("Unverified Deals page 1 is empty")
    bad = []
    for number, row in enumerate(rows, start=1):
        for header, cell in ((Hle.CC_HEADER, deals.cc_cell(row)), (Hle.DOC_HEADER, deals.doc_cell(row))):
            text = metric_text(cell)
            if text in ("", Hle.EMPTY_METRIC, "0"):
                bad.append((number, header, text))
    assert not bad, f"cells without the 'not yet viewed' state (row, column, text): {bad}"


def test_s2_04_empty_cell_has_no_drill_down_entry(deals):
    """HLE-22 (S2-04): an empty engagement cell ("-" today, "not yet viewed" later) has no link or pill and opens nothing."""
    cell = deals.cc_cell(_row_without_cc_views(deals))
    assert not deals.has_drill_down(cell), f"empty cell {metric_text(cell)!r} has a drill-down entry"
    cell.click()
    deals.page.wait_for_timeout(500)
    EngagementModal(deals.page).expect_closed()


@pytest.mark.destructive
def test_s2_05_view_with_no_time_data_still_renders(browser, admin_module_page):
    """HLE-14 (S2-05): a POC view whose time was never sent still renders as a count and a time on its row."""
    name = lead_name("S2-05")
    link, = poc_links("S2-05")

    # The POC opens the card and the context is killed before leaving, so no time is sent.
    ctx, page = new_anonymous_page(browser)
    try:
        ctx.route(BuyerCueCardPage.TRACKING_API, lambda route: route.abort())
        BuyerCueCardPage(page).open_deep_link(link)
        save_hle_use(link, {"case": "S2-05", "lead": name, "at": datetime.now().isoformat(timespec="seconds")})
    finally:
        ctx.close()

    deals = AdminUnverifiedDealsPage(admin_module_page)
    deadline = time.monotonic() + 120
    while True:
        rows = deals.open_unverified(search=name).rows_for_lead(name)
        if rows.count() or time.monotonic() > deadline:
            break
        admin_module_page.wait_for_timeout(15_000)
    expect(rows.first).to_be_visible()
    text = metric_text(deals.cc_cell(rows.first))
    assert not re.search(r"NaN|undefined|null", text), text
    assert METRIC_RE.match(text), f"CC cell {text!r} is not '<views> / <time>'"


# ================================================================== S3: drill-down

@pytest.mark.smoke
def test_s3_01_drill_down_entry_opens_the_modal(deals):
    """HLE-21 (S3-01): the first row's drill-down entry in "CC Views / Time" opens the engagement modal."""
    modal = deals.open_drill_down(_first_drill_down_cell(deals))
    assert modal.title_text().startswith(Hle.ENGAGEMENT_TITLE_PREFIX)


@pytest.mark.smoke
def test_s3_02_modal_lists_at_least_one_poc_row(deals):
    """HLE-23 (S3-02): the modal has at least one POC row with a value in each of its five columns."""
    rows = deals.open_drill_down(_first_drill_down_cell(deals)).row_values()
    assert any(len(values) == 5 and all(values) for values in rows), f"POC rows: {rows}"


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s3_03_modal_headers_match_figma(deals):
    """HLE-23 (S3-03): the modal headers read "POC Name", "CC Views", "CC Avg Time Spent", "Doc Views", "Doc Avg Time Spent"."""
    modal = deals.open_drill_down(_first_drill_down_cell(deals))
    assert modal.header_texts() == Hle.FIGMA_MODAL_HEADERS


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s3_04_modal_title_names_the_buyer_lead(deals):
    """HLE-25 (S3-04): the modal title reads "Engagement for B<digits>" (today "Engagement for D<dealId>")."""
    title = deals.open_drill_down(_first_drill_down_cell(deals)).title_text()
    assert TITLE_WITH_BUYER_ID.match(title), title


@pytest.mark.smoke
def test_s3_05_close_button_closes_the_modal(deals):
    """HLE-26 (S3-05): "Close" dismisses the modal and the Unverified Deals table is visible again."""
    deals.open_drill_down(_first_drill_down_cell(deals)).close()
    expect(deals.table).to_be_visible()


def test_s3_06_modal_time_values_are_present_and_formatted(deals):
    """HLE-23 (S3-06): every POC row with CC Views > 0 has a minute/second "CC Avg Time Spent"."""
    rows = deals.open_drill_down(_first_drill_down_cell(deals)).values_by_header()
    viewed = [row for row in rows if (row.get(Hle.CC_VIEWS) or "").isdigit() and int(row[Hle.CC_VIEWS]) > 0]
    assert viewed, f"no POC row with CC Views > 0: {rows}"
    bad = [row for row in viewed if not TIME_RE.match(row.get(Hle.CC_AVG_TIME) or "")]
    assert not bad, f"unformatted CC Avg Time Spent: {bad}"


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s3_07_primary_poc_carries_a_primary_chip(deals):
    """HLE-24 (S3-07): in a drill-down where the primary POC viewed, exactly one POC row has a "Primary" chip."""
    rows = [row for row in deals.row_list() if deals.has_drill_down(deals.cc_cell(row))]
    if not rows:
        pytest.skip('needs an Unverified Deals row with a drill-down entry in "CC Views / Time" on page 1')
    for row in rows:
        modal = deals.open_drill_down(deals.cc_cell(row))
        chips = modal.rows_with_primary_chip().count()
        modal.close()
        if chips:
            assert chips == 1, f"{chips} POC rows carry a Primary chip"
            return
    raise AssertionError(f"none of the {len(rows)} drill-downs on page 1 shows a Primary chip")


# ================================================================== S4: drill-down fails to load

INLINE_REASON = ("S4 needs the drill-down to fetch its own data (analysis Q10). Today it reads "
                 "pocEngagementDetails from the listing row (AdminDealsTableModel.js:531-556, no fetchModalData), "
                 "so there is no request to fail")


def _failed_drill_down(deals):
    """Open the drill-down once to learn its request, then open it again with that request failing."""
    page = deals.page
    cell = _first_drill_down_cell(deals)
    calls = []
    track_listener(page, "request", lambda r: calls.append(r.url) if r.resource_type in ("xhr", "fetch") else None)
    deals.open_drill_down(cell).close()
    if not calls:
        pytest.skip(INLINE_REASON)
    # The app reads the body status, not the HTTP code (DealsLink handleOpenModal).
    detail_url = calls[-1].split("?")[0]
    mock_json(page, lambda url: url.split("?")[0] == detail_url, failure_body(status="500"))
    deals.drill_down_entry(cell).click()
    return EngagementModal(page).wait_open()


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s4_01_failed_load_shows_an_error_message(deals):
    """HLE-27 (S4-01): when the engagement detail request fails, the modal shows the error instead of a blank table."""
    modal = _failed_drill_down(deals)
    expect(modal.error_message).to_be_visible()
    expect(modal.rows).to_have_count(0)


@pytest.mark.pending_feature("hot-lead-engagement-visibility")
def test_s4_02_error_state_can_be_closed(deals):
    """HLE-27 (S4-02): the error state closes with "Close" and the table is visible again."""
    modal = _failed_drill_down(deals)
    expect(modal.error_message).to_be_visible()
    modal.close()
    expect(deals.table).to_be_visible()
