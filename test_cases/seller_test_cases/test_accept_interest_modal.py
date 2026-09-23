"""Seller - request shown while accepting (DR-28 ... DR-41).

Figma: "Accept investor interest?" (44585:103166). The app's copy is asserted where it differs
(gap G5): "The investor would like to discuss", "Pitch Deck", "Audited Financials", "Cap Table".

Read-only on any row already in Interest Received: the deal rows, the seller's data room
(document/query) and the seller slots are rewritten, and deal/seller, document/deal/share and
document/user/upload are answered locally. No deal changes state and nothing is uploaded.
Runs with the phase 2 seller session, before the phase 2 journey that really accepts.
"""
import re
from dataclasses import dataclass, field

import pytest
from playwright.sync_api import expect

from constants import AUDITED, CAP_TABLE, INTRO_PENDING_STATUS, MIS, PITCHDECK, Copy, files_in_data_room
from pages.seller_module.accept_interest_modal import AcceptInterestModal, seller_label
from pages.seller_module.seller_deals_page import SellerDealsPage
from utils.network import (
    FAKE_SLOTS, fake_doc, mock_json, mock_seller_slots, mock_upload, rewrite_deal_rows, rewrite_seller_documents,
    success_body, with_investor_note, with_requested_docs, without_requested_docs,
)

pytestmark = [pytest.mark.seller, pytest.mark.phase2]


@dataclass
class OpenModal:
    modal: AcceptInterestModal
    deal: dict
    user_doc_map: dict
    accept_calls: list = field(default_factory=list)
    share_calls: list = field(default_factory=list)
    uploads: list = field(default_factory=list)


def open_modal(page, company_id, requested=(MIS, AUDITED), files=None, slots=(), note=None) -> OpenModal:
    """Open Accept on the first Interest Received row with a controlled request, data room and slots.

    `files` = {doc_type: count} of fake data-room files; `slots` = seller slots (empty = none required).
    """
    def mutate(deal):
        (with_requested_docs(requested) if requested else without_requested_docs)(deal)
        if note is not None:
            with_investor_note(note)(deal)

    rewrite_deal_rows(page, mutate)
    user_doc_map = rewrite_seller_documents(page, files or {})
    mock_seller_slots(page, list(slots))
    # Registered last so they win over the broad deal-row rewrite: nothing reaches the backend.
    opened = OpenModal(None, {}, user_doc_map)
    mock_json(page, "**/deal/seller", success_body(), sent=opened.accept_calls)
    mock_json(page, "**/document/deal/share", success_body(), sent=opened.share_calls)
    mock_upload(page, user_doc_map, opened.uploads)

    deals = SellerDealsPage(page).open_deals(company_id)
    opened.modal = deals.first_row_accept()
    opened.deal = deals.deals[0] if deals.deals else {}
    return opened


# ------------------------------------------------------------------ what the seller sees

@pytest.mark.smoke
def test_accept_opens_modal_with_request_section(seller_page, seller_company_id):
    """DR-28: Accept opens "Accept investor interest?" with "The investor would like to discuss"."""
    modal = open_modal(seller_page, seller_company_id).modal
    expect(modal.heading).to_be_visible()
    expect(modal.identity_line).to_be_visible()
    expect(modal.requested_section.get_by_text(Copy.INVESTOR_WANTS_TO_DISCUSS, exact=True)).to_be_visible()


def test_one_row_per_requested_type_in_request_order(seller_page, seller_company_id):
    """DR-29: rows "Pitch Deck", "MIS", "Cap Table" for a request of [MIS, Cap Table]."""
    modal = open_modal(seller_page, seller_company_id, requested=[MIS, CAP_TABLE]).modal
    assert modal.row_labels() == [seller_label(PITCHDECK), seller_label(MIS), seller_label(CAP_TABLE)]


@pytest.mark.parametrize("requested", [[MIS], [MIS, PITCHDECK]], ids=["deck-not-requested", "deck-requested"])
def test_pitch_deck_row_is_pinned_first_required_and_single(seller_page, seller_company_id, requested):
    """DR-30: the Pitch Deck row is always there, first, marked "*", and never duplicated."""
    modal = open_modal(seller_page, seller_company_id, requested=requested).modal
    assert modal.requested_row_types() == [PITCHDECK, MIS]
    assert modal.row_is_required(PITCHDECK)
    assert not modal.row_is_required(MIS)


def test_only_pitch_deck_row_without_request(seller_page, seller_company_id):
    """DR-31: with no request the section holds just "Pitch Deck *" and the counter reads x/1."""
    modal = open_modal(seller_page, seller_company_id, requested=None).modal
    assert modal.requested_row_types() == [PITCHDECK]
    expect(modal.counter).to_have_text(re.compile(r"^[01]/1$"))


def test_row_status_reflects_the_data_room(seller_page, seller_company_id):
    """DR-32: "Not uploaded yet", "N file(s) in your data room", or the attached file's name."""
    opened = open_modal(seller_page, seller_company_id, requested=[MIS, AUDITED, CAP_TABLE],
                        files={MIS: 2, AUDITED: 1})
    modal = opened.modal
    assert modal.row_status(PITCHDECK) == Copy.NOT_UPLOADED_YET
    assert modal.row_status(MIS) == files_in_data_room(2)
    assert modal.row_status(AUDITED) == files_in_data_room(1)
    assert modal.row_status(CAP_TABLE) == Copy.NOT_UPLOADED_YET
    picked = modal.attach_first_file(MIS)
    assert modal.row_status(MIS) == picked


def test_upload_sends_the_row_type_and_auto_attaches(seller_page, seller_company_id, make_pdf):
    """DR-33: "Upload" on an empty row posts that row's docType, then the new file shows as "Attached"."""
    opened = open_modal(seller_page, seller_company_id, requested=[CAP_TABLE], files={PITCHDECK: 1})
    modal = opened.modal
    expect(modal.row_button(CAP_TABLE, Copy.UPLOAD)).to_be_visible()

    modal.upload_into_row(CAP_TABLE, make_pdf("cap-table"))

    assert opened.uploads == [CAP_TABLE]
    expect(modal.row_button(CAP_TABLE, Copy.ATTACHED)).to_be_visible(timeout=15_000)
    assert modal.row_status(CAP_TABLE) == fake_doc(CAP_TABLE, 1)["fileName"]


def test_attach_existing_file_then_remove(seller_page, seller_company_id):
    """DR-34: "Attach" lists files of that type; once picked, "Attached" plus a remove (x) button."""
    modal = open_modal(seller_page, seller_company_id, requested=[MIS], files={PITCHDECK: 1, MIS: 2}).modal
    expect(modal.row_button(MIS, Copy.ATTACH)).to_be_visible()
    modal.row_button(MIS, Copy.ATTACH).click()
    expect(modal.page.get_by_role("menuitem")).to_have_count(2)
    modal.page.keyboard.press("Escape")

    modal.attach_first_file(MIS)
    expect(modal.row_button(MIS, Copy.ATTACHED)).to_be_visible()
    modal.remove_button(MIS).click()
    expect(modal.row_button(MIS, Copy.ATTACH)).to_be_visible()
    assert modal.row_status(MIS) == files_in_data_room(2)


def test_counter_counts_attached_rows(seller_page, seller_company_id):
    """DR-35: the header counter reads attached/total rows."""
    modal = open_modal(seller_page, seller_company_id, requested=[MIS, AUDITED],
                       files={PITCHDECK: 1, MIS: 1}).modal
    expect(modal.counter).to_have_text("1/3")  # the deck is pre-attached
    modal.attach_first_file(MIS)
    expect(modal.counter).to_have_text("2/3")


def test_deck_is_pre_attached_once(seller_page, seller_company_id):
    """DR-36: a deck on file is pre-attached once; removing it isn't undone by later changes.

    document/query carries no upload time (utils.js:73-75), so "latest" resolves to the first
    listed deck (IntroductionSetupModal.js:134-136) - see the plan's gap list.
    """
    modal = open_modal(seller_page, seller_company_id, requested=[MIS], files={PITCHDECK: 2, MIS: 1}).modal
    assert modal.row_status(PITCHDECK) == fake_doc(PITCHDECK, 1)["fileName"]
    expect(modal.row_button(PITCHDECK, Copy.ATTACHED)).to_be_visible()

    modal.remove_button(PITCHDECK).click()
    modal.attach_first_file(MIS)
    expect(modal.row_button(PITCHDECK, Copy.ATTACH)).to_be_visible()


@pytest.mark.parametrize("deck_files, message", [(1, Copy.PITCH_DECK_MANDATORY_SHARE),
                                                 (0, Copy.PITCH_DECK_MANDATORY_UPLOAD)],
                         ids=["deck-on-file", "no-deck"])
def test_accept_without_a_deck_is_blocked(seller_page, seller_company_id, deck_files, message):
    """DR-37: no deck attached -> the mandatory message (share vs upload wording) and no deal/seller call."""
    opened = open_modal(seller_page, seller_company_id, requested=[MIS], files={PITCHDECK: deck_files})
    modal = opened.modal
    if deck_files:
        modal.remove_button(PITCHDECK).click()
    modal.accept_button.click()
    expect(modal.pitch_deck_error).to_have_text(message)
    assert opened.accept_calls == []


def test_open_requests_do_not_block_accept(seller_page, seller_company_id):
    """DR-38: deck attached, MIS and Audited requested but not attached -> Accept still goes through."""
    opened = open_modal(seller_page, seller_company_id, requested=[MIS, AUDITED], files={PITCHDECK: 1})
    body = opened.modal.accept_and_capture()
    assert body["dealStatus"] == INTRO_PENDING_STATUS
    assert len(opened.accept_calls) == 1


def test_timeslot_is_required_when_slots_exist(seller_page, seller_company_id):
    """DR-39: with buyer slots, Accept without a slot shows "Please choose a timeslot to continue."."""
    opened = open_modal(seller_page, seller_company_id, requested=[MIS], files={PITCHDECK: 1}, slots=FAKE_SLOTS)
    modal = opened.modal
    expect(modal.page.get_by_text(Copy.CHOOSE_TIMESLOT)).to_be_visible()
    expect(modal.slot_options).to_have_count(len(FAKE_SLOTS))
    modal.accept_button.click()
    expect(modal.page.get_by_text(Copy.TIMESLOT_REQUIRED)).to_be_visible()
    assert opened.accept_calls == []

    modal.choose_slot(0)
    expect(modal.slot_options.nth(0)).to_have_attribute("aria-checked", "true")
    expect(modal.page.get_by_text(Copy.TIMESLOT_REQUIRED)).to_have_count(0)


def test_accept_payload_and_extra_share(seller_page, seller_company_id):
    """DR-40: deal/seller carries the deck as docUid and the slot; other attached docs go via document/deal/share."""
    opened = open_modal(seller_page, seller_company_id, requested=[MIS], files={PITCHDECK: 1, MIS: 1},
                        slots=FAKE_SLOTS)
    modal = opened.modal
    modal.attach_first_file(MIS)
    modal.choose_slot(1)

    with modal.page.expect_request(lambda r: "document/deal/share" in r.url, timeout=15_000):
        body = modal.accept_and_capture()

    assert body["dealStatus"] == INTRO_PENDING_STATUS
    assert body["docUid"] == fake_doc(PITCHDECK, 1)["uid"]
    assert str(body["slotId"]) == str(FAKE_SLOTS[1]["id"])
    assert body["buyerId"] == opened.deal.get("buyerId")
    assert body["companyId"] == opened.deal.get("sellerId")
    assert opened.share_calls == [{"dealIds": [opened.deal.get("id")], "uids": [fake_doc(MIS, 1)["uid"]]}]


@pytest.mark.parametrize("note, shown", [("Automation note: please have your financials ready", True),
                                         ("--", False), ("   ", False)],
                         ids=["note", "placeholder", "blank"])
def test_investor_message_only_when_buyer_left_a_note(seller_page, seller_company_id, note, shown):
    """DR-41: "Investor's message:" + the note when present; hidden for "--" or blank."""
    modal = open_modal(seller_page, seller_company_id, note=note).modal
    if shown:
        expect(modal.page.get_by_text(Copy.INVESTOR_MESSAGE, exact=True)).to_be_visible()
        expect(modal.investor_message).to_have_text(note)
    else:
        expect(modal.page.get_by_text(Copy.INVESTOR_MESSAGE, exact=True)).to_have_count(0)


@pytest.mark.parametrize("dismiss", ["cancel", "close-icon"])
def test_dismiss_closes_without_accepting(seller_page, seller_company_id, dismiss):
    """DR-28 (exit path): Cancel or the x closes the modal and sends nothing."""
    opened = open_modal(seller_page, seller_company_id, files={PITCHDECK: 1})
    modal = opened.modal
    (modal.cancel_button if dismiss == "cancel" else modal.close_icon).click()
    modal.wait_until_closed()
    assert opened.accept_calls == []
