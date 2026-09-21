"""Buyer - Express Interest modal, slot step (Figma: Modal - Required Note, calendar & time picker).

Every test here opens the modal and backs out, so none of them create a deal.
"""
import re

import pytest
from playwright.sync_api import expect

from config import settings
from constants import Copy
from pages.buyer_cue_card_page import BuyerCueCardPage

pytestmark = pytest.mark.buyer


@pytest.fixture
def slot_modal(buyer_page, readonly_company_uid):
    cue_card = BuyerCueCardPage(buyer_page).open_cue_card(readonly_company_uid)
    return cue_card.click_express_interest()


@pytest.mark.smoke
def test_express_interest_opens_slot_modal(slot_modal):
    expect(slot_modal.slot_label).to_be_visible()
    expect(slot_modal.request_call_button).to_be_visible()
    expect(slot_modal.cancel_button).to_be_visible()


def test_past_dates_are_disabled(slot_modal):
    # StaticDatePicker runs with disablePast; today's date must still be selectable.
    assert slot_modal.enabled_days().count() > 0
    if slot_modal.past_days().count():
        expect(slot_modal.past_days().first).to_be_disabled()


def test_picking_a_date_shows_time_slots_with_back(slot_modal):
    slot_modal.pick_first_available_date()
    expect(slot_modal.page.get_by_text("India Standard Time (IST)")).to_be_visible()
    assert slot_modal.available_times().count() > 0
    times = slot_modal.available_times().all_inner_texts()
    assert all(re.fullmatch(r"\d{1,2}:\d{2} (AM|PM)", t.strip()) for t in times), times


def test_confirm_selection_disabled_until_time_chosen(slot_modal):
    slot_modal.pick_first_available_date()
    expect(slot_modal.confirm_selection_button).to_be_disabled()
    slot_modal.available_times().first.click()
    expect(slot_modal.confirm_selection_button).to_be_enabled()


def test_back_returns_to_calendar(slot_modal):
    slot_modal.pick_first_available_date()
    slot_modal.page.get_by_text("Back", exact=True).click()
    expect(slot_modal.enabled_days().first).to_be_visible()


def test_confirmed_slot_shows_date_and_30_minute_range(slot_modal):
    picked = slot_modal.add_slot()
    expect(slot_modal.selected_slot_rows().first).to_be_visible()
    range_text = slot_modal.page.get_by_text(re.compile(rf"^{re.escape(picked)} - \d{{1,2}}:\d{{2}} (AM|PM)$")).first
    expect(range_text).to_be_visible()


def test_add_second_slot(slot_modal):
    slot_modal.add_slot()
    expect(slot_modal.page.get_by_text(Copy.ADD_SECOND_SLOT)).to_be_visible()
    slot_modal.add_second_slot()
    expect(slot_modal.selected_slot_rows()).to_have_count(2)


def test_request_call_blocked_until_slot_selected(slot_modal):
    required = slot_modal.slot_label.inner_text().strip().endswith("*")
    if not required:
        pytest.skip("Slot is optional for this buyer/company combination")
    assert slot_modal.is_visually_disabled(slot_modal.request_call_button)
    slot_modal.add_slot()
    if not slot_modal.note_label.count():
        assert not slot_modal.is_visually_disabled(slot_modal.request_call_button)


def test_cancel_asks_for_confirmation_and_sends_nothing(slot_modal):
    requests = []
    slot_modal.page.on("request", lambda r: "deal/capture/interest" in r.url and requests.append(r.url))
    slot_modal.add_slot()
    slot_modal.cancel_button.click()
    expect(slot_modal.page.get_by_text("Your interest has not been sent to the company yet")).to_be_visible()
    assert requests == []


class TestOutsidePreferences:
    """Figma: amber warning + mandatory founder note when the company is outside buyer preferences."""

    @pytest.fixture
    def outside_pref_modal(self, buyer_page):
        if not settings.outside_pref_company_uid:
            pytest.skip("DD_OUTSIDE_PREF_COMPANY_UID is not configured")
        cue_card = BuyerCueCardPage(buyer_page).open_cue_card(settings.outside_pref_company_uid)
        return cue_card.click_express_interest()

    def test_warning_and_required_note_are_shown(self, outside_pref_modal):
        expect(outside_pref_modal.outside_pref_warning).to_be_visible()
        expect(outside_pref_modal.note_label).to_contain_text("*")

    def test_request_call_needs_slot_and_note(self, outside_pref_modal):
        outside_pref_modal.add_slot()
        assert outside_pref_modal.is_visually_disabled(outside_pref_modal.request_call_button)
        outside_pref_modal.fill_note("Exploring minority growth investments.")
        assert not outside_pref_modal.is_visually_disabled(outside_pref_modal.request_call_button)

    def test_note_is_capped_at_400_chars(self, outside_pref_modal):
        outside_pref_modal.fill_note("x" * 450)
        assert len(outside_pref_modal.note_input.input_value()) == 400
