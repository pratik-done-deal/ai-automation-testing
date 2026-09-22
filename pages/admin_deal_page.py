import re

from playwright.sync_api import expect

from constants import CAP_TABLE, DOC_LABELS, PRD_CAP_TABLE_LABEL, Copy
from pages.base_page import BasePage
from pages.buyer_cue_card_page import BuyerCueCardPage


def topic_label_pattern(doc_type):
    # The card isn't built (DR-46). Figma/PRD say "Cap Table and Board Profile", the app map "Cap Table" (G8).
    labels = [DOC_LABELS[doc_type]] + ([PRD_CAP_TABLE_LABEL] if doc_type == CAP_TABLE else [])
    return re.compile(rf"^\s*({'|'.join(re.escape(label) for label in labels)})\s*$")


class AdminDealPage(BasePage):
    """Admin / biz deal page: /admin/deal-notes/:dealId (DealNotesContainer), tabs from dealNotesTabModel.js."""

    def open_deal(self, deal_id):
        self.open(f"admin/deal-notes/{deal_id}")
        return self

    def open_data_room_tab(self):
        """Switch to Data Room and wait until DealDataRoom has rendered its document/query result."""
        tab = self.page.get_by_role("tab", name=Copy.ADMIN_DATA_ROOM_TAB).or_(
            self.page.get_by_text(Copy.ADMIN_DATA_ROOM_TAB, exact=True)
        ).first
        with self.page.expect_response(lambda r: "document/query" in r.url, timeout=30_000):
            tab.click()
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def topics_card(self):
        return self.page.locator("div").filter(has_text=Copy.ADMIN_TOPICS_TITLE).last

    def topic_chip(self, doc_type):
        return self.topics_card.get_by_text(topic_label_pattern(doc_type))

    def expect_topics(self, doc_types):
        expect(self.page.get_by_text(Copy.ADMIN_TOPICS_TITLE)).to_be_visible(timeout=15_000)
        for doc_type in doc_types:
            expect(self.topic_chip(doc_type).first).to_be_visible()

    def expect_no_topics_card(self):
        expect(self.page.get_by_text(Copy.ADMIN_TOPICS_TITLE)).to_have_count(0)


class AdminCueCardPage(BuyerCueCardPage):
    """Admin / biz view of a company cue card: /admin/cue-card/:uid (same CuecardContainer as the buyer)."""

    def open_admin_cue_card(self, uid: str):
        with self.page.expect_response(lambda r: self.CUE_CARD_API.search(r.url) and r.ok, timeout=30_000) as res:
            self.open(f"admin/cue-card/{uid}")
        self.cue_card_payload = res.value.json()
        return self
