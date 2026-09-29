"""Admin star marking on the seller cue card (star-seller-fundraising, scenarios S1-S5 and S11).

Spec: specs/features/star-seller-fundraising/test-cases.md. One admin context for the file; every
test browses for the seller it needs (utils.ssf_browse) and opens its cue card from Sellers > tab >
Actions "View", skipping, naming the kind of seller, when none fits.

Cases that pass on today's build (the save path, rules that don't change) run as normal tests; the
new funding rule, the requirements-panel rows and the "<item> is missing" message are
pending_feature and run as strict xfail until the feature ships. Cases that click Confirm on
Star = Yes star a real seller: they are `destructive` (reset: set Star back to No).
"""
import re

import pytest
from playwright.sync_api import expect

from constants import StarSellerCopy as Ssc
from pages.admin_module.additional_details_modal import names_missing
from pages.admin_module.admin_seller_cue_card_page import AdminSellerCueCardPage
from pages.admin_module.admin_sellers_page import AdminSellersPage
from utils.ssf_data import SLUG, done, require_done, require_shipped, seller


@pytest.fixture
def cue(admin_module_page):
    return AdminSellerCueCardPage(admin_module_page)


def _has(text, needle):
    return bool(re.search(re.escape(needle), text, re.I))


def _require_not_star(cue, case, name):
    if cue.star_value() == Ssc.YES:
        pytest.skip(f"{case}: {name} is already star from an earlier run; set its Star back to No")


# ================================================================== S1: ready funding seller (highlights + pitch deck)

@pytest.mark.smoke
@pytest.mark.pending_feature(SLUG)
def test_s1_01_requirements_panel_lists_the_pitch_deck(cue):
    """SSF-13 (S1-01): a funding seller's "Star seller requirements" panel names "Pitch deck" under the highlights row."""
    panel = cue.open_seller(seller("F-ready", "S1-01")).open_additional_details().panel
    text = panel.text()
    assert _has(text, Ssc.PITCH_DECK), text
    assert text.lower().index(Ssc.HIGHLIGHTS_ROW.lower()) < text.lower().index(Ssc.PITCH_DECK.lower()), text


def test_s1_02_admin_panel_has_no_call_or_mis_row(cue):
    """SSF-14 (S1-02): the admin's panel never shows "A completed call with Seller or MIS document upload"."""
    text = cue.open_seller(seller("F-ready", "S1-02")).open_additional_details().panel.text()
    assert Ssc.CALL_OR_MIS_ROW not in text, text


@pytest.mark.smoke
def test_s1_03_clicking_yes_selects_star_with_no_message(cue):
    """SSF-01 (S1-03): on a ready funding seller "Yes" is selected and no "is missing" message appears."""
    cue.open_seller(seller("F-ready", "S1-03"))
    _require_not_star(cue, "S1-03", "F-ready")
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.expect_no_block_message()
    assert modal.star_selected(Ssc.YES)
    modal.cancel()


@pytest.mark.smoke
@pytest.mark.destructive
def test_s1_04_confirm_saves_the_star(cue):
    """SSF-01 (S1-04): Yes + Confirm on a ready funding seller saves; the block reads "Star: Yes" after reload."""
    uid = seller("F-ready", "S1-04")
    cue.open_seller(uid)
    _require_not_star(cue, "S1-04", "F-ready")   # clicking Yes on a star seller would unselect it
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.confirm()
    cue.reload()
    assert cue.star_value() == Ssc.YES
    done("S1-04", uid)


@pytest.mark.destructive
def test_s1_05_starred_seller_is_in_the_star_sellers_tab(cue):
    """SSF-01 (S1-05): after S1-04 the seller's row in "Star Sellers" shows the star after its S-id."""
    uid = require_done("S1-05", "S1-04")
    sid, _ = cue.open_seller(uid).seller_heading()
    row = AdminSellersPage(cue.page).open_star_sellers(sid).row(sid)
    expect(row).to_contain_text(Ssc.STAR_MARK)


@pytest.mark.pending_feature(SLUG)
def test_s1_06_pitch_deck_row_is_a_verified_document(cue):
    """SSF-13 (S1-06): the funding pitch deck row reads "A verified document" with "Pitch deck" beneath it."""
    panel = cue.open_seller(seller("F-nodeck", "S1-06")).open_additional_details().panel
    assert _has(panel.row_description(Ssc.VERIFIED_DOCUMENT), Ssc.PITCH_DECK)


@pytest.mark.pending_feature(SLUG)
def test_s1_07_cue_card_edit_modal_shows_the_pitch_deck_requirement(cue):
    """SSF-13 (S1-07): the panel at the top of "Cue card edit" names "Pitch deck"."""
    text = cue.open_seller(seller("F-ready", "S1-07")).open_cue_card_edit().panel.text()
    assert _has(text, Ssc.PITCH_DECK), text


# ================================================================== S2: funding seller with highlights, no pitch deck

@pytest.mark.smoke
@pytest.mark.pending_feature(SLUG)
def test_s2_01_clicking_yes_shows_the_pitch_deck_is_missing(cue):
    """SSF-02 (S2-01): clicking "Yes" shows a message naming the pitch deck as missing."""
    modal = cue.open_seller(seller("F-nodeck", "S2-01")).open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_PITCH_DECK), text


@pytest.mark.pending_feature(SLUG)
def test_s2_02_seller_stays_non_star_after_the_block(cue):
    """SSF-02, SSF-15 (S2-02): Yes then Confirm leaves the seller non-star after reload."""
    modal = cue.open_seller(seller("F-nodeck", "S2-02")).open_additional_details()
    modal.click_star(Ssc.YES)
    # Without the block, Confirm would really star F-nodeck: stop here while the rule is absent.
    modal.expect_block_message()
    modal.confirm(expect_save=False)
    cue.reload()
    assert cue.star_value() != Ssc.YES   # a never-set star shows no "Star:" row at all


@pytest.mark.pending_feature(SLUG)
def test_s2_03_message_names_only_the_missing_item(cue):
    """SSF-09 (S2-03): with only the pitch deck missing, the message doesn't name the highlights."""
    modal = cue.open_seller(seller("F-nodeck", "S2-03")).open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert not _has(text, Ssc.ITEM_HIGHLIGHT), text


@pytest.mark.pending_feature(SLUG)
def test_s2_04_back_to_cue_card_closes_the_modal(cue):
    """(S2-04, new — needs an id): "Back to cue card" closes the modal and the cue card is visible."""
    modal = cue.open_seller(seller("F-nodeck", "S2-04")).open_additional_details()
    modal.back_to_cue_card()
    expect(modal.root).to_have_count(0)
    expect(cue.block(Ssc.OBJECTIVE_BLOCK)).to_be_visible()


# ================================================================== S3: funding seller missing highlights and pitch deck

@pytest.mark.pending_feature(SLUG)
def test_s3_01_one_message_names_highlights_and_pitch_deck(cue):
    """SSF-09 (S3-01): one message names both "highlight" and "pitch deck" as missing."""
    modal = cue.open_seller(seller("F-empty", "S3-01")).open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_HIGHLIGHT) and names_missing(text, Ssc.ITEM_PITCH_DECK), text


def test_s3_02_highlights_row_shows_the_count_added(cue):
    """SSF-13 (S3-02): the highlights row reads "<N> of 3 added on the cue card" with N below 3."""
    panel = cue.open_seller(seller("F-empty", "S3-02")).open_additional_details().panel
    count = panel.highlights_count()
    assert count is not None and count < 3, panel.text()


@pytest.mark.pending_feature(SLUG)
def test_s3_03_highlight_under_50_characters_does_not_count(cue):
    """SSF-01 (S3-03): with one highlight under 50 characters, the message names the highlights as missing."""
    modal = cue.open_seller(seller("F-short", "S3-03")).open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_HIGHLIGHT), text


# ================================================================== S4: other settings must not block the star

@pytest.mark.destructive
def test_s4_01_funding_seller_open_to_acquisition_needs_no_teaser(cue):
    """SSF-10 (S4-01): a "Primary: Funding | Secondary: Acquisition" seller with no teaser is starred."""
    cue.open_seller(seller("F-open", "S4-01"))
    _require_not_star(cue, "S4-01", "F-open")
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.confirm()
    cue.reload()
    assert cue.star_value() == Ssc.YES


def test_s4_02_panel_shows_no_teaser_row(cue):
    """SSF-10 (S4-02): that seller's panel has no "Investment teaser" row."""
    text = cue.open_seller(seller("F-open", "S4-02")).open_additional_details().panel.text()
    assert not _has(text, Ssc.INVESTMENT_TEASER), text


@pytest.mark.destructive
def test_s4_03_pitch_deck_consent_off_does_not_block(cue):
    """SSF-11 (S4-03): a seller whose pitch deck consent setting is off is starred."""
    cue.open_seller(seller("F-noconsent", "S4-03"))
    _require_not_star(cue, "S4-03", "F-noconsent")
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.confirm()
    cue.reload()
    assert cue.star_value() == Ssc.YES


# ================================================================== S5: acquisition sellers (rules unchanged)

@pytest.mark.destructive
def test_s5_01_acquisition_seller_with_highlights_and_teaser_is_starred(cue):
    """SSF-12 (S5-01): an acquisition seller with highlights and a teaser (no pitch deck) is starred."""
    uid = seller("A-ready", "S5-01")
    cue.open_seller(uid)
    _require_not_star(cue, "S5-01", "A-ready")
    modal = cue.open_additional_details()
    modal.click_star(Ssc.YES)
    modal.confirm()
    cue.reload()
    assert cue.star_value() == Ssc.YES
    done("S5-01", uid)


@pytest.mark.pending_feature(SLUG)
def test_s5_02_missing_teaser_is_named_in_the_new_format(cue):
    """SSF-12 (S5-02): the missing teaser is named as "investment teaser ... missing" (replaces today's toast)."""
    modal = cue.open_seller(seller("A-noteaser", "S5-02")).open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_TEASER), text


def test_s5_03_acquisition_panel_still_asks_for_the_teaser(cue):
    """SSF-12 (S5-03): the acquisition panel shows "A qualifying document" with "Investment teaser" beneath it."""
    panel = cue.open_seller(seller("A-noteaser", "S5-03")).open_additional_details().panel
    assert _has(panel.row_description(Ssc.QUALIFYING_DOCUMENT), Ssc.INVESTMENT_TEASER)


@pytest.mark.pending_feature(SLUG)
def test_s5_04_acquisition_seller_missing_both_gets_one_message(cue):
    """SSF-09, SSF-12 (S5-04): one message names both "highlight" and "investment teaser" as missing."""
    modal = cue.open_seller(seller("A-empty", "S5-04")).open_additional_details()
    modal.click_star(Ssc.YES)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_HIGHLIGHT) and names_missing(text, Ssc.ITEM_TEASER), text


# ================================================================== S11: documents change around the star

@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s11_01_pitch_deck_deleted_before_confirm_blocks_the_save(cue):
    """SSF-16, SSF-15 (S11-01): pitch decks deleted in a second tab before Confirm block the save."""
    uid = seller("F-del", "S11-01")
    require_shipped("S11-01", "it deletes the seller's pitch decks, and without the rule Confirm would star it")
    modal = cue.open_seller(uid).open_additional_details()
    modal.click_star(Ssc.YES)
    tab2 = cue.page.context.new_page()
    try:
        deleted, left = AdminSellerCueCardPage(tab2).open_seller(uid).open_data_room().delete_all_pitch_decks()
        if left:
            pytest.skip("S11-01: the seller's pitch deck can't be deleted (shared with a buyer); "
                        "needs a seller whose pitch deck was never shared")
        assert deleted, "F-del has no pitch deck in its Data Room to delete"
    finally:
        tab2.close()
    modal.confirm(expect_save=False)
    text = modal.expect_block_message()
    assert names_missing(text, Ssc.ITEM_PITCH_DECK), text
    cue.reload()
    assert cue.star_value() != Ssc.YES


@pytest.mark.destructive
def test_s11_02_deleting_the_pitch_deck_after_starring_keeps_the_star(cue):
    """SSF-17 (S11-02): deleting every pitch deck of a star seller leaves "Star: Yes"."""
    cue.open_seller(seller("F-star-del", "S11-02"))
    if cue.star_value() != Ssc.YES:
        pytest.skip("S11-02: F-star-del must be a star funding seller with a pitch deck")
    _, left = cue.open_data_room().delete_all_pitch_decks()
    if left:
        pytest.skip("S11-02: the seller's pitch deck can't be deleted (shared with a buyer); "
                    "needs a star seller whose pitch deck was never shared")
    cue.reload()
    assert cue.star_value() == Ssc.YES
