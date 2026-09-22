"""Buyer journey on ONE company outside the buyer's preferences, no reloads (DR-09).

Figma "Modal - Required Note" (43762:147112): amber warning, and the founder note becomes mandatory.
The card is opened once (conftest.outside_pref_journey_card) and the steps run in order on it.
Request Call is mocked at the end, so this company is never used up.
"""
import pytest
from playwright.sync_api import expect

from utils.flows import mock_interest_capture

pytestmark = [pytest.mark.buyer, pytest.mark.incremental]

NOTE = "Exploring minority growth investments. Would like to discuss ARR growth."


@pytest.fixture(scope="module")
def modal(outside_pref_journey_card):
    return outside_pref_journey_card[2]


def test_founder_note_is_required(modal):
    expect(modal.note_label).to_be_visible()
    expect(modal.note_label).to_contain_text("*")


@pytest.mark.not_implemented_yet
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="not_implemented_yet: Figma's amber 'You are expressing interest in a company outside "
                          "your preferences' banner isn't in src/ (only the mandatory note is)")
def test_outside_preference_warning_is_shown(modal):
    expect(modal.outside_pref_warning).to_be_visible(timeout=3_000)


def test_request_call_needs_slot_and_note(modal):
    modal.add_slot()
    assert modal.is_visually_disabled(modal.request_call_button)
    modal.fill_note(NOTE)
    assert not modal.is_visually_disabled(modal.request_call_button)


def test_note_is_capped_at_400_chars(modal):
    modal.fill_note("x" * 450)
    assert len(modal.note_input.input_value()) == 400
    modal.fill_note(NOTE)


def test_mandatory_note_is_read_only(modal):
    """DR-09: the note written in step 1 shows as text under "Note shared with the founder:"."""
    mock_interest_capture(modal.page, [])  # no deal: this company stays available
    success = modal.submit()
    expect(success.note_shared_text()).to_have_text(NOTE)
    expect(success.note_textarea).to_have_count(0)
