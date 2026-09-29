"""Biz user star marking and objective change (star-seller-fundraising, scenarios S6-S10 and S16).

Spec: specs/features/star-seller-fundraising/test-cases.md. Needs a biz user (userType 4) session:
`python scripts/save_auth_state.py biz_user`; every test here skips while auth/biz_user.json is
missing. Sellers are browsed for (utils.ssf_browse) and opened from the Sellers list.

A biz user needs the call-or-MIS requirement on top of the admin's. Funding sellers that pass
today (they need only highlights) run as normal tests; the new funding rules, the call/MIS row for
funding sellers and the "<item> is missing" message are pending_feature.
"""
import re

import pytest

from constants import StarSellerCopy as Ssc
from pages.admin_module.additional_details_modal import names_missing
from pages.admin_module.admin_seller_cue_card_page import AdminSellerCueCardPage
from utils.ssf_data import SLUG, done, hold_objective_save_until_shipped, produced_or_env, require_done, seller


@pytest.fixture
def cue(biz_user_page):
    return AdminSellerCueCardPage(biz_user_page)


def _require_not_star(cue, case, name):
    if cue.star_value() == Ssc.YES:
        pytest.skip(f"{case}: {name} is already star from an earlier run; set its Star back to No")


def _star_and_reload(cue, uid, case, name):
    cue.open_seller(uid)
    _require_not_star(cue, case, name)
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.confirm()
    cue.reload()
    return cue.star_value()


def _block_text(cue, uid):
    modal = cue.open_seller(uid).open_additional_details()
    modal.click_star(Ssc.YES)
    return modal.expect_block_message()


# ================================================================== S6: ready funding seller with an MIS

@pytest.mark.smoke
def test_s6_01_clicking_yes_selects_star_with_no_message(cue):
    """SSF-03 (S6-01): on a funding seller with highlights, pitch deck and MIS, "Yes" is selected with no message."""
    cue.open_seller(seller("F-mis", "S6-01"))
    _require_not_star(cue, "S6-01", "F-mis")
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.expect_no_block_message()
    assert modal.star_selected(Ssc.YES)
    modal.cancel()


@pytest.mark.smoke
@pytest.mark.destructive
def test_s6_02_confirm_saves_the_star(cue):
    """SSF-03 (S6-02): Yes + Confirm saves; the block reads "Star: Yes" after reload."""
    uid = seller("F-mis", "S6-02")
    assert _star_and_reload(cue, uid, "S6-02", "F-mis") == Ssc.YES
    done("S6-02", uid)


@pytest.mark.pending_feature(SLUG)
def test_s6_03_biz_user_panel_shows_the_call_or_mis_row_for_funding(cue):
    """SSF-13 (S6-03): a funding seller's panel shows "A completed call with Seller or MIS document upload"."""
    text = cue.open_seller(seller("F-nodeck", "S6-03")).open_additional_details().panel.text()
    assert Ssc.CALL_OR_MIS_ROW in text, text


# ================================================================== S7: completed seller call, no MIS

@pytest.mark.destructive
def test_s7_01_completed_seller_call_stands_in_for_the_mis(cue):
    """SSF-04 (S7-01): a funding seller with a completed 1-on-1 seller call and no MIS is starred."""
    assert _star_and_reload(cue, seller("F-call", "S7-01"), "S7-01", "F-call") == Ssc.YES


# ================================================================== S8: no MIS and no counting seller call

@pytest.mark.pending_feature(SLUG)
def test_s8_01_no_mis_and_no_call_names_the_mis(cue):
    """SSF-05 (S8-01): with no MIS and no calls, the message names the MIS as missing."""
    text = _block_text(cue, seller("F-nomis", "S8-01"))
    assert names_missing(text, Ssc.ITEM_MIS), text


@pytest.mark.pending_feature(SLUG)
def test_s8_02_a_deal_call_with_a_buyer_does_not_count(cue):
    """SSF-06 (S8-02): with only a buyer deal call, the message names the MIS as missing."""
    text = _block_text(cue, seller("F-dealcall", "S8-02"))
    assert names_missing(text, Ssc.ITEM_MIS), text


@pytest.mark.pending_feature(SLUG)
def test_s8_03_a_cancelled_seller_call_does_not_count(cue):
    """SSF-07 (S8-03): with only a cancelled 1-on-1 seller call, the message names the MIS as missing."""
    text = _block_text(cue, seller("F-cancelled", "S8-03"))
    assert names_missing(text, Ssc.ITEM_MIS), text


@pytest.mark.pending_feature(SLUG)
def test_s8_04_a_scheduled_seller_call_does_not_count(cue):
    """SSF-05, SSF-04 (S8-04): with only a scheduled, not completed seller call, the MIS is named as missing."""
    text = _block_text(cue, seller("F-scheduled", "S8-04"))
    assert names_missing(text, Ssc.ITEM_MIS), text


# ================================================================== S9: no pitch deck

@pytest.mark.pending_feature(SLUG)
def test_s9_01_pitch_deck_is_named_when_only_it_is_missing(cue):
    """SSF-08 (S9-01): with highlights and an MIS but no pitch deck, the message names the pitch deck."""
    text = _block_text(cue, seller("F-mis-nodeck", "S9-01"))
    assert names_missing(text, Ssc.ITEM_PITCH_DECK), text


@pytest.mark.pending_feature(SLUG)
def test_s9_02_everything_missing_is_named_in_one_message(cue):
    """SSF-09 (S9-02): one message names "highlight", "pitch deck" and "MIS" as missing."""
    text = _block_text(cue, seller("F-empty", "S9-02"))
    missing = [item for item in (Ssc.ITEM_HIGHLIGHT, Ssc.ITEM_PITCH_DECK, Ssc.ITEM_MIS)
               if not names_missing(text, item)]
    assert not missing, f"not named in {text!r}: {missing}"


# ================================================================== S10: acquisition sellers (rules unchanged)

@pytest.mark.pending_feature(SLUG)
def test_s10_01_acquisition_seller_without_mis_or_call_is_blocked(cue):
    """SSF-12 (S10-01): an acquisition seller with no MIS and no call gets "MIS ... missing"."""
    text = _block_text(cue, seller("A-biz-nomis", "S10-01"))
    assert names_missing(text, Ssc.ITEM_MIS), text


@pytest.mark.destructive
def test_s10_02_acquisition_seller_with_an_mis_is_starred(cue):
    """SSF-12 (S10-02): an acquisition seller with highlights, a teaser and an MIS is starred."""
    assert _star_and_reload(cue, seller("A-biz-mis", "S10-02"), "S10-02", "A-biz-mis") == Ssc.YES


# ================================================================== S16: biz user changes a star seller's objective

@pytest.mark.pending_feature(SLUG)
def test_s16_01_biz_user_gets_the_same_block_on_a_missing_teaser(cue):
    """SSF-18, SSF-19 (S16-01): a star funding seller without a teaser: on selecting Acquisition the message mentions
    "star" and the teaser, and Confirm is disabled."""
    uid = produced_or_env("S16-01", "F-star-biz", "S6-02")
    hold_objective_save_until_shipped(cue.page)
    cue.open_seller(uid)
    if cue.star_value() != Ssc.YES:
        pytest.skip("S16-01: the seller must be star")
    modal = cue.open_objective().select_primary(Ssc.ACQUISITION)
    _, text = modal.expect_star_message()
    assert re.search(re.escape(Ssc.ITEM_TEASER), text, re.I), text
    modal.expect_confirm_disabled()
    modal.cancel()


@pytest.mark.destructive
def test_s16_02_objective_change_ignores_mis_and_seller_call(cue):
    """SSF-29 (S16-02): a star seller with teaser and pitch deck but no MIS/call changes to Acquisition with no message."""
    uid = require_done("S16-02", "S14-05")   # A-star, now funding, with both documents
    modal = cue.open_seller(uid).open_objective().select_primary(Ssc.ACQUISITION)
    modal.expect_no_star_message()
    modal.confirm_and_save()
    cue.reload()
    assert cue.primary_objective() == Ssc.ACQUISITION
