"""PHASE 2 - seller / admin side of a phase 1 deal (PRD Stories 3-4, 'Fulfillment', edge cases
'Seller uploads a document that wasn't requested' and 'Multiple document types requested, only
some uploaded').

Run after phase 1, once you have the seller's credentials:

    python scripts/save_auth_state.py seller
    DD_PHASE2_SELLER_CUE_CARD_UID=<uid> pytest -m phase2     # uid only needed if phase 1 had several

The tests are ordered and share one deal.
"""
import json

import pytest
from playwright.sync_api import expect

from constants import DOC_LABELS, INTRO_PENDING_STATUS, ITR, PITCHDECK, Copy
from pages.admin_deal_page import AdminDealPage
from pages.buyer_cue_card_page import BuyerCueCardPage
from pages.seller_deals_page import SellerDealsPage
from utils.api_client import find_key, is_success
from utils.run_state import phase2_record
from utils.sessions import new_role_page

pytestmark = [pytest.mark.e2e, pytest.mark.phase2, pytest.mark.destructive]


@pytest.fixture(scope="module")
def deal():
    return phase2_record()


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


def _buyer_docs(buyer_session, deal):
    cue_card = BuyerCueCardPage(buyer_session).open_cue_card(deal["uid"])
    docs = find_key(cue_card.cue_card_payload, "requestedDocuments") or []
    return cue_card, {d["docType"]: d for d in docs}


# ------------------------------------------------------------------ Story 3: seller accept + upload

def test_01_seller_sees_request_when_accepting(deal, seller_session, seller_company_id, buyer_display_name):
    modal = SellerDealsPage(seller_session).open_deals(seller_company_id).open_accept(buyer_display_name)
    expect(modal.page.get_by_text(deal["note"])).to_be_visible()
    assert sorted(modal.requested_row_labels()) == sorted([PITCHDECK, *deal["requested"]])
    modal.cancel_button.click()


def test_02_seller_uploads_one_requested_doc_and_accepts(deal, seller_session, seller_company_id,
                                                          buyer_display_name, sample_pdf):
    first_requested = deal["requested"][0]
    modal = SellerDealsPage(seller_session).open_deals(seller_company_id).open_accept(buyer_display_name)
    if modal.requested_row(PITCHDECK).get_by_text(Copy.NOT_UPLOADED_YET).count():
        modal.upload_into_row(PITCHDECK, sample_pdf)
    modal.upload_into_row(first_requested, sample_pdf)
    if modal.slot_options.count():
        modal.choose_slot(0)

    body = modal.accept_and_capture()

    assert body["dealStatus"] == INTRO_PENDING_STATUS
    expect(modal.accept_button).to_have_count(0, timeout=20_000)


# ------------------------------------------------------------------ Fulfilment rules

def test_03_non_requested_upload_does_not_touch_request(deal, buyer_session, seller_api, sample_pdf):
    _, before = _buyer_docs(buyer_session, deal)
    status, payload = seller_api.upload_document(sample_pdf, ITR)
    assert status == 200 and is_success(payload), payload

    _, after = _buyer_docs(buyer_session, deal)
    assert ITR not in after
    assert {k: v.get("fulfilled") for k, v in after.items()} == {k: v.get("fulfilled") for k, v in before.items()}


def test_04_partial_upload_keeps_request_open(deal, buyer_session):
    first, *rest = deal["requested"]
    cue_card, docs = _buyer_docs(buyer_session, deal)
    assert docs[first].get("fulfilled") is True
    assert cue_card.chip_is_fulfilled(first)
    for pending in rest:
        assert not docs[pending].get("fulfilled"), f"{pending} should still be pending"
        assert not cue_card.chip_is_fulfilled(pending)


def test_05_remaining_uploads_fulfil_everything(deal, buyer_session, seller_api, sample_pdf):
    for doc_type in deal["requested"][1:]:
        status, payload = seller_api.upload_document(sample_pdf, doc_type)
        assert status == 200 and is_success(payload), payload

    cue_card, docs = _buyer_docs(buyer_session, deal)
    for doc_type in deal["requested"]:
        assert docs[doc_type].get("fulfilled") is True, doc_type
        assert cue_card.chip_is_fulfilled(doc_type)


# ------------------------------------------------------------------ Story 4: buyer owner (admin / biz)

def test_06_request_stored_as_single_deal_note(deal, admin_page):
    with admin_page.expect_response(lambda r: "note/query" in r.url, timeout=30_000) as res:
        AdminDealPage(admin_page).open_deal(deal["deal_id"])
    notes = find_key(res.value.json(), "content") or find_key(res.value.json(), "data") or []
    notes = notes if isinstance(notes, list) else []
    blob = lambda n: json.dumps(n).lower()  # noqa: E731
    matching = [n for n in notes
                if all(d in blob(n) or DOC_LABELS[d].lower() in blob(n) for d in deal["requested"])]
    assert len(matching) == 1, f"Expected exactly one deal note holding the request, found {len(matching)}"
    assert deal["note"].lower() in blob(matching[0])


@pytest.mark.not_implemented_yet
def test_07_admin_data_room_shows_request(deal, admin_page):
    page = AdminDealPage(admin_page).open_deal(deal["deal_id"]).open_data_room_tab()
    page.expect_topics(deal["requested"])
