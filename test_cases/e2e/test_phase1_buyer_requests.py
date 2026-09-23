"""PHASE 1 - buyer side, no seller login needed.

Starting from /buyer/browse, for each company:
  1. click a mini cue card's "View Listing" (opens the cue card in a new tab),
  2. Express Interest -> pick a slot -> Request Call,
  3. request documents (DR-01, DR-10) and check the cue card shows them (DR-17),
  4. close the tab, back to /buyer/browse, next card.

Then one more company where the buyer closes the step without requesting anything
(DR-13, DR-18); its deal is the "no request" case for phase 2 and the admin pair (DR-31, DR-47).
Turn that round off with DD_PHASE1_NO_REQUEST_ROUND=0.

Companies the buyer already expressed interest in are skipped. Every deal is written to
run_state/phase1.json (title, uid, deal id) - get those sellers' credentials, then run phase 2.

    DD_BROWSE_INTEREST_COUNT=3 pytest -m phase1 --headed
"""
import sys

import pytest
from playwright.sync_api import expect

from config import settings
from constants import AUDITED, CAP_TABLE, DOC_LABELS, MIS, Copy
from pages.buyer_module.buyer_browse_page import BuyerBrowsePage
from utils.api_client import is_success, requested_types
from utils.flows import express_interest_on
from utils.run_state import save_record
from utils.sessions import new_role_page

pytestmark = [pytest.mark.e2e, pytest.mark.phase1, pytest.mark.destructive]

REQUESTED = [MIS, AUDITED, CAP_TABLE]
NOTE = "Automation e2e: please have your financials ready before the call"
NO_REQUEST_NOTE = "Automation e2e: no documents requested for this one"


@pytest.fixture(scope="module")
def browse(browser):
    ctx, page = new_role_page(browser, "buyer")
    yield BuyerBrowsePage(page).open_browse()
    ctx.close()


def _record(uid, title, flow, requested, note):
    save_record(uid, {"title": title, "deal_id": flow.deal_id, "company_id": flow.company_id,
                      "requested": requested, "note": note})
    kind = "request" if requested else "no request"
    sys.__stdout__.write(f"\n  recorded ({kind}): {title} | uid {uid} | deal {flow.deal_id}\n")


@pytest.mark.parametrize("round_no", range(1, settings.browse_interest_count + 1))
def test_express_interest_and_request_docs_from_browse(browse, browse_used, round_no):
    """DR-01, DR-10, DR-12, DR-15, DR-17: request docs at express interest and see them on the cue card."""
    uid, cue_card = browse.open_next_fresh_listing(browse_used)
    title = cue_card.title
    flow = express_interest_on(cue_card, uid, note=NOTE)
    assert flow.deal_id, f"deal/capture/interest did not return a dealId: {flow.success.capture_response}"
    expect(flow.success.page.get_by_text(Copy.DOC_REQUEST_TITLE)).to_be_visible()

    flow.success.toggle(*REQUESTED)
    body, response = flow.success.submit_and_capture()
    assert is_success(response), response
    assert body["requestedDocTypes"] == REQUESTED
    flow.success.wait_until_closed()
    _record(uid, title, flow, REQUESTED, NOTE)

    cue_card.open_cue_card(uid)  # reload to read what the backend stored
    assert sorted(requested_types(cue_card.requested_documents)) == sorted(REQUESTED)
    assert sorted(cue_card.flagged_labels()) == sorted(DOC_LABELS[d] for d in REQUESTED)
    expect(cue_card.expressed_interest_button).to_be_visible()
    # Close only after success: a failed round leaves its tab open for the failure screenshot.
    browse.back_to_browse(cue_card)


@pytest.mark.skipif(not settings.phase1_no_request_round, reason="DD_PHASE1_NO_REQUEST_ROUND=0")
def test_express_interest_and_close_without_request(browse, browse_used):
    """DR-13, DR-18: closing the untouched step sends no update and the cue card has no flagged card."""
    uid, cue_card = browse.open_next_fresh_listing(browse_used)
    title = cue_card.title
    flow = express_interest_on(cue_card, uid, note=NO_REQUEST_NOTE)
    assert flow.deal_id, f"deal/capture/interest did not return a dealId: {flow.success.capture_response}"
    updates = []
    page = flow.success.page
    page.on("request", lambda r: "deal/capture/interest/update" in r.url and updates.append(r.url))

    flow.success.close_button.click()
    flow.success.wait_until_closed()
    assert updates == [], "Close on an untouched step must not call deal/capture/interest/update"
    _record(uid, title, flow, [], NO_REQUEST_NOTE)

    cue_card.open_cue_card(uid)
    assert requested_types(cue_card.requested_documents) == []
    cue_card.expect_no_flagged_card()
    # Close only after success: a failed round leaves its tab open for the failure screenshot.
    browse.back_to_browse(cue_card)
