"""PHASE 1 - buyer side, no seller login needed.

Starting from /buyer/browse, for each company:
  1. click a mini cue card's "View Listing" (opens the cue card in a new tab),
  2. Express Interest -> pick a slot -> Request Call,
  3. request documents (PRD Story 1) and check the cue card shows them,
  4. close the tab, back to /buyer/browse, next card.

Companies the buyer already expressed interest in are skipped. Every deal is written to
run_state/phase1.json (title, uid, deal id) - get those sellers' credentials, then run phase 2.

    DD_BROWSE_INTEREST_COUNT=3 pytest -m phase1 --headed
"""
import sys

import pytest
from playwright.sync_api import expect

from config import settings
from constants import AUDITED, CAP_TABLE, DOC_LABELS, MIS, Copy
from pages.buyer_browse_page import BuyerBrowsePage
from utils.api_client import find_key, is_success, requested_types
from utils.flows import express_interest_on
from utils.run_state import load_all, save_record
from utils.sessions import new_role_page

pytestmark = [pytest.mark.e2e, pytest.mark.phase1, pytest.mark.destructive]

REQUESTED = [MIS, AUDITED, CAP_TABLE]
NOTE = "Automation e2e: please have your financials ready before the call"
MAX_CARDS_TO_TRY = 40


@pytest.fixture(scope="module")
def browse(browser):
    ctx, page = new_role_page(browser, "buyer")
    browse_page = BuyerBrowsePage(page).open_browse()
    browse_page.tried = set(load_all())  # never reuse a company from an earlier phase 1 run
    yield browse_page
    ctx.close()


def _next_fresh_listing(browse):
    """Open listings in turn until one still offers Express Interest; returns (uid, cue_card)."""
    for _ in range(MAX_CARDS_TO_TRY):
        uid = next((u for u in browse.listing_uids() if u not in browse.tried), None)
        if uid is None:
            if not browse.load_more():
                break
            continue
        browse.tried.add(uid)
        cue_card = browse.open_listing(uid)
        if cue_card.can_express_interest():
            return uid, cue_card
        browse.back_to_browse(cue_card)  # already expressed interest in this one
    pytest.fail(f"No company on /buyer/browse still offers Express Interest (tried {len(browse.tried)})")


@pytest.mark.parametrize("round_no", range(1, settings.browse_interest_count + 1))
def test_express_interest_and_request_docs_from_browse(browse, round_no):
    uid, cue_card = _next_fresh_listing(browse)
    title = cue_card.title
    try:
        flow = express_interest_on(cue_card, uid, note=NOTE)
        assert flow.deal_id, f"deal/capture/interest did not return a dealId: {flow.success.capture_response}"

        flow.success.toggle(*REQUESTED)
        body, response = flow.success.submit_and_capture()
        assert is_success(response), response
        assert sorted(body["requestedDocTypes"]) == sorted(REQUESTED)
        flow.success.wait_until_closed()

        save_record(uid, {"title": title, "deal_id": flow.deal_id, "company_id": flow.company_id,
                          "requested": REQUESTED, "note": NOTE})
        sys.__stdout__.write(f"\n  recorded: {title} | uid {uid} | deal {flow.deal_id}\n")

        cue_card.open_cue_card(uid)  # reload to read what the backend stored
        docs = find_key(cue_card.cue_card_payload, "requestedDocuments")
        assert sorted(requested_types(docs)) == sorted(REQUESTED)
        assert sorted(cue_card.flagged_labels()) == sorted(DOC_LABELS[d] for d in REQUESTED)
        expect(cue_card.expressed_interest_button).to_be_visible()
        expect(cue_card.page.get_by_text(Copy.FLAGGED_TITLE)).to_be_visible()
    finally:
        browse.back_to_browse(cue_card)
