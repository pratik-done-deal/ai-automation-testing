"""PHASE 2 - seller / admin side of the phase 1 deal that has a document request.

DR-28/29/32/41 on real data, DR-33/38/40 (real upload + the one real Accept), DR-43/44/45/20
(fulfilment), DR-42 (share after accept) and DR-48 (single deal note).

Run after phase 1, once you have the seller's credentials:

    python scripts/save_auth_state.py seller
    DD_PHASE2_SELLER_CUE_CARD_UID=<uid> pytest -m phase2     # uid only needed if phase 1 had several

The tests are ordered and share one deal. test_01 is read-only and must run before test_02,
which accepts: Accept is one-time and removes the row from Interest Received.
"""
import json

import pytest
from playwright.sync_api import expect

from constants import DOC_LABELS, INTRO_PENDING_STATUS, ITR, PITCHDECK, Copy
from pages.seller_module.accept_interest_modal import DEAL_SHARE_API
from pages.admin_module.admin_deal_page import AdminDealPage
from pages.buyer_module.buyer_cue_card_page import BuyerCueCardPage
from pages.seller_module.seller_deals_page import SellerDealsPage
from utils.api_client import find_key, is_success
from utils.run_state import phase2_record
from utils.sessions import new_role_page

pytestmark = [pytest.mark.e2e, pytest.mark.phase2, pytest.mark.destructive]


@pytest.fixture(scope="module")
def deal():
    return phase2_record(with_request=True)


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


@pytest.fixture(scope="module")
def shared(deal):
    """State handed between the ordered tests (uploaded file uids and names)."""
    return {}


def _buyer_docs(buyer_session, deal):
    cue_card = BuyerCueCardPage(buyer_session).open_cue_card(deal["uid"])
    return cue_card, {d["docType"]: d for d in cue_card.requested_documents}


def _open_accept(seller_session, seller_company_id, deal):
    deals = SellerDealsPage(seller_session).open_deals(seller_company_id, deal_id=deal["deal_id"])
    return deals.open_accept_for_deal(deal["deal_id"])


# ------------------------------------------------------------------ Story 3: seller accept + upload

@pytest.mark.smoke
def test_01_seller_sees_request_when_accepting(deal, seller_session, seller_company_id):
    """DR-28, DR-29, DR-32, DR-41 on the real deal (read-only: backs out with Cancel)."""
    modal = _open_accept(seller_session, seller_company_id, deal)
    expect(modal.requested_section.get_by_text(Copy.INVESTOR_WANTS_TO_DISCUSS, exact=True)).to_be_visible()
    expect(modal.investor_message).to_have_text(deal["note"])
    assert modal.requested_row_types() == [PITCHDECK, *deal["requested"]]
    for doc_type in deal["requested"]:  # nothing is attached yet, so each row reports the data room
        assert modal.row_status(doc_type) == modal.expected_status(doc_type), doc_type
    modal.cancel_button.click()
    modal.wait_until_closed()


def test_02_seller_uploads_one_requested_doc_and_accepts(deal, seller_session, seller_company_id, make_pdf, shared):
    """DR-33 (real upload with the row's docType), DR-38 and DR-40 (the one real Accept)."""
    first_requested = deal["requested"][0]
    modal = _open_accept(seller_session, seller_company_id, deal)
    if modal.row_status(PITCHDECK) == Copy.NOT_UPLOADED_YET:
        modal.upload_into_row(PITCHDECK, make_pdf("pitch-deck"))
    elif not modal.remove_button(PITCHDECK).count():
        modal.attach_first_file(PITCHDECK)

    upload_body = modal.upload_into_row(first_requested, make_pdf(first_requested))
    assert f'"docType":"{first_requested}"'.encode() in upload_body.replace(b" ", b"")
    expect(modal.row_button(first_requested, Copy.ATTACHED)).to_be_visible(timeout=20_000)
    shared["uploaded_name"] = modal.row_status(first_requested)
    if modal.slot_options.count():
        modal.choose_slot(0)

    with seller_session.expect_request(lambda r: DEAL_SHARE_API in r.url, timeout=30_000) as share:
        body = modal.accept_and_capture()

    assert body["dealStatus"] == INTRO_PENDING_STATUS
    assert body.get("docUid"), "deal/seller must carry the pitch deck uid"
    assert len(share.value.post_data_json["uids"]) >= 1  # the uploaded requested doc
    modal.wait_until_closed()
    deals = SellerDealsPage(seller_session).open_deals(seller_company_id, deal_id=deal["deal_id"])
    assert int(deal["deal_id"]) not in deals.deal_ids_listed(), "Accepted deal is still in Interest Received"


# ------------------------------------------------------------------ Fulfilment rules

def test_03_non_requested_upload_does_not_touch_request(deal, buyer_session, seller_api, make_pdf):
    """DR-44: uploading a type that wasn't requested (ITR) changes nothing in the request."""
    _, before = _buyer_docs(buyer_session, deal)
    status, payload = seller_api.upload_document(make_pdf("itr"), ITR)
    assert status == 200 and is_success(payload), payload

    _, after = _buyer_docs(buyer_session, deal)
    assert ITR not in after
    assert {k: v.get("fulfilled") for k, v in after.items()} == {k: v.get("fulfilled") for k, v in before.items()}


def test_04_partial_upload_keeps_request_open(deal, buyer_session):
    """DR-43, DR-45, DR-20: the uploaded type is fulfilled (check icon); the rest stay pending."""
    first, *rest = deal["requested"]
    cue_card, docs = _buyer_docs(buyer_session, deal)
    assert docs[first].get("fulfilled") is True
    assert cue_card.chip_is_fulfilled(first)
    for pending in rest:
        assert not docs[pending].get("fulfilled"), f"{pending} should still be pending"
        assert not cue_card.chip_is_fulfilled(pending)


def test_05_remaining_uploads_fulfil_everything(deal, buyer_session, seller_api, make_pdf, shared):
    """DR-43, DR-45: once every requested type is uploaded, every chip shows the check."""
    shared["api_uploads"] = {}
    for doc_type in deal["requested"][1:]:
        pdf = make_pdf(f"{doc_type}-api")
        status, payload = seller_api.upload_document(pdf, doc_type)
        assert status == 200 and is_success(payload), payload
        shared["api_uploads"][doc_type] = pdf.name

    cue_card, docs = _buyer_docs(buyer_session, deal)
    for doc_type in deal["requested"]:
        assert docs[doc_type].get("fulfilled") is True, doc_type
        assert cue_card.chip_is_fulfilled(doc_type)


def test_06_seller_shares_a_requested_doc_from_active_deals(deal, seller_session, seller_company_id, shared):
    """DR-42: after accepting, the seller shares a requested doc through the Active Deals manage-docs flow."""
    if not shared.get("api_uploads"):
        pytest.skip("test_05 uploaded nothing to share")
    doc_type, file_name = next(iter(shared["api_uploads"].items()))
    deals = SellerDealsPage(seller_session).open_deals(seller_company_id, tab=Copy.ACTIVE_DEALS_TAB,
                                                       deal_id=deal["deal_id"])
    deals.open_manage_docs(deal["deal_id"])
    toggle = deals.share_toggle(file_name)
    expect(toggle).to_have_attribute("aria-checked", "false")
    toggle.click()

    body = deals.save_share_edits()

    assert body["dealIds"] == [int(deal["deal_id"])]
    assert len(body["uids"]) == 1
    deals.expect_snackbar(Copy.DOCUMENT_ACCESS_UPDATED)


# ------------------------------------------------------------------ Story 4: buyer owner (admin / biz)

def test_07_request_stored_as_single_deal_note(deal, admin_page):
    """DR-48: exactly one deal note holds the requested types and the buyer's note."""
    with admin_page.expect_response(lambda r: "note/query" in r.url, timeout=30_000) as res:
        AdminDealPage(admin_page).open_deal(deal["deal_id"])
    notes = find_key(res.value.json(), "elements") or find_key(res.value.json(), "content") or []
    notes = notes if isinstance(notes, list) else []
    blob = lambda n: json.dumps(n).lower()  # noqa: E731
    matching = [n for n in notes
                if all(d in blob(n) or DOC_LABELS[d].lower() in blob(n) for d in deal["requested"])]
    assert len(matching) == 1, f"Expected exactly one deal note holding the request, found {len(matching)}"
    assert deal["note"].lower() in blob(matching[0])
