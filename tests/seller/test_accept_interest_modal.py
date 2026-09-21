"""Seller - request shown while accepting (PRD Story 3, 'Visibility gating', 'Not mandatory').

Figma: 'Accept investor interest?' modal - investor's message, 'Request documents from the investor'
rows (Attached / Attach / Upload), timeslot radios incl. 'Neither, schedule over email'.

These tests work on any row already in Interest Received. The deals response is rewritten to
add or strip `requestedDocuments`, and every test backs out with Cancel, so no deal changes state.
"""
import pytest
from playwright.sync_api import expect

from constants import AUDITED, CAP_TABLE, DOC_LABELS, MIS, PITCHDECK, Copy
from pages.accept_interest_modal import seller_label
from pages.seller_deals_page import SellerDealsPage
from utils.network import rewrite_deal_rows, with_requested_docs, without_requested_docs

pytestmark = [pytest.mark.seller, pytest.mark.phase2]

REQUESTED = [MIS, AUDITED]


def _open_first_accept(page, company_id):
    deals = SellerDealsPage(page).open_deals(company_id)
    if deals.rows().count() == 0:
        pytest.skip("Seller has no rows in Interest Received to open")
    return deals.first_row_accept()


@pytest.fixture
def modal_with_request(seller_page, seller_company_id):
    rewrite_deal_rows(seller_page, with_requested_docs(REQUESTED))
    return _open_first_accept(seller_page, seller_company_id)


@pytest.fixture
def modal_without_request(seller_page, seller_company_id):
    rewrite_deal_rows(seller_page, without_requested_docs)
    return _open_first_accept(seller_page, seller_company_id)


@pytest.mark.smoke
def test_requested_documents_listed_while_accepting(modal_with_request):
    expect(modal_with_request.page.get_by_text(Copy.INVESTOR_WANTS_TO_DISCUSS)).to_be_visible()
    for doc_type in REQUESTED:
        expect(modal_with_request.requested_section.get_by_text(seller_label(doc_type), exact=True)).to_be_visible()


def test_pitch_deck_row_pinned_even_when_not_requested(modal_with_request):
    rows = modal_with_request.requested_row_labels()
    assert PITCHDECK in rows
    assert sorted(rows) == sorted([PITCHDECK, *REQUESTED])


def test_non_requested_types_are_not_listed(modal_with_request):
    expect(modal_with_request.requested_section.get_by_text(DOC_LABELS[CAP_TABLE], exact=True)).to_have_count(0)


def test_missing_document_row_offers_upload(modal_with_request):
    # A seller rarely has Audited Financials on file in QA; either state is valid, but the row must be actionable.
    row = modal_with_request.requested_row(AUDITED)
    not_uploaded = row.get_by_text(Copy.NOT_UPLOADED_YET)
    if not_uploaded.count():
        expect(row.get_by_role("button", name=Copy.UPLOAD)).to_be_visible()
    else:
        expect(row.get_by_role("button")).not_to_have_count(0)


def test_only_pitch_deck_row_when_no_request(modal_without_request):
    """PRD 'Visibility gating': the seller view is only populated when a request exists."""
    assert modal_without_request.requested_row_labels() == [PITCHDECK]


def test_investor_message_shows_buyer_note(seller_page, seller_company_id):
    note = "Automation note: please have your financials ready before the call"
    # getInvestorMessage() reads deal.investorNote.description.
    rewrite_deal_rows(seller_page, lambda d: (d.__setitem__("requestedDocuments", REQUESTED),
                                              d.__setitem__("investorNote", {"description": note})))
    modal = _open_first_accept(seller_page, seller_company_id)
    expect(modal.page.get_by_text(Copy.INVESTOR_MESSAGE)).to_be_visible()
    expect(modal.page.get_by_text(note)).to_be_visible()


def test_timeslot_is_required_when_buyer_proposed_slots(modal_with_request):
    if modal_with_request.slot_options.count() == 0:
        pytest.skip("Deal has no buyer-proposed slots")
    expect(modal_with_request.page.get_by_text(Copy.CHOOSE_TIMESLOT)).to_be_visible()
    calls = []
    modal_with_request.page.on("request", lambda r: r.url.rstrip("/").endswith("deal/seller") and calls.append(r))
    modal_with_request.accept_button.click()
    expect(modal_with_request.page.get_by_text(Copy.TIMESLOT_REQUIRED)).to_be_visible()
    assert calls == []


def test_selecting_slot_marks_radio_checked(modal_with_request):
    if modal_with_request.slot_options.count() == 0:
        pytest.skip("Deal has no buyer-proposed slots")
    modal_with_request.choose_slot(0)
    expect(modal_with_request.slot_options.nth(0)).to_have_attribute("aria-checked", "true")


def test_accept_is_not_blocked_by_unfulfilled_non_deck_requests(modal_with_request):
    """PRD 'Not mandatory': open requests for MIS / Audited must not block Accept (only the deck is mandatory)."""
    page = modal_with_request.page
    if modal_with_request.slot_options.count():
        modal_with_request.choose_slot(0)
    deck_missing = modal_with_request.requested_row(PITCHDECK).get_by_text(Copy.NOT_UPLOADED_YET).count() > 0

    page.route("**/deal/seller", lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"status":"200","data":{}}'))
    page.route("**/document/deal/share", lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"status":"200","data":{}}'))

    if deck_missing:
        modal_with_request.accept_button.click()
        expect(page.get_by_text(Copy.PITCH_DECK_MANDATORY)).to_be_visible()
        return
    body = modal_with_request.accept_and_capture()
    assert body["dealStatus"] == "introduction_pending"


def test_placeholder_note_hides_investor_message(seller_page, seller_company_id):
    # Backend sends "--" when the buyer left no note; the card must not render empty.
    rewrite_deal_rows(seller_page, lambda d: d.__setitem__("investorNote", {"description": "--"}))
    modal = _open_first_accept(seller_page, seller_company_id)
    expect(modal.page.get_by_text(Copy.INVESTOR_MESSAGE)).to_have_count(0)


def test_cancel_closes_without_accepting(modal_with_request):
    calls = []
    modal_with_request.page.on("request", lambda r: r.url.rstrip("/").endswith("deal/seller") and calls.append(r))
    modal_with_request.cancel_button.click()
    expect(modal_with_request.page.get_by_text(Copy.INVESTOR_WANTS_TO_DISCUSS)).to_have_count(0)
    assert calls == []
