"""Backend contract for `deal/capture/interest/update` (PRD section 6 "Logics").

Each test expresses interest for real on a company from /buyer/browse (the only way to get a fresh
deal with the right slots) and, while the document-request step is still open, calls the update
endpoint directly: the same call "Send request (N)" makes. One company per test.
"""
import pytest

from constants import AUDITED, MIS
from pages.buyer_cue_card_page import BuyerCueCardPage
from utils.api_client import is_success, requested_types

pytestmark = [pytest.mark.api, pytest.mark.destructive]

UNKNOWN_TYPES = ["bank_statements", "Please send your cap table", "", "PITCH_DECK"]


def _stored_types(flow):
    return requested_types(BuyerCueCardPage(flow.cue_card.page).open_cue_card(flow.uid).requested_documents)


def test_unknown_or_free_text_types_are_not_stored(live_success_view, buyer_api):
    """DR-02 (backend): only existing doc-type keys can be stored; no free-text names."""
    status, payload = buyer_api.update_interest(live_success_view.company_id, requested_doc_types=UNKNOWN_TYPES)
    stored = _stored_types(live_success_view)
    assert not set(stored) & set(UNKNOWN_TYPES), f"Unknown type persisted (API said {status} {payload})"


def test_empty_list_creates_no_request(live_success_view, buyer_api):
    """DR-11 / DR-13 (backend): an empty requestedDocTypes stores nothing."""
    status, payload = buyer_api.update_interest(live_success_view.company_id, requested_doc_types=[])
    assert status == 200, payload
    assert _stored_types(live_success_view) == []


def test_second_submission_cannot_extend_request(live_success_view, buyer_api):
    """DR-16 (unverified, analysis Q7): one-time capture - a second call must not add AUDITED."""
    first_status, first = buyer_api.update_interest(live_success_view.company_id, requested_doc_types=[MIS])
    assert first_status == 200 and is_success(first), first

    buyer_api.update_interest(live_success_view.company_id, requested_doc_types=[MIS, AUDITED])
    assert _stored_types(live_success_view) == [MIS]


def test_request_locked_after_modal_closed_empty(live_success_view, buyer_api):
    """DR-15 / DR-16 (unverified): closing without selecting locks the request - a later call stores nothing."""
    live_success_view.success.close_button.click()
    live_success_view.success.wait_until_closed()

    buyer_api.update_interest(live_success_view.company_id, requested_doc_types=[MIS])
    assert _stored_types(live_success_view) == []
