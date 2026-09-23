"""/buyer/login - the two-step email -> 6-digit passcode sign-in (module buyer-login)."""
import json
import re

from playwright.sync_api import expect

from config import settings
from constants import PERSISTED_STATE_KEY, TOKEN_KEY, BuyerLoginCopy
from locators.buyer.login_locators import (
    BLUR_WRAPPER, CODE_SENT_SENTENCE, EDIT_EMAIL_ICON, EMAIL_INPUT, EMAIL_STEP, FIELD_IN_ERROR, FIELD_LABEL,
    HELPER_TEXT, OTP_INPUT, RESEND_LINK, SIGNUP_LINK, SUBMIT_BUTTON,
)
from pages.shared.base_page import BasePage
from utils.sessions import track_listener

LOGIN_URL = re.compile(r"/buyer/login")


class BuyerLoginPage(BasePage):
    """Both steps live at the same URL: step 1 -> step 2 is a re-render, so the location never
    changes between them and every step assertion is made on copy.

    There is no screen-load API request: step 1 is pure client state and the first call is the
    passcode request the buyer triggers, so waiting for a response on open would hang.
    """

    # ------------------------------------------------------------------ opening

    def open_login(self, query=""):
        self.open_login_at(query)
        expect(self.email_input).to_be_visible(timeout=30_000)
        return self

    def open_login_at(self, query=""):
        """Open /buyer/login without assuming which step renders: the link-prefill and the
        stored-passcode paths open step 2 on mount, so step 1 may never be on screen."""
        self.open("buyer/login" + query)
        return self

    def open_after_bounce(self, path):
        """Open a protected buyer route while logged out: the app bounces to /buyer/login and records
        `path` as commonStore.previousPath, which is what the post-login redirect reads."""
        self.page.goto(settings.app_url + path.lstrip("/"))
        expect(self.email_input).to_be_visible(timeout=30_000)
        expect(self.page).to_have_url(LOGIN_URL)
        return self

    # ------------------------------------------------------------------ elements

    @property
    def email_step(self):
        return self.page.locator(EMAIL_STEP)

    @property
    def email_input(self):
        return self.page.locator(EMAIL_INPUT)

    @property
    def otp_input(self):
        return self.page.locator(OTP_INPUT)

    @property
    def field_label(self):
        return self.page.locator(FIELD_LABEL)

    @property
    def helper_text(self):
        return self.page.locator(HELPER_TEXT)

    @property
    def field_in_error(self):
        return self.page.locator(FIELD_IN_ERROR)

    @property
    def submit_button(self):
        return self.page.locator(SUBMIT_BUTTON)

    @property
    def signup_link(self):
        return self.page.locator(SIGNUP_LINK)

    @property
    def code_step_heading(self):
        return self.page.get_by_text(BuyerLoginCopy.OTP_HEADING, exact=True)

    @property
    def code_sent_sentence(self):
        # Ancestors match the text too; the last match in DOM order is the sentence itself.
        return self.page.locator(CODE_SENT_SENTENCE).last

    @property
    def edit_email_icon(self):
        return self.code_sent_sentence.locator(EDIT_EMAIL_ICON)

    @property
    def resend_link(self):
        return self.page.locator(RESEND_LINK).filter(has_text=BuyerLoginCopy.RESEND_LINK)

    # ------------------------------------------------------------------ actions

    def submit(self):
        """The one submit button both steps share (label "Verify" / "Verify & Login")."""
        self.submit_button.click()

    def submit_email(self, email):
        self.email_input.fill(email)
        self.submit()
        return self

    def submit_code(self, code):
        self.otp_input.fill(code)
        self.submit()
        return self

    def expect_email_step(self):
        expect(self.email_step).to_be_visible()
        expect(self.submit_button).to_have_text(BuyerLoginCopy.VERIFY_CTA)
        return self

    def expect_code_step(self):
        expect(self.code_step_heading).to_be_visible(timeout=20_000)
        expect(self.submit_button).to_have_text(BuyerLoginCopy.OTP_CTA)
        return self

    def sentence_text(self):
        """The step-2 sentence with its whitespace collapsed, so the email reads as one word."""
        return " ".join((self.code_sent_sentence.text_content() or "").split())

    def helper_message(self):
        # Two chained requests stand between some submits and their helper text.
        expect(self.helper_text).to_be_visible(timeout=15_000)
        return (self.helper_text.text_content() or "").strip()

    def label_asterisk_colour(self):
        """The `*` after the field label is its own span; Tailwind carries the colour in the class."""
        return self.field_label.locator("span").get_attribute("class") or ""

    # ------------------------------------------------------------------ what the page recorded

    def watch_api_calls(self):
        """Live list of API paths this page requests from now on, e.g. "user", "buyer/status".

        Registered before the click that should (or should not) call the backend; there is no
        screen-load request to wait for, so tests read it after a short settle.
        """
        seen = []

        def record(request):
            if request.url.startswith(settings.api_url):
                seen.append(request.url[len(settings.api_url):])

        track_listener(self.page, "request", record)   # removed when the shared page is reset
        return seen

    def local_storage(self, *keys):
        """{key: value or None} straight out of the page's localStorage."""
        return self.page.evaluate("keys => Object.fromEntries(keys.map(k => [k, localStorage.getItem(k)]))",
                                  list(keys))

    def set_local_storage(self, values):
        self.page.evaluate("values => Object.entries(values).forEach(([k, v]) => localStorage.setItem(k, v))",
                           values)

    def persisted_state(self):
        """The persisted Redux state (localStorage "state"): authorizationStore, commonStore,
        buyerVerificationStore, written by store.subscribe on every dispatch."""
        raw = self.page.evaluate("key => localStorage.getItem(key)", PERSISTED_STATE_KEY)
        return json.loads(raw) if raw else {}

    def login_response(self):
        return (self.persisted_state().get("authorizationStore") or {}).get("loginResponse") or {}

    # ------------------------------------------------------------------ seeded browser state

    def patch_persisted_state(self, patch, storage=None):
        """Merge `patch` (slice -> fields) into the persisted state, optionally write `storage`
        localStorage keys, and reload so the store boots from it.

        The app is loaded first, so the patch lands on the real state shape instead of replacing it.
        """
        self.page.evaluate(
            """([key, patch]) => {
                const state = JSON.parse(localStorage.getItem(key) || '{}');
                for (const [slice, values] of Object.entries(patch)) {
                    state[slice] = Object.assign({}, state[slice], values);
                }
                localStorage.setItem(key, JSON.stringify(state));
            }""",
            [PERSISTED_STATE_KEY, patch],
        )
        if storage:
            self.set_local_storage(storage)
        self.page.reload()
        return self

    def set_previous_path(self, path):
        """Set the in-app previous location the post-login redirect reads (commonStore.previousPath).

        A directly opened /buyer/login has none, and HomeLayoutContainer never records a path
        containing /login, so this stands in for having navigated there from inside the app.
        """
        return self.patch_persisted_state({"commonStore": {"previousPath": path}})

    def seed_live_session(self, verification, user_type=3, token="automation-seeded-session"):
        """Make this context look signed in: localStorage authToken plus the persisted
        loginResponse and buyerVerificationState that isAuthenticated() / reRouteUser read.

        Nothing is sent to the backend, no passcode and no device session, and auth/<role>.json is
        untouched - the only way to reach the already-authenticated redirect without a real login.
        """
        return self.patch_persisted_state(
            {"authorizationStore": {"loginResponse": {"userType": user_type, "isBuyer": user_type == 3,
                                                      "sessionId": token, "email": "seeded@example.com"}},
             "buyerVerificationStore": {"buyerVerificationState": verification}},
            storage={TOKEN_KEY: token},
        )

    # ------------------------------------------------------------------ production-only guards

    def blur_filter(self):
        """The CSS filter on the buyer shell: "none" unless useBlurOnFocusLoss has tripped."""
        return self.page.evaluate(
            """selector => {
                const el = document.querySelector(selector);
                return el ? getComputedStyle(el).filter : null;
            }""",
            BLUR_WRAPPER,
        )
