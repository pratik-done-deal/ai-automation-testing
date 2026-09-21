"""Multi-step buyer flows reused by fixtures and module-scoped setups."""
from dataclasses import dataclass

from pages.buyer_cue_card_page import BuyerCueCardPage
from pages.interest_shared_modal import InterestSharedModal
from utils.sessions import cue_card_company_id

DEFAULT_NOTE = "Automation: keen to discuss growth and unit economics."


@dataclass
class ExpressedInterest:
    cue_card: BuyerCueCardPage
    success: InterestSharedModal
    uid: str
    company_id: int
    note: str

    @property
    def deal_id(self):
        return (self.success.capture_response.get("data") or {}).get("dealId")


def run_express_interest(page, uid, note=DEFAULT_NOTE) -> ExpressedInterest:
    """Open a cue card by uid, then express interest on it."""
    return express_interest_on(BuyerCueCardPage(page).open_cue_card(uid), uid, note)


def express_interest_on(cue_card: BuyerCueCardPage, uid, note=DEFAULT_NOTE) -> ExpressedInterest:
    """Click Express Interest, pick one slot (plus the note when required) and land on the success view."""
    modal = cue_card.click_express_interest()
    modal.add_slot()
    if modal.note_label.count():
        modal.fill_note(note)
    success = modal.submit()
    return ExpressedInterest(cue_card, success, uid, cue_card_company_id(cue_card.cue_card_payload), note)
