import re

from playwright.sync_api import expect

from constants import StarSellerCopy as Ssc
from locators.admin import star_seller_locators as L
from pages.shared.base_page import BasePage

MISSING_RE = re.compile(Ssc.MISSING, re.I)
# PUT company/update/admin saves both the additional details and the objective (endpoint.js:58).
SAVE_API = "company/update/admin"


def is_admin_save(response):
    return SAVE_API in response.url and response.request.method == "PUT"


def names_missing(text, item):
    """True when the block message names `item` as missing: "<item> is missing", case and order ignored."""
    return bool(re.search(re.escape(item), text or "", re.I)) and bool(MISSING_RE.search(text or ""))


class StarRequirementsPanel:
    """The "Star seller requirements" panel (StarSellerRequirementsPanel), inside any modal."""

    def __init__(self, scope):
        self.root = scope.get_by_text(Ssc.REQUIREMENTS_PANEL, exact=True).locator("xpath=..")

    def text(self):
        expect(self.root).to_be_visible(timeout=15_000)
        return " ".join(self.root.inner_text().split())

    def row_description(self, title):
        """The grey line under a row title, e.g. "A verified document" -> "Pitch deck"."""
        label = self.root.get_by_text(title, exact=True)
        expect(label).to_be_visible(timeout=10_000)
        return label.locator("xpath=following-sibling::div[1]").inner_text().strip()

    def highlights_count(self):
        match = re.search(Ssc.HIGHLIGHTS_COUNT_RE, self.text())
        return int(match.group(1)) if match else None


class AdditionalDetailsModal(BasePage):
    """"Additional Details for this Seller" (AdditionalFieldsModal, cue card > Additional details > Edit).

    Clicking "Yes" under Star runs the star check first; when it fails the Yes chip is not selected
    and a block message is shown (today a snackbar naming the first missing item; after
    star-seller-fundraising one message listing "<item> is missing"). Confirm runs the check again.
    """

    def wait_open(self):
        expect(self.root).to_be_visible(timeout=15_000)
        expect(self.panel.root).to_be_visible(timeout=15_000)
        self.page.wait_for_load_state("networkidle")   # the completed-call lookup feeds the check
        return self

    @property
    def root(self):
        return self.page.locator(L.MODAL).filter(has_text=Ssc.ADDITIONAL_DETAILS_TITLE)

    @property
    def panel(self):
        return StarRequirementsPanel(self.root)

    def category(self, title):
        heading = self.root.locator(L.CATEGORY_TITLE).filter(has_text=re.compile(rf"^\s*{re.escape(title)}\b"))
        return heading.first.locator("xpath=..")

    def chip(self, category, label):
        return self.category(category).locator(L.CHIP).filter(has_text=re.compile(rf"^\s*{re.escape(label)}\s*$"))

    @staticmethod
    def is_selected(chip):
        return chip.evaluate("el => getComputedStyle(el).backgroundColor") == L.SELECTED_CHIP_BG

    def star_chip(self, label):
        return self.chip(Ssc.STAR, label)

    def click_star(self, label):
        self.star_chip(label).click()
        self.page.wait_for_timeout(500)   # the check and the snackbar are synchronous; let it paint
        return self

    def star_selected(self, label):
        return self.is_selected(self.star_chip(label))

    def growth_chips(self):
        chips = self.category(Ssc.GROWTH).locator(L.CHIP)
        return [chips.nth(i) for i in range(chips.count())]

    @property
    def block_message(self):
        """The star block message: a snackbar/alert or text inside the modal that says "missing"."""
        toast = self.page.locator(L.SNACKBAR).filter(has_text=MISSING_RE)
        inline = self.root.get_by_text(MISSING_RE)
        return toast.or_(inline)

    def expect_block_message(self):
        message = self.block_message.last
        expect(message).to_be_visible(timeout=10_000)
        return " ".join(message.inner_text().split())

    def expect_no_block_message(self):
        self.page.wait_for_timeout(1_500)
        expect(self.block_message).to_have_count(0)

    def confirm(self, expect_save=True):
        """Click Confirm. With expect_save the PUT must go out and the page reloads."""
        button = self.root.get_by_role("button", name=Ssc.CONFIRM, exact=True)
        if not expect_save:
            button.click()
            self.page.wait_for_timeout(1_500)
            return self
        with self.page.expect_response(is_admin_save, timeout=30_000):
            button.click()
        self.page.wait_for_load_state("networkidle")
        return self

    def cancel(self):
        self.root.get_by_role("button", name=Ssc.CANCEL, exact=True).click()
        expect(self.root).to_have_count(0)

    def back_to_cue_card(self):
        self.root.get_by_role("button", name=Ssc.BACK_TO_CUE_CARD).click()
        return self
