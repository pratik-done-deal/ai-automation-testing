import re

from playwright.sync_api import Page, expect

from config import settings


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def open(self, path: str):
        self.page.goto(settings.app_url + path.lstrip("/"))
        self.page.wait_for_load_state("networkidle")

    def snackbar(self):
        # MUI snackbar rendered by the app's global updateSnackbar slice.
        return self.page.locator(".MuiSnackbar-root, .MuiAlert-root, [role='alert']").first

    def expect_snackbar(self, text):
        expect(self.snackbar()).to_contain_text(re.compile(text, re.I), timeout=15_000)

    @staticmethod
    def is_visually_disabled(locator) -> bool:
        """The app often disables CTAs with `opacity-40 pointer-events-none` instead of `disabled`."""
        if locator.is_disabled():
            return True
        cls = locator.get_attribute("class") or ""
        return "pointer-events-none" in cls or "Mui-disabled" in cls
