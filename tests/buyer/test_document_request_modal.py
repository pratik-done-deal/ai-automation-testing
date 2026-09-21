"""Buyer - document request step shown right after Request Call (PRD Story 1, section 6 'Logics').

Figma: 'Interest Shared with Founder' confirmation, empty (Close) and selected (Send request (3)) states.
Each test consumes one fresh company uid because express interest is one-time per company.
"""
import pytest
from playwright.sync_api import expect

from constants import (
    AUDITED, BUYER_MODAL_OPTIONS, CAP_TABLE, DOC_LABELS, MIS, PITCHDECK, PRD_ALLOWED_DOC_TYPES, Copy,
    send_request_label,
)
from pages.buyer_cue_card_page import BuyerCueCardPage
from utils.api_client import find_key, is_success, requested_types

pytestmark = [pytest.mark.buyer, pytest.mark.destructive]


# ------------------------------------------------------------------ layout and copy

@pytest.mark.smoke
def test_success_view_layout_matches_design(buyer_at_success_view):
    success = buyer_at_success_view.success
    expect(success.title).to_be_visible()
    expect(success.page.get_by_text(Copy.SUCCESS_SUBTITLE)).to_be_visible()
    expect(success.page.get_by_text(Copy.PROPOSED_SLOTS)).to_be_visible()
    assert len(success.proposed_slot_lines()) >= 1
    expect(success.page.get_by_text(Copy.NOTE_SHARED)).to_be_visible()
    expect(success.page.get_by_text(Copy.DOC_REQUEST_TITLE)).to_be_visible()
    expect(success.page.get_by_text(Copy.DOC_REQUEST_HINT)).to_be_visible()
    expect(success.page.get_by_text(Copy.ADD_TEAM_MEMBER)).to_be_visible()
    expect(success.close_button).to_be_visible()


def test_options_come_only_from_existing_document_list(buyer_at_success_view):
    success = buyer_at_success_view.success
    labels = success.doc_option_labels()
    allowed_labels = {DOC_LABELS[k] for k in PRD_ALLOWED_DOC_TYPES}

    assert labels == [DOC_LABELS[k] for k in BUYER_MODAL_OPTIONS]
    assert set(labels) <= allowed_labels
    # PRD: "No free-text document names" - the section must not contain any text input.
    assert success.doc_section.locator("input, textarea").count() == 0
    for doc_type in BUYER_MODAL_OPTIONS:
        assert not success.is_selected(doc_type), f"{doc_type} should start unselected"
    success.close_button.click()


# ------------------------------------------------------------------ selection behaviour

def test_selection_count_toggle_and_cancel(buyer_at_success_view):
    success = buyer_at_success_view.success
    expect(success.close_button).to_be_visible()

    for count, doc_type in enumerate(BUYER_MODAL_OPTIONS, start=1):
        success.toggle(doc_type)
        assert success.is_selected(doc_type)
        expect(success.primary_button).to_have_text(send_request_label(count))
        expect(success.close_button).to_have_count(0)

    success.toggle(MIS)
    assert not success.is_selected(MIS)
    expect(success.primary_button).to_have_text(send_request_label(len(BUYER_MODAL_OPTIONS) - 1))

    success.cancel_button.click()
    for doc_type in BUYER_MODAL_OPTIONS:
        assert not success.is_selected(doc_type)
    expect(success.close_button).to_be_visible()
    success.close_button.click()


# ------------------------------------------------------------------ submit paths

@pytest.mark.smoke
@pytest.mark.parametrize("requested", [[PITCHDECK], [PITCHDECK, MIS, CAP_TABLE], BUYER_MODAL_OPTIONS],
                         ids=["one", "three", "all"])
def test_send_request_posts_selected_types(buyer_at_success_view, requested):
    success = buyer_at_success_view.success
    success.toggle(*requested)
    expect(success.primary_button).to_have_text(send_request_label(len(requested)))

    body, response = success.submit_and_capture()

    assert is_success(response), response
    assert sorted(body["requestedDocTypes"]) == sorted(requested)
    assert body["companyId"] == buyer_at_success_view.company_id
    success.expect_snackbar(response.get("message") or Copy.DOC_REQUEST_SNACKBAR)
    success.wait_until_closed()


def test_close_without_selection_creates_no_request(buyer_at_success_view):
    """PRD edge case: buyer closes the modal without selecting anything -> no request, no note."""
    success, page = buyer_at_success_view.success, buyer_at_success_view.success.page
    calls = []
    page.on("request", lambda r: "deal/capture/interest/update" in r.url and calls.append(r))

    success.close_button.click()
    success.wait_until_closed()
    assert calls == [], "Closing an untouched modal must not hit the update endpoint"

    cue_card = BuyerCueCardPage(page).open_cue_card(buyer_at_success_view.uid)
    assert not requested_types(find_key(cue_card.cue_card_payload, "requestedDocuments"))
    cue_card.expect_no_flagged_card()


def test_submit_note_change_without_docs_omits_requested_types(buyer_at_success_view):
    success = buyer_at_success_view.success
    if success.page.locator("textarea:not([aria-hidden='true'])").count() == 0:
        pytest.skip("Note is read-only here (outside-preference flow captured it already)")
    success.page.locator("textarea:not([aria-hidden='true'])").first.fill("Updated note, no documents")
    expect(success.primary_button).to_have_text(Copy.SUBMIT)

    body, response = success.submit_and_capture()

    assert is_success(response), response
    assert "requestedDocTypes" not in body


def test_request_fails_gracefully_on_server_error(buyer_at_success_view):
    page = buyer_at_success_view.success.page
    page.route("**/deal/capture/interest/update", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"status":"500","message":"Automation forced failure"}',
    ))
    success = buyer_at_success_view.success
    success.toggle(AUDITED)
    success.primary_button.click()
    success.expect_snackbar("Automation forced failure")
    expect(success.title).to_be_visible()  # modal stays open so the buyer can retry
