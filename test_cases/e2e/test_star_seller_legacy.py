"""A seller starred before star-seller-fundraising: kept, edited, unstarred and re-marked (scenario S18).

Spec: specs/features/star-seller-fundraising/test-cases.md. Admin and biz user, in this order:
S18-01 -> S18-02 -> S18-03 (unstars it for good) -> admin uploads a pitch deck -> S18-04 (biz user)
-> S18-05.

L-star is a funding seller with 3 highlights, no pitch deck, no MIS
and no call, marked star under today's rules BEFORE the release reaches QA. It can't be recreated
once the release is on QA, and S18-03 consumes it, so S18-03 runs only once the feature is on QA.
"""
import pytest

from constants import StarSellerCopy as Ssc
from pages.admin_module.additional_details_modal import names_missing
from pages.admin_module.admin_seller_cue_card_page import AdminSellerCueCardPage
from utils.ssf_data import SLUG, done, require_done, require_shipped, seller


def _legacy_star(page, case):
    return AdminSellerCueCardPage(page).open_seller(seller("L-star", case))


def test_s18_01_legacy_star_without_a_pitch_deck_stays_star(admin_module_page):
    """SSF-32 (S18-01): the legacy star's block still reads "Star: Yes"."""
    cue = _legacy_star(admin_module_page, "S18-01")
    assert cue.star_value() == Ssc.YES


@pytest.mark.destructive
def test_s18_02_legacy_star_can_still_save_other_details(admin_module_page):
    """SSF-32 (S18-02): changing "Growth" on the legacy star saves, and the block still reads "Star: Yes"."""
    cue = _legacy_star(admin_module_page, "S18-02")
    if cue.star_value() != Ssc.YES:
        pytest.skip("S18-02: L-star is no longer star (S18-03 consumed it); prepare another legacy star")
    modal = cue.open_additional_details()
    chip = next((c for c in modal.growth_chips() if not modal.is_selected(c)), None)
    assert chip, "no unselected Growth chip to switch to"
    new_growth = chip.inner_text().strip()
    chip.click()
    modal.confirm()
    cue.reload()
    assert cue.additional_detail_value(Ssc.GROWTH) == new_growth
    assert cue.star_value() == Ssc.YES


@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s18_03_unstarred_legacy_seller_is_blocked_on_the_pitch_deck(admin_module_page):
    """SSF-33 (S18-03): after No + Confirm, clicking Yes again names the pitch deck as missing."""
    cue = _legacy_star(admin_module_page, "S18-03")
    require_shipped("S18-03", "unstarring the legacy star can't be undone once the release is on QA")
    if cue.star_value() != Ssc.YES:
        pytest.skip("S18-03: L-star is no longer star; prepare another legacy star")
    modal = cue.open_additional_details()
    modal.click_star(Ssc.NO)
    modal.confirm()
    cue.reload()
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_PITCH_DECK), text
    modal.cancel()
    done("S18-03", cue.uid)


@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s18_04_biz_user_re_marking_is_blocked_on_mis_or_call(admin_module_page, biz_user_page, make_pdf):
    """SSF-34 (S18-04): with a pitch deck uploaded after S18-03, the biz user is blocked on "MIS ... missing"."""
    uid = require_done("S18-04", "S18-03")
    admin = AdminSellerCueCardPage(admin_module_page).open_seller(uid)
    if not admin.pitch_deck_files():
        admin.open_data_room().upload_pitch_deck(make_pdf("ssf-legacy-pitch-deck"))
    modal = AdminSellerCueCardPage(biz_user_page).open_seller(uid).open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_MIS), text
    done("S18-04", uid)


@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s18_05_admin_re_marks_once_the_new_rules_are_met(admin_module_page):
    """SSF-35 (S18-05): after S18-04, the admin stars the seller again: "Star: Yes"."""
    uid = require_done("S18-05", "S18-04")
    cue = AdminSellerCueCardPage(admin_module_page).open_seller(uid)
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.confirm()
    cue.reload()
    assert cue.star_value() == Ssc.YES
