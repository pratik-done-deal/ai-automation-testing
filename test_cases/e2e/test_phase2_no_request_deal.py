"""PHASE 2 - the phase 1 deal that was closed WITHOUT a document request (DR-31 real, DR-22 xfail).

It belongs to a different seller than the request deal, so it runs only when that seller's
session is saved and DD_PHASE2_SELLER_CUE_CARD_UID names this deal's uid:

    python scripts/save_auth_state.py seller      # log in as the no-request company's seller
    DD_PHASE2_SELLER_CUE_CARD_UID=<no-request uid> pytest -m phase2

Ordered: test_01 is read-only, test_02 accepts (one-time), test_03 needs the deal at intro pending.
"""
import re

import pytest
from playwright.sync_api import expect

from constants import DOC_LABELS, INTRO_PENDING_STATUS, MIS, PITCHDECK, Copy
from pages.buyer_module.buyer_cue_card_page import BuyerCueCardPage
from pages.seller_module.seller_deals_page import SellerDealsPage
from utils.api_client import requested_types
from utils.run_state import phase2_record
from utils.sessions import new_role_page

pytestmark = [pytest.mark.e2e, pytest.mark.phase2, pytest.mark.destructive]


@pytest.fixture(scope="module")
def deal():
    return phase2_record(with_request=False)


@pytest.fixture(scope="module")
def seller_session(browser, deal):
    ctx, page = new_role_page(browser, "seller")
    yield page
    ctx.close()


@pytest.fixture(scope="module")
def buyer_session(browser, deal):
    ctx, page = new_role_page(browser, "buyer")
    yield page
    ctx.close()


def _open_accept(seller_session, seller_company_id, deal):
    deals = SellerDealsPage(seller_session).open_deals(seller_company_id, deal_id=deal["deal_id"])
    return deals.open_accept_for_deal(deal["deal_id"])


def test_01_accept_modal_shows_only_the_deck_row(deal, seller_session, seller_company_id):
    """DR-31 (real data): no request -> the section holds only "Pitch Deck *"; counter x/1."""
    modal = _open_accept(seller_session, seller_company_id, deal)
    assert modal.requested_row_types() == [PITCHDECK]
    assert modal.row_is_required(PITCHDECK)
    expect(modal.counter).to_have_text(re.compile(r"^[01]/1$"))
    modal.cancel_button.click()
    modal.wait_until_closed()


def test_02_seller_accepts(deal, seller_session, seller_company_id, make_pdf):
    """Moves the deal to introduction_pending so DR-22 has its precondition."""
    modal = _open_accept(seller_session, seller_company_id, deal)
    if modal.row_status(PITCHDECK) == Copy.NOT_UPLOADED_YET:
        modal.upload_into_row(PITCHDECK, make_pdf("pitch-deck"))
    elif not modal.remove_button(PITCHDECK).count():
        modal.attach_first_file(PITCHDECK)
    if modal.slot_options.count():
        modal.choose_slot(0)
    body = modal.accept_and_capture()
    assert body["dealStatus"] == INTRO_PENDING_STATUS
    modal.wait_until_closed()


@pytest.mark.not_implemented_yet
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="not_implemented_yet: DR-22 no buyer entry point to request documents at "
                          "introduction_pending (status is set by the seller, useIntroductionSetup.js:143)")
def test_03_buyer_can_raise_request_at_introduction_pending(deal, buyer_session):
    """DR-22: at introduction_pending with no request, the buyer can raise one and it is stored.

    No design exists yet, so only the outcome is asserted: an MIS option is offered and sending it
    stores MIS in the deal's requestedDocuments. Tighten the selectors once the screen is designed.
    """
    cue_card = BuyerCueCardPage(buyer_session).open_cue_card(deal["uid"])
    if cue_card.deal_status != INTRO_PENDING_STATUS or cue_card.requested_documents:
        pytest.skip(f"Precondition not met: status {cue_card.deal_status}, request {cue_card.requested_documents}")
    page = cue_card.page

    option = page.get_by_role("button", name=DOC_LABELS[MIS], exact=True)
    expect(option.first).to_be_visible(timeout=10_000)
    option.first.click()
    sent = []
    page.on("request", lambda r: r.method == "POST" and "requestedDocTypes" in (r.post_data or "") and sent.append(r))
    page.get_by_role("button", name=re.compile(r"send|submit|request", re.I)).last.click()
    page.wait_for_load_state("networkidle")
    assert sent, "No request carrying requestedDocTypes was sent"

    stored = requested_types(BuyerCueCardPage(page).open_cue_card(deal["uid"]).requested_documents)
    assert MIS in stored
