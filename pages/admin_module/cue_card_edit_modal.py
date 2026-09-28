from playwright.sync_api import expect

from constants import StarSellerCopy as Ssc
from locators.admin import star_seller_locators as L
from pages.admin_module.additional_details_modal import StarRequirementsPanel
from pages.shared.base_page import BasePage


class CueCardEditModal(BasePage):
    """"Cue card edit" (EditCuecardModal): the star requirements panel sits at the top (index.js:315)."""

    def wait_open(self):
        expect(self.root).to_be_visible(timeout=15_000)
        return self

    @property
    def root(self):
        return self.page.locator(L.MODAL).filter(has_text=Ssc.CUE_CARD_EDIT_TITLE)

    @property
    def panel(self):
        return StarRequirementsPanel(self.root)
