"""Buyer journey on ONE cue card, no reloads between tests (DR-01 ... DR-21, DR-53).

The card is opened once from /buyer/browse via View Listing (conftest.journey_card). The tests run
in file order, each continuing from where the previous one left the page:

  1. slot modal           - calendar, times, two slots, cancel-then-back (Figma 43762:147112 / 146883 / 146825)
  2. Request Call (real)  - creates the interest; Express Interest is disabled from here on
  3. document step        - options, selection, note, error path, Send request (real)  (43762:147640 / 147749)
  4. after submit         - Expressed Interest, flagged card, lock                       (43762:142649)

Destructive: uses up one company per run and records its deal in run_state/phase1.json, so
phase 2 can pick it up. A failing step doesn't stop the journey: later steps still run, and a step
is skipped only when what it needs never happened (e.g. no confirmation step without Request Call).
Only the steps whose subject is reloading (DR-17 persistence, DR-15 deep link, DR-16, DR-21)
navigate the tab.
"""
import re
import sys
from types import SimpleNamespace

import pytest
from playwright.sync_api import expect

from config import settings
from constants import (
    AUDITED, BUYER_MODAL_OPTIONS, CAP_TABLE, DOC_LABELS, MIS, NOT_BUILT_REQUEST_OPTIONS, PITCHDECK,
    PRD_ALLOWED_DOC_TYPES, PRD_CATEGORIES, Copy, send_request_label,
)
from pages.buyer_module.buyer_cue_card_page import BuyerCueCardPage
from utils.api_client import is_success, requested_types
from utils.network import mock_json
from utils.run_state import save_record
from utils.sessions import cue_card_company_id

pytestmark = [pytest.mark.buyer, pytest.mark.destructive]
DESIGN_FEATURE = "data-room-document-request"  # design.check() steps: specs/features/<this>/flow.yaml

# Deliberately not in display order: the payload keeps click order, the card leads with the deck (DR-19).
REQUESTED = [MIS, CAP_TABLE, PITCHDECK]
NOTE = "Automation journey: please cover MIS and the cap table."
UPDATE_API = "**/deal/capture/interest/update"
FORCED_ERROR = {"status": "500", "message": "Automation forced failure"}


@pytest.fixture(scope="module")
def j(journey_card):
    """Shared state of the journey: the one tab, and what earlier steps produced."""
    uid, cue_card, modal = journey_card
    return SimpleNamespace(uid=uid, cue_card=cue_card, page=cue_card.page, modal=modal, success=None,
                           company_id=cue_card_company_id(cue_card.cue_card_payload), deal_id=None,
                           title=cue_card.title, slots=0, request_sent=False)


# A step skips only when what it needs never happened; otherwise it runs even after earlier failures.

def _modal(j):
    if j.modal is None:
        pytest.skip("needs the Express Interest modal, which didn't open")
    return j.modal


def _success(j):
    if j.success is None:
        pytest.skip("needs the confirmation step, which Request Call didn't reach")
    return j.success


def _need_interest(j):
    if not j.deal_id:
        pytest.skip("needs the interest from Request Call, which wasn't created")


def _need_request(j):
    if not j.request_sent:
        pytest.skip("needs the document request, which Send request didn't store")


# ================================================================== 1. slot modal (nothing sent yet)

@pytest.mark.smoke
def test_express_interest_opens_slot_modal(j, design):
    if j.modal is None:  # the card is still untouched: check it, then open the modal
        design.check("buyer-1-cue-card-before", j.page)
        j.modal = j.cue_card.click_express_interest()
    design.check("buyer-2a-express-interest-calendar", j.page)
    expect(_modal(j).slot_label).to_be_visible()
    expect(_modal(j).request_call_button).to_be_visible()
    expect(_modal(j).cancel_button).to_be_visible()


def test_request_call_blocked_until_slot_selected(j):
    if not _modal(j).slot_label.inner_text().strip().endswith("*"):
        pytest.skip("Slot is optional for this buyer/company combination")
    assert _modal(j).is_visually_disabled(_modal(j).request_call_button)


def test_past_dates_are_disabled(j):
    assert _modal(j).enabled_days().count() > 0
    if _modal(j).past_days().count():
        expect(_modal(j).past_days().first).to_be_disabled()


def test_picking_a_date_shows_time_slots_with_back(j, design):
    _modal(j).pick_date_with_times()
    design.check("buyer-2b-express-interest-timeslots", j.page)
    expect(j.page.get_by_text("India Standard Time (IST)")).to_be_visible()
    times = _modal(j).available_times().all_inner_texts()
    assert times and all(re.fullmatch(r"\d{1,2}:\d{2} (AM|PM)", t.strip()) for t in times), times


def test_confirm_selection_disabled_until_time_chosen(j):
    # Continues on the time view opened by the previous step.
    expect(_modal(j).confirm_selection_button).to_be_disabled()
    _modal(j).available_times().first.click()
    expect(_modal(j).confirm_selection_button).to_be_enabled()


def test_back_returns_to_calendar(j):
    _modal(j).back_link.click()
    expect(_modal(j).enabled_days().first).to_be_visible()


def test_confirmed_slot_shows_date_and_30_minute_range(j, design):
    picked = _modal(j).add_slot()
    j.slots = 1
    design.check("buyer-2c-express-interest-filled", j.page)
    expect(_modal(j).selected_slot_rows().first).to_be_visible()
    time_range = re.compile(rf"^{re.escape(picked)} - \d{{1,2}}:\d{{2}} (AM|PM)$")
    expect(j.page.get_by_text(time_range).first).to_be_visible()


def test_add_second_slot(j):
    expect(j.page.get_by_text(Copy.ADD_SECOND_SLOT)).to_be_visible()
    _modal(j).add_second_slot()
    expect(_modal(j).selected_slot_rows()).to_have_count(2)
    j.slots = 2


def test_cancel_asks_for_confirmation_and_back_keeps_slots(j):
    sent = []
    j.page.on("request", lambda r: r.url.rstrip("/").endswith("deal/capture/interest") and sent.append(r.url))
    _modal(j).cancel_button.click()
    expect(_modal(j).cancel_confirmation).to_be_visible()
    _modal(j).cancel_confirmation_back.click()
    expect(_modal(j).cancel_confirmation).to_have_count(0)
    expect(_modal(j).selected_slot_rows()).to_have_count(j.slots)
    assert sent == []


# ================================================================== 2. Request Call (real)

@pytest.mark.smoke
def test_request_call_creates_the_interest(j):
    if _modal(j).note_label.count():  # the modal asks for the founder note for some companies
        _modal(j).fill_note(NOTE)
    assert not _modal(j).is_visually_disabled(_modal(j).request_call_button)
    j.success = _modal(j).submit()
    j.deal_id = (_success(j).capture_response.get("data") or {}).get("dealId")
    assert j.deal_id, f"deal/capture/interest returned no dealId: {_success(j).capture_response}"
    sys.__stdout__.write(f"\n  journey deal: {j.title} | uid {j.uid} | deal {j.deal_id}\n")


# ================================================================== 3. document request step

@pytest.mark.smoke
def test_success_view_shows_document_request_section(j, design):
    """DR-01: after express interest succeeds, the confirmation step carries the doc-request section."""
    design.check("buyer-3a-success-no-docs", j.page)
    expect(_success(j).title).to_be_visible()
    expect(j.page.get_by_text(Copy.SUCCESS_SUBTITLE)).to_be_visible()
    expect(j.page.get_by_text(Copy.PROPOSED_SLOTS)).to_be_visible()
    assert len(_success(j).proposed_slot_lines()) == j.slots
    expect(j.page.get_by_text(Copy.NOTE_SHARED)).to_be_visible()
    expect(j.page.get_by_text(Copy.DOC_REQUEST_TITLE)).to_be_visible()
    expect(j.page.get_by_text(Copy.DOC_REQUEST_HINT)).to_be_visible()
    expect(_success(j).add_team_member).to_be_visible()


@pytest.mark.smoke
def test_offers_exactly_the_four_built_options_in_order(j):
    """DR-53: Pitchdeck, MIS, Cap Table, Audited Financials - in that order, nothing else."""
    assert _success(j).doc_option_labels() == [DOC_LABELS[k] for k in BUYER_MODAL_OPTIONS]


def test_options_come_only_from_existing_document_list(j):
    """DR-02: every chip is a known doc type, there is no free-text input, and nothing starts selected."""
    assert set(_success(j).doc_option_labels()) <= {DOC_LABELS[k] for k in PRD_ALLOWED_DOC_TYPES}
    assert _success(j).doc_section.locator("input, textarea, [contenteditable='true']").count() == 0
    for doc_type in BUYER_MODAL_OPTIONS:
        assert not _success(j).is_selected(doc_type), f"{doc_type} should start unselected"


def test_only_close_when_nothing_changed(j):
    """DR-07: untouched step shows only "Close" (no Cancel / Submit)."""
    expect(_success(j).close_button).to_be_visible()
    expect(_success(j).primary_button).to_have_count(0)
    expect(j.page.get_by_role("button", name=Copy.CANCEL, exact=True)).to_have_count(0)


@pytest.mark.not_implemented_yet
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="not_implemented_yet: DR-03 Registration & Licenses, ITR, GST Filing and Credit rating "
                          "are commented out of SuccessView.DOCUMENT_REQUEST_OPTIONS (SuccessView.js:32-35)")
def test_other_prd_document_types_are_offered(j):
    """DR-03: the remaining 4 PRD section 8 types are offered as chips too."""
    for doc_type in NOT_BUILT_REQUEST_OPTIONS:
        expect(_success(j).doc_option(doc_type)).to_be_visible(timeout=5_000)


@pytest.mark.not_implemented_yet
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="not_implemented_yet: DR-04 options are a flat list, not grouped by category "
                          "(SuccessView.js:178)")
def test_options_are_grouped_by_category(j):
    """DR-04: chips sit under Company Information / Financial Information / Others."""
    for heading, doc_types in PRD_CATEGORIES.items():
        expect(_success(j).doc_section.get_by_text(heading, exact=True)).to_be_visible(timeout=5_000)
        group = _success(j).category_group(heading)
        for doc_type in doc_types:
            label = re.escape(DOC_LABELS[doc_type])
            expect(group.get_by_role("button", name=re.compile(rf"^{label}"))).to_be_visible()


def test_chip_toggles_selection(j):
    """DR-05: clicking a chip shows the check; clicking again removes it."""
    _success(j).toggle(MIS)
    assert _success(j).is_selected(MIS)
    _success(j).toggle(MIS)
    assert not _success(j).is_selected(MIS)


def test_cta_counts_selected_documents(j):
    """DR-06: with N selected the primary CTA reads "Send request (N)", with Cancel beside it."""
    for count, doc_type in enumerate(BUYER_MODAL_OPTIONS, start=1):
        _success(j).toggle(doc_type)
        expect(_success(j).primary_button).to_have_text(send_request_label(count))
        expect(_success(j).cancel_button).to_be_visible()
        expect(_success(j).close_button).to_have_count(0)
    _success(j).toggle(MIS)
    expect(_success(j).primary_button).to_have_text(send_request_label(len(BUYER_MODAL_OPTIONS) - 1))


def test_cancel_clears_selection_and_edits(j):
    """DR-14: Cancel clears the chips (3 still selected from the previous step), reverts the note, back to "Close"."""
    original_note = _success(j).note_textarea.first.input_value() if _success(j).note_textarea.count() else None
    if original_note is not None:
        _success(j).note_textarea.first.fill("Edited then cancelled")
    _success(j).cancel_button.click()
    for doc_type in BUYER_MODAL_OPTIONS:
        assert not _success(j).is_selected(doc_type)
    if original_note is not None:
        assert _success(j).note_textarea.first.input_value() == original_note
    expect(_success(j).close_button).to_be_visible()


def test_note_on_confirmation_step(j):
    """DR-08 / DR-09: a note written in step 1 shows read-only; otherwise the note is editable (max 400)."""
    if _success(j).note_textarea.count() == 0:  # DR-09: step 1 asked for the note
        expect(_success(j).note_shared_text()).to_have_text(NOTE)
        return
    _success(j).note_textarea.first.fill("x" * 450)  # DR-08
    assert len(_success(j).note_textarea.first.input_value()) == 400
    _success(j).note_textarea.first.fill(NOTE)
    expect(_success(j).primary_button).to_have_text(Copy.SUBMIT)


def test_note_only_submit_omits_requested_types(j):
    """DR-11: note changed, no chips -> "Submit" sends no requestedDocTypes key.

    The reply is forced to an error so the step stays open for the rest of the journey.
    """
    if _success(j).note_textarea.count() == 0:
        pytest.skip("The note was mandatory for this company, so it can't be edited here")
    sent = []
    mock_json(j.page, UPDATE_API, FORCED_ERROR, sent=sent)
    try:
        expect(_success(j).primary_button).to_have_text(Copy.SUBMIT)
        _success(j).primary_button.click()
        _success(j).expect_snackbar(FORCED_ERROR["message"])
    finally:
        j.page.unroute(UPDATE_API)
    assert len(sent) == 1 and "requestedDocTypes" not in sent[0], sent


def test_request_error_keeps_step_open(j):
    """DR-12 (failure path): a failed update shows the error and leaves the step open for a retry."""
    mock_json(j.page, UPDATE_API, FORCED_ERROR)
    try:
        _success(j).toggle(AUDITED)
        _success(j).primary_button.click()
        _success(j).expect_snackbar(FORCED_ERROR["message"])
        expect(_success(j).title).to_be_visible()
        assert _success(j).is_selected(AUDITED)
    finally:
        j.page.unroute(UPDATE_API)
    _success(j).toggle(AUDITED)  # leave only the final selection for the real send


@pytest.mark.smoke
def test_send_request_posts_selected_types_and_closes(j, design):
    """DR-10, DR-12: the real update carries the selection in click order; snackbar, then the step closes."""
    _success(j).toggle(*REQUESTED)
    expect(_success(j).primary_button).to_have_text(send_request_label(len(REQUESTED)))
    design.check("buyer-3b-success-docs-selected", j.page)
    body, response = _success(j).submit_and_capture()

    assert is_success(response), response
    j.request_sent = True
    assert body["requestedDocTypes"] == REQUESTED
    assert body["companyId"] == j.company_id
    assert isinstance(body["interactionNotes"], str) and isinstance(body["teamMembers"], list)
    _success(j).expect_snackbar(response.get("message") or Copy.DOC_REQUEST_SNACKBAR)
    _success(j).wait_until_closed()
    save_record(j.uid, {"title": j.title, "deal_id": j.deal_id, "company_id": j.company_id,
                        "requested": REQUESTED, "note": body["interactionNotes"]})


# ================================================================== 4. after submit, same tab

def test_express_interest_is_now_disabled(j):
    """DR-15: the cue card switched to "Expressed Interest"; there's no Express Interest CTA any more."""
    _need_interest(j)
    expect(j.cue_card.expressed_interest_button).to_be_visible(timeout=15_000)
    expect(j.cue_card.express_interest_button).to_have_count(0)


def test_flagged_card_appears_without_reload(j):
    """DR-17 (live): the flagged card should appear as soon as the step closes."""
    _need_request(j)
    try:
        expect(j.page.get_by_role("heading", name=Copy.FLAGGED_TITLE)).to_be_visible(timeout=5_000)
    except AssertionError:
        pytest.xfail("Cue card isn't refetched after Send request: SuccessView's handleClose only closes "
                     "the modal (SlotSchedulerModal/index.js:628-631). Raise with the frontend team.")


@pytest.mark.smoke
def test_request_persists_after_reload(j, design):
    """DR-17: after a reload the card is rebuilt from the backend: heading, subtitle, one chip per doc."""
    _need_request(j)
    j.cue_card.open_cue_card(j.uid)  # this step's subject is the reload
    expect(j.page.get_by_role("heading", name=Copy.FLAGGED_TITLE)).to_be_visible()
    design.check("buyer-4-cue-card-after", j.page)
    expect(j.page.get_by_text(Copy.FLAGGED_SUBTITLE)).to_be_visible()
    assert sorted(requested_types(j.cue_card.requested_documents)) == sorted(REQUESTED)
    assert sorted(j.cue_card.flagged_labels()) == sorted(DOC_LABELS[d] for d in REQUESTED)


def test_pitch_deck_leads_and_others_keep_request_order(j):
    """DR-19: Pitchdeck first; the rest keep the order they were requested in."""
    _need_request(j)
    expected = [DOC_LABELS[PITCHDECK]] + [DOC_LABELS[d] for d in REQUESTED if d != PITCHDECK]
    assert j.cue_card.flagged_labels() == expected


def test_chip_icon_matches_fulfilment_state(j):
    """DR-20 (pending half): each chip shows the check only when requestedDocuments[].fulfilled is true."""
    _need_request(j)
    for doc in j.cue_card.requested_documents:
        assert j.cue_card.chip_is_fulfilled(doc["docType"]) == bool(doc.get("fulfilled")), doc
        if doc["docType"] != PITCHDECK:  # the seller may already hold a deck in the data room
            assert not doc.get("fulfilled"), f"{doc['docType']} can't be fulfilled before any upload"


def test_no_ui_to_change_the_request_after_close(j):
    """DR-15: read-only flagged card, and the deep link that normally opens the modal doesn't reopen it."""
    _need_request(j)
    expect(j.cue_card.flagged_card_controls()).to_have_count(0)
    j.cue_card.open_cue_card(j.uid, "?showExpressInterest=true")  # SlotSchedulerModal/index.js:265
    expect(j.cue_card.expressed_interest_button).to_be_visible()
    expect(j.page.get_by_text(Copy.DOC_REQUEST_TITLE)).to_have_count(0)
    expect(j.page.get_by_text(re.compile(Copy.SLOT_LABEL, re.I))).to_have_count(0)


@pytest.mark.api
def test_backend_rejects_adding_documents_after_lock(j, buyer_api):
    """DR-16: a second update with other types must leave the stored request unchanged."""
    _need_request(j)
    status, payload = buyer_api.update_interest(j.company_id, notes="late add", requested_doc_types=[MIS, AUDITED])
    stored = requested_types(BuyerCueCardPage(j.page).open_cue_card(j.uid).requested_documents)
    assert AUDITED not in stored, f"Locked request was modified (API said {status} {payload})"
    assert sorted(stored) == sorted(REQUESTED)


@pytest.mark.not_implemented_yet
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="not_implemented_yet: DR-21 the buyer deals tab shows no requested documents "
                          "(nothing in src/Container/BuyersDealsContainer)")
def test_buyer_deals_tab_shows_requested_docs_and_status(j):
    """DR-21: /buyer/deals deal detail lists the requested docs, each marked pending or fulfilled."""
    _need_request(j)
    j.page.goto(f"{settings.app_url}buyer/deals?dealId={j.deal_id}&s=deals")
    j.page.wait_for_load_state("networkidle")
    for doc_type in (MIS, CAP_TABLE):  # the deck label also appears on existing pitch-deck CTAs
        expect(j.page.get_by_text(DOC_LABELS[doc_type], exact=True).first).to_be_visible(timeout=10_000)
    expect(j.page.get_by_text(re.compile(r"\b(pending|fulfilled)\b", re.I)).first).to_be_visible()
