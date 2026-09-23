"""Multi-step buyer flows reused by fixtures and module-scoped setups."""
from dataclasses import dataclass, field

from pages.buyer_module.buyer_cue_card_page import BuyerCueCardPage
from pages.buyer_module.interest_shared_modal import InterestSharedModal
from utils.network import mock_json, success_body
from utils.sessions import cue_card_company_id

DEFAULT_NOTE = "Automation: keen to discuss growth and unit economics."
MOCK_DEAL_ID = 999_999_001


@dataclass
class ExpressedInterest:
    cue_card: BuyerCueCardPage
    success: InterestSharedModal
    uid: str
    company_id: int
    note: str
    mocked: bool = False
    # Request bodies the mocked deal/capture/interest/update received (mocked flows only).
    update_calls: list = field(default_factory=list)

    @property
    def deal_id(self):
        return (self.success.capture_response.get("data") or {}).get("dealId")


def mock_interest_capture(page, update_calls):
    """Answer step 1 and step 2 locally, so reaching the document request step creates no deal.

    SlotSchedulerModal only needs `status == "200"` and `data.dealId > 0` to switch to SuccessView.
    Tests can register their own deal/capture/interest/update route afterwards to override the reply.
    """
    mock_json(page, "**/deal/capture/interest", success_body({"dealId": MOCK_DEAL_ID}))
    mock_json(page, "**/deal/capture/interest/update", success_body(), sent=update_calls)


def run_express_interest(page, uid, note=DEFAULT_NOTE, mock=False) -> ExpressedInterest:
    """Open a cue card by uid, then express interest on it."""
    update_calls = []
    if mock:
        mock_interest_capture(page, update_calls)
    flow = express_interest_on(BuyerCueCardPage(page).open_cue_card(uid), uid, note)
    flow.mocked, flow.update_calls = mock, update_calls
    return flow


def express_interest_on(cue_card: BuyerCueCardPage, uid, note=DEFAULT_NOTE) -> ExpressedInterest:
    """Click Express Interest, pick one slot (plus the note when required) and land on the success view."""
    modal = cue_card.click_express_interest()
    modal.add_slot()
    if modal.note_label.count():
        modal.fill_note(note)
    success = modal.submit()
    return ExpressedInterest(cue_card, success, uid, cue_card_company_id(cue_card.cue_card_payload), note)
