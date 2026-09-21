"""Backend contract for `deal/capture/interest/update` (PRD section 6 'Logics').

Each test expresses interest through the real UI (the only way to get a fresh deal with the right
slots) and, while the document-request step is still open, calls the update endpoint directly -
the same call the "Send request (N)" button makes.
"""
import pytest

from constants import AUDITED, MIS, PITCHDECK
from pages.buyer_cue_card_page import BuyerCueCardPage
from utils.api_client import find_key, is_success, requested_types

pytestmark = [pytest.mark.api, pytest.mark.destructive]


def _stored_types(page, uid):
    cue_card = BuyerCueCardPage(page).open_cue_card(uid)
    return requested_types(find_key(cue_card.cue_card_payload, "requestedDocuments"))


def test_valid_types_are_stored(buyer_at_success_view, buyer_api):
    status, payload = buyer_api.update_interest(
        buyer_at_success_view.company_id, requested_doc_types=[PITCHDECK, MIS])
    assert status == 200 and is_success(payload), payload
    assert sorted(_stored_types(buyer_at_success_view.cue_card.page, buyer_at_success_view.uid)) == [MIS, PITCHDECK]


@pytest.mark.parametrize("bad_type", ["bank_statements", "Please send your cap table", "", "PITCH_DECK"])
def test_free_text_or_unknown_types_are_rejected(buyer_at_success_view, buyer_api, bad_type):
    """PRD: 'existing document type list only. No free-text document names.'"""
    status, payload = buyer_api.update_interest(buyer_at_success_view.company_id, requested_doc_types=[bad_type])
    stored = _stored_types(buyer_at_success_view.cue_card.page, buyer_at_success_view.uid)
    assert bad_type not in stored, f"Unknown type persisted (API said {status} {payload})"


def test_empty_list_creates_no_request(buyer_at_success_view, buyer_api):
    status, payload = buyer_api.update_interest(buyer_at_success_view.company_id, requested_doc_types=[])
    assert status == 200, payload
    assert _stored_types(buyer_at_success_view.cue_card.page, buyer_at_success_view.uid) == []


def test_second_submission_cannot_extend_request(buyer_at_success_view, buyer_api):
    """PRD: one-time capture - the second call must not add AUDITED."""
    first_status, first = buyer_api.update_interest(buyer_at_success_view.company_id, requested_doc_types=[MIS])
    assert first_status == 200 and is_success(first), first

    buyer_api.update_interest(buyer_at_success_view.company_id, requested_doc_types=[MIS, AUDITED])
    assert _stored_types(buyer_at_success_view.cue_card.page, buyer_at_success_view.uid) == [MIS]


def test_duplicate_types_are_stored_once(buyer_at_success_view, buyer_api):
    buyer_api.update_interest(buyer_at_success_view.company_id, requested_doc_types=[MIS, MIS])
    assert _stored_types(buyer_at_success_view.cue_card.page, buyer_at_success_view.uid) == [MIS]


def test_request_locked_after_modal_closed_empty(buyer_at_success_view, buyer_api):
    """PRD: closing without selecting = no request, and the request is locked once the modal closes."""
    buyer_at_success_view.success.close_button.click()
    buyer_at_success_view.success.wait_until_closed()

    buyer_api.update_interest(buyer_at_success_view.company_id, requested_doc_types=[MIS])
    assert _stored_types(buyer_at_success_view.cue_card.page, buyer_at_success_view.uid) == []
