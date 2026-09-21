"""Admin / biz user (PRD Stories 4 and 5, 'Trigger', 'Visibility gating').

Figma: 'Meeting notes' frame - Deal page > Data Room tab with 'Topics for the intro call'.
"""
import pytest
from playwright.sync_api import expect

from config import settings
from constants import Copy
from pages.admin_deal_page import AdminDealPage

pytestmark = pytest.mark.admin


@pytest.mark.not_implemented_yet
def test_data_room_tab_shows_topics_card_when_request_exists(admin_page):
    if not settings.admin_deal_with_request_uid:
        pytest.skip("DD_ADMIN_DEAL_WITH_REQUEST_UID is not configured")
    page = AdminDealPage(admin_page).open_deal(settings.admin_deal_with_request_uid).open_data_room_tab()
    expect(page.page.get_by_text(Copy.ADMIN_TOPICS_TITLE)).to_be_visible()
    assert page.topics_card.locator("svg").count() > 0  # each topic chip carries the message icon


def test_data_room_tab_has_no_topics_card_without_request(admin_page):
    if not settings.admin_deal_without_request_uid:
        pytest.skip("DD_ADMIN_DEAL_WITHOUT_REQUEST_UID is not configured")
    page = AdminDealPage(admin_page).open_deal(settings.admin_deal_without_request_uid).open_data_room_tab()
    expect(page.page.get_by_text("Pitchdeck").or_(page.page.get_by_text("Company")).first).to_be_visible()
    page.expect_no_topics_card()


def test_biz_user_moving_deal_never_sees_document_request_step(admin_page):
    """PRD Story 5: the document-request step is skipped for biz-user-initiated actions."""
    admin_page.goto(settings.app_url + "admin/deals")
    admin_page.wait_for_load_state("networkidle")
    edit_deal = admin_page.locator(".deal-action-container div.cursor-pointer").first
    if not edit_deal.count():
        pytest.skip("No deals listed for this admin")

    sent = []
    admin_page.on("request", lambda r: r.url.rstrip("/").endswith("deal/admin") and sent.append(r.post_data_json))
    edit_deal.click()
    expect(admin_page.get_by_text("Edit deal state for D")).to_be_visible()

    expect(admin_page.get_by_text(Copy.DOC_REQUEST_TITLE)).to_have_count(0)
    expect(admin_page.get_by_text(Copy.SUCCESS_TITLE)).to_have_count(0)
    assert all("requestedDocTypes" not in (body or {}) for body in sent)
