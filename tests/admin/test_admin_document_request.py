"""Admin / biz user (DR-23, DR-24 UI half, DR-46 + DR-47 xfail pair).

Figma: "Meeting notes" frame 43790:150553 - Deal page > Data Room tab with "Topics for the intro call".
Read-only: nothing here changes a deal.
"""
import re

import pytest
from playwright.sync_api import expect

from config import settings
from constants import Copy
from pages.admin_deal_page import AdminCueCardPage, AdminDealPage
from utils.run_state import latest

pytestmark = pytest.mark.admin


def _deal_pair():
    """(deal with a request + its types, deal without a request): .env overrides, else phase 1's deals."""
    with_request = latest(with_request=True)
    without_request = latest(with_request=False)
    with_id = settings.admin_deal_with_request_uid or (with_request or {}).get("deal_id")
    without_id = settings.admin_deal_without_request_uid or (without_request or {}).get("deal_id")
    if not with_id or not without_id:
        pytest.skip("Needs a deal with and one without a request: run phase 1 (with DD_PHASE1_NO_REQUEST_ROUND=1) "
                    "or set DD_ADMIN_DEAL_WITH_REQUEST_UID / DD_ADMIN_DEAL_WITHOUT_REQUEST_UID")
    # Chips are only checked for phase 1's deal, whose requested types are known.
    types = (with_request or {}).get("requested", []) if not settings.admin_deal_with_request_uid else []
    return with_id, types, without_id


@pytest.mark.phase2
@pytest.mark.not_implemented_yet
@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="not_implemented_yet: DR-46/DR-47 no 'Topics for the intro call' card in "
                          "DealNotesContainer/DealDataRoom/index.js")
def test_data_room_topics_card_only_when_request_exists(admin_page):
    """DR-46 + DR-47 as one check: the card lists the request on a deal that has one, and is absent otherwise.

    Paired on purpose: "absent without a request" alone passes today only because the card never renders.
    """
    with_id, types, without_id = _deal_pair()

    page = AdminDealPage(admin_page).open_deal(with_id).open_data_room_tab()
    page.expect_topics(types)

    page = AdminDealPage(admin_page).open_deal(without_id).open_data_room_tab()
    page.expect_no_topics_card()


def test_biz_user_cue_card_has_no_express_interest_or_request_step(admin_page):
    """DR-23: a biz/admin user viewing a company cue card gets no Express Interest CTA or doc-request step."""
    record = latest(with_request=True) or latest(with_request=False)
    if not record:
        pytest.skip("Needs a company uid: run phase 1 first")
    cue_card = AdminCueCardPage(admin_page).open_admin_cue_card(record["uid"])
    assert (cue_card.cue_card_payload or {}).get("data"), "cue card fetch returned no company"
    admin_page.wait_for_load_state("networkidle")
    expect(cue_card.express_interest_button).to_have_count(0)
    expect(admin_page.get_by_text(re.compile(Copy.SLOT_LABEL, re.I))).to_have_count(0)
    expect(admin_page.get_by_text(Copy.DOC_REQUEST_TITLE)).to_have_count(0)


def test_biz_edit_deal_state_has_no_document_request_step(admin_page):
    """DR-23 / DR-24 (UI half): moving a deal in admin tools offers no doc-request step.

    The backend half of DR-24 (no requestedDocuments after a biz transition) needs a real state
    change, so it is left to a manual check.
    """
    admin_page.goto(settings.app_url + "admin/deals")
    admin_page.wait_for_load_state("networkidle")
    edit_deal = admin_page.locator(".deal-action-container div.cursor-pointer").first
    if not edit_deal.count():
        pytest.skip("No deals listed for this admin")
    edit_deal.click()
    expect(admin_page.get_by_text(Copy.ADMIN_EDIT_DEAL_TITLE)).to_be_visible()
    expect(admin_page.get_by_text(Copy.DOC_REQUEST_TITLE)).to_have_count(0)
    expect(admin_page.get_by_text(Copy.SUCCESS_TITLE)).to_have_count(0)
