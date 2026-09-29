"""Admin objective change on a star seller (star-seller-fundraising, scenarios S12-S15 and S17).

Spec: specs/features/star-seller-fundraising/test-cases.md. One admin context for the file.

Sellers are browsed for (utils.ssf_browse) and opened from Sellers > "Star Sellers" > Actions "View":
  * F-star: a star funding seller with no investment teaser (S1-04 may also produce one).
  * A-star: a star acquisition seller with a teaser and no pitch deck.
  * Nonstar-funding (from "Non Star Sellers") for S15-01.
Every case that uploads the missing document uses its seller up (S12-04, S12-05, S13-02, S14-03,
S17-01); the next case of that kind browses for another. The smoke run (S12-01, S12-05) needs one F-star.
Order: the run order of test-cases.md section 6 — S12-01..03, then S13 and S17 (which need the
blocked state before anything uploads the teaser), then S12-04/05; S14 in order; S15 last.

While the feature isn't on QA, the block cases hold the objective save (utils.ssf_data), so their
strict xfail can't really change a star seller's objective.
"""
import json
import re

import pytest
from playwright.sync_api import expect

from constants import StarSellerCopy as Ssc
from pages.admin_module.admin_seller_cue_card_page import AdminSellerCueCardPage
from utils.network import failure_body
from utils.ssf_data import SLUG, done, hold_objective_save_until_shipped, require_done, seller, star_seller

UPLOAD_API = re.compile(r"/document/.*upload")


@pytest.fixture
def cue(admin_module_page):
    return AdminSellerCueCardPage(admin_module_page)


@pytest.fixture(scope="module")
def docx(tmp_path_factory):
    path = tmp_path_factory.mktemp("ssf") / "automation-teaser.docx"
    path.write_bytes(b"PK\x03\x04 not really a word document")
    return path


def _has(text, needle):
    return bool(re.search(re.escape(needle), text, re.I))


def _blocked(cue, uid, case, new_objective, document):
    """Open the objective modal of star seller `uid` and pick `new_objective`: the star-seller message
    shows on selection and Confirm is disabled. Returns (modal, message)."""
    hold_objective_save_until_shipped(cue.page)
    cue.open_seller(uid)
    if cue.star_value() != Ssc.YES:
        pytest.skip(f"{case}: the seller must be star")
    modal = cue.open_objective().select_primary(new_objective)
    message, text = modal.expect_star_message()
    assert _has(text, document), text
    modal.expect_confirm_disabled()
    return modal, message


def _fail_uploads(page):
    page.route(UPLOAD_API, lambda route: route.fulfill(
        status=500, content_type="application/json", body=json.dumps(failure_body()))
        if route.request.method == "POST" else route.fallback())


# ================================================================== S12: star funding -> acquisition, no teaser

@pytest.mark.smoke
@pytest.mark.pending_feature(SLUG)
def test_s12_01_switching_to_acquisition_shows_the_star_seller_message(cue):
    """SSF-18, SSF-19 (S12-01): on selecting Acquisition a message below the dropdown mentions "star" and names
    the investment teaser, and Confirm is disabled."""
    uid = star_seller("S12-01", "F-star", "S1-04")
    _blocked(cue, uid, "S12-01", Ssc.ACQUISITION, Ssc.ITEM_TEASER)


@pytest.mark.pending_feature(SLUG)
def test_s12_02_teaser_upload_option_appears_below_the_message(cue):
    """SSF-20 (S12-02): an investment teaser upload option ("Required", "Upload") is shown right below the message."""
    uid = star_seller("S12-02", "F-star", "S1-04")
    modal, message = _blocked(cue, uid, "S12-02", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    expect(modal.upload_option).to_be_visible()
    expect(modal.required_tag).to_be_visible()
    assert modal.upload_option.bounding_box()["y"] >= message.bounding_box()["y"]


@pytest.mark.pending_feature(SLUG)
def test_s12_03_objective_is_not_saved_while_blocked(cue):
    """SSF-18 (S12-03): after the block and a reload "Company's Objective" still reads "Primary: Funding"."""
    uid = star_seller("S12-03", "F-star", "S1-04")
    _blocked(cue, uid, "S12-03", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    cue.reload()
    assert cue.primary_objective() == Ssc.FUNDING


# ================================================================== S13: failing or wrong upload (blocked state of S12-01)

@pytest.mark.pending_feature(SLUG)
def test_s13_01_failed_upload_shows_an_error(cue, make_pdf):
    """SSF-23 (S13-01): with the upload request failing, an error shows and the star-seller message stays."""
    uid = star_seller("S13-01", "F-star", "S1-04")
    modal, message = _blocked(cue, uid, "S13-01", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    _fail_uploads(cue.page)
    modal.upload(make_pdf("ssf-teaser"))
    expect(modal.upload_error.first).to_be_visible(timeout=15_000)
    expect(message).to_be_visible()
    modal.expect_confirm_disabled()


@pytest.mark.pending_feature(SLUG)
def test_s13_03_wrong_file_type_is_rejected_naming_pdf(cue, docx):
    """SSF-24 (S13-03): a .docx in the upload option is rejected with a message naming PDF; the star message stays."""
    uid = star_seller("S13-03", "F-star", "S1-04")
    modal, message = _blocked(cue, uid, "S13-03", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    modal.upload(docx)
    expect(modal.pdf_rule_message.first).to_be_visible(timeout=15_000)
    expect(message).to_be_visible()
    modal.expect_confirm_disabled()


@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s13_02_user_can_retry_after_a_failed_upload(cue, make_pdf):
    """SSF-23 (S13-02): after a failed upload, a second upload in the same option clears the message and enables Confirm."""
    uid = star_seller("S13-02", "F-star", "S1-04", consumes=True)
    modal, message = _blocked(cue, uid, "S13-02", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    _fail_uploads(cue.page)
    modal.upload(make_pdf("ssf-teaser"))
    expect(modal.upload_error.first).to_be_visible(timeout=15_000)
    cue.page.unroute(UPLOAD_API)
    modal.upload(make_pdf("ssf-teaser"))
    modal.expect_uploaded()


# ================================================================== S17: another tab uploads the missing teaser

@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s17_01_teaser_uploaded_elsewhere_needs_no_second_upload(cue, make_pdf):
    """SSF-30 (S17-01): a teaser uploaded from a second tab while tab 1 is blocked: once tab 1's cue card is
    reloaded, picking Acquisition shows no message and Confirm saves, with no second upload asked.

    The modal reads the documents from the cue card data, so tab 1 only sees tab 2's upload after a reload."""
    uid = star_seller("S17-01", "F-star", "S1-04", consumes=True)
    modal, _ = _blocked(cue, uid, "S17-01", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    # The only teaser upload surface for a funding seller is the objective modal's own option, so
    # tab 2 uses it and cancels (S14-04: an upload before Cancel stays on the profile).
    tab2 = cue.page.context.new_page()
    try:
        hold_objective_save_until_shipped(tab2)
        other, _ = _blocked(AdminSellerCueCardPage(tab2), uid, "S17-01", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
        other.upload(make_pdf("ssf-teaser-tab2"))
        other.expect_uploaded()
        other.cancel()
    finally:
        tab2.close()
    modal.cancel()
    retry = cue.reload().open_objective().select_primary(Ssc.ACQUISITION)
    retry.expect_no_star_message()
    retry.confirm_and_save()
    cue.reload()
    assert cue.primary_objective() == Ssc.ACQUISITION


# ================================================================== S12 (continued): upload and save

@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s12_04_uploading_the_teaser_clears_the_message(cue, make_pdf):
    """SSF-22 (S12-04): uploading a PDF clears the star-seller message; the box shows the file, "Added to the data
    room", and Confirm is enabled."""
    uid = star_seller("S12-04", "F-star", "S1-04", consumes=True)
    modal, _ = _blocked(cue, uid, "S12-04", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    modal.upload(make_pdf("ssf-teaser"))
    text = modal.expect_uploaded()
    assert _has(text, ".pdf"), text


@pytest.mark.smoke
@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s12_05_change_saves_in_the_same_step_after_upload(cue, make_pdf):
    """SSF-22 (S12-05): after the upload, Confirm saves and the block reads "Primary: Acquisition"."""
    uid = star_seller("S12-05", "F-star", "S1-04", consumes=True)
    modal, _ = _blocked(cue, uid, "S12-05", Ssc.ACQUISITION, Ssc.ITEM_TEASER)
    modal.upload(make_pdf("ssf-teaser"))
    modal.expect_uploaded()
    modal.confirm_and_save()
    cue.reload()
    assert cue.primary_objective() == Ssc.ACQUISITION


# ================================================================== S14: star acquisition -> funding, no pitch deck, Cancel

@pytest.mark.pending_feature(SLUG)
def test_s14_01_switching_to_funding_names_the_pitch_deck(cue):
    """SSF-21 (S14-01): a message below the dropdown mentions "star" and names the pitch deck."""
    uid = star_seller("S14-01", "A-star", "S5-01")
    _blocked(cue, uid, "S14-01", Ssc.FUNDING, Ssc.ITEM_PITCH_DECK)


@pytest.mark.pending_feature(SLUG)
def test_s14_02_pitch_deck_upload_option_appears_below_the_message(cue):
    """SSF-21 (S14-02): a pitch deck upload option ("Required", "Upload") is shown below the message."""
    uid = star_seller("S14-02", "A-star", "S5-01")
    modal, message = _blocked(cue, uid, "S14-02", Ssc.FUNDING, Ssc.ITEM_PITCH_DECK)
    expect(modal.upload_option).to_be_visible()
    expect(modal.required_tag).to_be_visible()
    assert modal.upload_option.bounding_box()["y"] >= message.bounding_box()["y"]


@pytest.mark.destructive
@pytest.mark.pending_feature(SLUG)
def test_s14_03_cancel_keeps_the_previous_objective(cue, make_pdf):
    """SSF-25 (S14-03): upload a pitch deck, then Cancel: the block still reads "Primary: Acquisition"."""
    uid = star_seller("S14-03", "A-star", "S5-01", consumes=True)
    modal, _ = _blocked(cue, uid, "S14-03", Ssc.FUNDING, Ssc.ITEM_PITCH_DECK)
    modal.upload(make_pdf("ssf-pitch-deck"))
    modal.expect_uploaded()
    modal.cancel()
    cue.reload()
    assert cue.primary_objective() == Ssc.ACQUISITION
    done("S14-03", uid)


@pytest.mark.pending_feature(SLUG)
def test_s14_04_pitch_deck_uploaded_before_cancel_stays(cue):
    """SSF-26 (S14-04): after S14-03 a pitch deck is listed under "Pitch Deck" in "Important Documents"."""
    uid = require_done("S14-04", "S14-03")
    cue.open_seller(uid)
    assert cue.pitch_deck_files(), "no pitch deck listed under Important Documents"
    done("S14-04", uid)


@pytest.mark.destructive
def test_s14_05_with_the_document_present_the_change_saves(cue):
    """SSF-27 (S14-05): with the pitch deck present, Funding saves with no star-seller message."""
    uid = require_done("S14-05", "S14-04")
    modal = cue.open_seller(uid).open_objective().select_primary(Ssc.FUNDING)
    modal.expect_no_star_message()
    modal.confirm_and_save()   # the save request only goes out when nothing blocks it
    cue.reload()
    assert cue.primary_objective() == Ssc.FUNDING
    done("S14-05", uid)


# ================================================================== S15: non-star seller

@pytest.mark.destructive
def test_s15_01_non_star_seller_changes_objective_with_no_check(cue):
    """SSF-28 (S15-01): a non-star funding seller changes to Acquisition with no message; changed back afterwards."""
    uid = seller("Nonstar-funding", "S15-01")
    cue.open_seller(uid)
    if cue.star_value() == Ssc.YES or cue.primary_objective() != Ssc.FUNDING:
        pytest.skip("S15-01: Nonstar-funding must be a non-star, funding-primary seller")
    modal = cue.open_objective().select_primary(Ssc.ACQUISITION)
    try:
        modal.expect_no_star_message()
        modal.confirm_and_save()
        cue.reload()
        assert cue.primary_objective() == Ssc.ACQUISITION
    finally:
        cue.reload()
        if cue.primary_objective() != Ssc.FUNDING:
            cue.open_objective().select_primary(Ssc.FUNDING).confirm_and_save()
