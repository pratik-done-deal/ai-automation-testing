from playwright.sync_api import expect

from constants import DOC_LABELS, Copy
from pages.base_page import BasePage


class AdminDealPage(BasePage):
    """Admin / biz deal page: /admin/deal-notes/:uid -> Data Room tab (Figma "Meeting notes" frame)."""

    def open_deal(self, uid: str):
        self.open(f"admin/deal-notes/{uid}")
        return self

    def open_data_room_tab(self):
        self.page.get_by_role("tab", name=Copy.ADMIN_DATA_ROOM_TAB).or_(
            self.page.get_by_text(Copy.ADMIN_DATA_ROOM_TAB, exact=True)
        ).first.click()
        return self

    @property
    def topics_card(self):
        return self.page.locator("div").filter(has_text=Copy.ADMIN_TOPICS_TITLE).last

    def topic_chip(self, doc_type):
        return self.topics_card.get_by_text(DOC_LABELS[doc_type], exact=True)

    def expect_topics(self, doc_types):
        expect(self.page.get_by_text(Copy.ADMIN_TOPICS_TITLE)).to_be_visible(timeout=15_000)
        for doc_type in doc_types:
            expect(self.topic_chip(doc_type)).to_be_visible()

    def expect_no_topics_card(self):
        expect(self.page.get_by_text(Copy.ADMIN_TOPICS_TITLE)).to_have_count(0)
