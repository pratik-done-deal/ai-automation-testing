"""Buyer - state after a document request is raised (PRD section 5 'Buyer', 6 'One-time capture').

Figma: detailed cue card after submit - success toast, 'Expressed Interest' disabled, and the
'You flagged for the intro call' card listing the requested topics.

One request is raised for the whole module; the tests then read that state.
"""
import pytest
from playwright.sync_api import expect

from constants import CAP_TABLE, DOC_LABELS, MIS, PITCHDECK, Copy
from pages.buyer_cue_card_page import BuyerCueCardPage
from utils.api_client import find_key, is_success, requested_types
from utils.sessions import cue_card_company_id, new_role_page

pytestmark = [pytest.mark.buyer, pytest.mark.destructive]

# Deliberately not in display order: the card must still lead with the pitch deck.
REQUESTED = [MIS, CAP_TABLE, PITCHDECK]


@pytest.fixture(scope="module")
def raised_request(browser, uid_pool):
    uid = uid_pool.take()
    ctx, page = new_role_page(browser, "buyer")
    cue_card = BuyerCueCardPage(page).open_cue_card(uid)
    modal = cue_card.click_express_interest()
    modal.add_slot()
    if modal.note_label.count():
        modal.fill_note("Automation: please cover MIS and cap table.")
    success = modal.submit()
    success.toggle(*REQUESTED)
    _, response = success.submit_and_capture()
    assert is_success(response), response
    success.wait_until_closed()
    yield {"page": page, "uid": uid, "company_id": cue_card_company_id(cue_card.cue_card_payload)}
    ctx.close()


@pytest.fixture
def cue_card(raised_request):
    return BuyerCueCardPage(raised_request["page"]).open_cue_card(raised_request["uid"])


@pytest.mark.smoke
def test_cue_card_shows_flagged_card_with_requested_docs(cue_card):
    expect(cue_card.page.get_by_role("heading", name=Copy.FLAGGED_TITLE)).to_be_visible()
    expect(cue_card.page.get_by_text(Copy.FLAGGED_SUBTITLE)).to_be_visible()
    assert sorted(cue_card.flagged_labels()) == sorted(DOC_LABELS[d] for d in REQUESTED)


def test_pitch_deck_leads_the_flagged_list(cue_card):
    assert cue_card.flagged_labels()[0] == DOC_LABELS[PITCHDECK]


def test_new_request_items_start_pending(cue_card):
    docs = find_key(cue_card.cue_card_payload, "requestedDocuments")
    assert sorted(requested_types(docs)) == sorted(REQUESTED)
    for doc in docs:
        if doc.get("docType") != PITCHDECK:  # the seller may already hold a deck in the data room
            assert doc.get("fulfilled") in (False, None), doc
            assert not cue_card.chip_is_fulfilled(doc["docType"])


def test_express_interest_is_locked_after_submit(cue_card):
    expect(cue_card.expressed_interest_button).to_be_visible()
    expect(cue_card.express_interest_button).to_have_count(0)


def test_request_persists_after_reload(cue_card):
    cue_card.page.reload()
    expect(cue_card.page.get_by_role("heading", name=Copy.FLAGGED_TITLE)).to_be_visible()
    assert sorted(cue_card.flagged_labels()) == sorted(DOC_LABELS[d] for d in REQUESTED)


@pytest.mark.api
def test_backend_rejects_adding_documents_after_lock(raised_request, buyer_api):
    """PRD: 'Once the modal is closed, the request is locked - no further documents can be added.'"""
    status, payload = buyer_api.update_interest(
        raised_request["company_id"], notes="late add", requested_doc_types=[REQUESTED[0], "audited_financials"],
    )
    refreshed = BuyerCueCardPage(raised_request["page"]).open_cue_card(raised_request["uid"])
    stored = requested_types(find_key(refreshed.cue_card_payload, "requestedDocuments"))

    assert "audited_financials" not in stored, f"Locked request was modified (API said {status} {payload})"
    assert sorted(stored) == sorted(REQUESTED)


@pytest.mark.not_implemented_yet
def test_buyer_deals_tab_shows_requested_docs_and_status(raised_request):
    """PRD section 5: 'Post-request, the buyer's deals tab ... show[s] the requested documents and their status'."""
    page = raised_request["page"]
    page.goto(page.url.split("/buyer/")[0] + "/buyer/deals")
    page.wait_for_load_state("networkidle")
    for doc_type in REQUESTED:
        expect(page.get_by_text(DOC_LABELS[doc_type], exact=True).first).to_be_visible()
    expect(page.get_by_text("Pending", exact=False).first).to_be_visible()
