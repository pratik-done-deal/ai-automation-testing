"""Buyer login, /buyer/login (BUY-LGN-01 ... BUY-LGN-56).

Spec: specs/modules/buyer-login/module.md. Every test runs in a FRESH logged-out context
(`logged_out_page`): the saved sessions in auth/ are never read and never written.

How the cost is kept at zero (module.md "Data cost and sequencing"):
  * step 1 and its validation need no backend at all - the screen makes no data request;
  * the passcode payload, step 2, the whole error matrix, the session writes and every post-login
    redirect are reached by answering `user/send/passcode`, `user`, `user/emailCheck`, `buyer/status`
    and `buyer/linkInfo` locally, so no passcode is ever sent, no device session is created and no
    wrong passcode is offered to the backend (a lockout policy is unverified - open question 2);
  * exactly one test (`test_live_buyer_login_lands_on_a_buyer_screen`, marker `live_login`) completes
    a real login: one real passcode goes out and the account gets a device session, which can evict
    a saved auth/buyer.json. Re-run `python scripts/save_auth_state.py buyer` after it.

Deliberately not asserted, because the behaviour is a suspected bug and a test would lock it in
(module.md "Suspected bugs and oddities"): the copy shown for an EMPTY passcode (bug 1), whether the
passcode error clears while retyping (bug 2), the double callback on a transport failure (bug 3), and
the discarded `renderSections()` (bug 8).

BUY-LGN-55 (the "claude" element detector) is deliberately NOT automated: the probe it needs would
clear this context's storage and hard-navigate, and the suite must never inject such markup on a
/buyer/* page. It stays a manual check.
"""
import re
import time
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

from config import settings
from constants import (
    BUYER_ID_KEY, BUYER_LANDING_DESKTOP, BUYER_LANDING_MOBILE, BUYER_ONBOARDING_PATH, BUYER_PROFILE_PATH,
    SAVE_LOGIN_MODAL_SHOWN_KEY, SAVED_PROFILE_KEY, SELLER_UID_KEY, SESSION_ID_KEY, TOKEN_KEY, BuyerLoginCopy,
)
from pages.buyer_module.buyer_login_page import LOGIN_URL, BuyerLoginPage
from utils.network import (
    api_route, buyer_status_body, email_check_body, failure_body, login_success, mock_json, mock_json_sequence,
    passcode_not_registered, passcode_success, success_body,
)

# No account needed: every request that would leave the browser is answered locally.
EMAIL = "abhijeet@gullu.com"
CODE = "12345"
SESSION = "automation-session-id"
BUYER_UID = "automation-buyer-uid"
LISTING_UID = "1a2b3c4d-0000-4000-8000-000000000001"
SHARED_CARD_PATH = "/buyer/sharedcard/automation-shared-uid"
BOUNCED_PATH = "/buyer/categories/automation-category-uid"   # ProtectedRoute, and on the post-login allow-list

# page.route predicates: `**/user` would otherwise read as a prefix of `**/user/send/passcode`.
PASSCODE_API = api_route("user/send/passcode")
LOGIN_API = api_route("user")
EMAIL_CHECK_API = api_route("user/emailCheck")
STATUS_API = api_route("buyer/status")
LINK_INFO_API = api_route("buyer/linkInfo")
# expect_request / expect_response match on the URL, so those take patterns instead.
PASSCODE_URL = re.compile(r"/user/send/passcode")
LOGIN_API_URL = re.compile(r"/user$")
EMAIL_CHECK_URL = re.compile(r"/user/emailCheck")


def expected_sentence(email, mobile=None):
    """The step-2 sentence with whitespace collapsed: "…code to <email> [and <mobile>] . Enter it…"."""
    parts = [BuyerLoginCopy.OTP_SENT_PREFIX, email] + (["and", mobile] if mobile else [])
    return " ".join(parts) + " " + BuyerLoginCopy.OTP_SENT_SUFFIX


def open_code_step(page, mobile=None, email=EMAIL, passcodes=None):
    """A logged-out page on step 2, with `user/send/passcode` answered locally.

    Returns (page object, the payloads it captured), so a test can also assert what was sent.
    """
    login = BuyerLoginPage(page).open_login()
    sent = []
    mock_json_sequence(page, PASSCODE_API, passcodes or [passcode_success(mobile)], sent=sent)
    login.submit_email(email)
    login.expect_code_step()
    return login, sent


def mocked_login(login, buyer_status="verified", onboarding_stage=2, email=EMAIL):
    """Both steps, with the passcode, the login and the status gate all answered locally.

    Nothing reaches the backend: no passcode is sent, the account gets no device session, and the
    authToken this leaves behind belongs to the throwaway context only.
    """
    page = login.page
    mock_json(page, PASSCODE_API, passcode_success())
    mock_json(page, LOGIN_API, login_success(email, session_id=SESSION, uid=BUYER_UID))
    mock_json(page, STATUS_API, buyer_status_body(buyer_status, onboarding_stage))
    login.submit_email(email)
    login.expect_code_step()
    login.submit_code(CODE)
    return login


# ------------------------------------------------------------------ step 1: no API call at all

@pytest.mark.smoke
def test_login_screen_renders_step_one(logged_out_page):
    """BUY-LGN-01, BUY-LGN-02, BUY-LGN-04: /buyer/login opens the email step, titled "Login - Done Deal"."""
    BuyerLoginPage(logged_out_page).open_login()
    expect(logged_out_page).to_have_url(LOGIN_URL)
    expect(logged_out_page).to_have_title(BuyerLoginCopy.PAGE_TITLE)
    expect(logged_out_page.get_by_text(BuyerLoginCopy.EMAIL_HEADING, exact=True)).to_be_visible()
    expect(logged_out_page.get_by_text(BuyerLoginCopy.EMAIL_SUBTITLE)).to_be_visible()
    expect(logged_out_page.get_by_text(BuyerLoginCopy.EMAIL_HINT, exact=True)).to_be_visible()


def test_step_one_labels_the_field_and_the_cta(logged_out_page):
    """BUY-LGN-03, BUY-LGN-05: "Official Email ID*", the work-email placeholder, and a "Verify" CTA."""
    login = BuyerLoginPage(logged_out_page).open_login()
    expect(login.field_label).to_have_text(BuyerLoginCopy.EMAIL_LABEL + "*")
    assert "B42318" in login.label_asterisk_colour()          # the asterisk is red
    expect(login.email_input).to_be_visible()                 # located by its placeholder
    expect(login.submit_button).to_have_text(BuyerLoginCopy.VERIFY_CTA)


def test_signup_link_points_at_buyer_onboarding(logged_out_page):
    """BUY-LGN-06: "Don't have an account? Sign up here" links to /buyer/onboarding."""
    login = BuyerLoginPage(logged_out_page).open_login()
    expect(logged_out_page.get_by_text(BuyerLoginCopy.SIGNUP_PROMPT)).to_be_visible()
    expect(login.signup_link).to_have_text(BuyerLoginCopy.SIGNUP_LINK)


def test_empty_email_shows_the_helper_and_sends_nothing(logged_out_page):
    """BUY-LGN-07, BUY-LGN-08: the helper appears under the field and no API request is made."""
    login = BuyerLoginPage(logged_out_page).open_login()
    calls = login.watch_api_calls()

    login.submit()

    assert login.helper_message() == BuyerLoginCopy.INCORRECT_EMAIL_HELPER
    expect(login.field_in_error).to_have_count(1)
    logged_out_page.wait_for_timeout(1_500)
    assert calls == []


@pytest.mark.parametrize("value", ["not-an-email", "buyer@example", "buyer@example.com."],
                         ids=["no-at", "no-dot-suffix", "trailing-dot"])
def test_malformed_email_stays_on_step_one_without_a_request(logged_out_page, value):
    """BUY-LGN-09, BUY-LGN-10: emailIsValid rejects it client-side, so nothing is sent."""
    login = BuyerLoginPage(logged_out_page).open_login()
    calls = login.watch_api_calls()

    login.submit_email(value)

    assert login.helper_message() == BuyerLoginCopy.INCORRECT_EMAIL_HELPER
    expect(logged_out_page).to_have_url(LOGIN_URL)
    login.expect_email_step()
    logged_out_page.wait_for_timeout(1_500)
    assert calls == []


def test_typing_clears_the_email_error(logged_out_page):
    """BUY-LGN-11: one character in the email field drops the error state and the helper text."""
    login = BuyerLoginPage(logged_out_page).open_login()
    login.submit()
    assert login.helper_message() == BuyerLoginCopy.INCORRECT_EMAIL_HELPER

    login.email_input.fill("d")

    expect(login.helper_text).to_have_count(0)
    expect(login.field_in_error).to_have_count(0)


def test_plain_login_makes_no_link_info_call(logged_out_page):
    """BUY-LGN-52: without listingUid / pocUid there is no buyer/linkInfo request (nor any other)."""
    login = BuyerLoginPage(logged_out_page)
    calls = login.watch_api_calls()          # registered before the first navigation: mount is covered

    login.open_login()

    logged_out_page.wait_for_timeout(2_000)
    assert [call for call in calls if "linkInfo" in call] == []
    # module.md, code facts: the screen has no data request of its own either.
    assert calls == [], f"/buyer/login is expected to load without any API call, but made: {calls}"


def test_qa_has_no_viewport_guard_and_no_blur(logged_out_page):
    """BUY-LGN-56: both guards are gated on production, so resizing and losing focus do nothing."""
    login = BuyerLoginPage(logged_out_page).open_login()

    logged_out_page.set_viewport_size({"width": 900, "height": 700})
    logged_out_page.evaluate("() => window.dispatchEvent(new Event('blur'))")

    expect(logged_out_page.get_by_text(BuyerLoginCopy.VIEWPORT_GUARD)).to_have_count(0)
    expect(login.email_input).to_be_visible()
    assert login.blur_filter() == "none"


# ------------------------------------------------------------------ the passcode request payload

def test_passcode_request_carries_the_email_and_buyer_user_type(logged_out_page):
    """BUY-LGN-12, BUY-LGN-13: one POST user/send/passcode with {email, userType: 3} and no resend key.

    The response is answered locally, so the payload is checked without a passcode going out.
    """
    login = BuyerLoginPage(logged_out_page).open_login()
    sent = []
    mock_json(logged_out_page, PASSCODE_API, passcode_success(), sent=sent)

    login.submit_email(EMAIL)

    login.expect_code_step()
    assert sent == [{"email": EMAIL, "userType": 3}]


def test_passcode_request_trims_the_email(logged_out_page):
    """BUY-LGN-14: surrounding whitespace is stripped from the email in the payload."""
    login = BuyerLoginPage(logged_out_page).open_login()
    sent = []
    mock_json(logged_out_page, PASSCODE_API, passcode_success(), sent=sent)

    login.submit_email(f"  {EMAIL}  ")

    login.expect_code_step()
    assert sent == [{"email": EMAIL, "userType": 3}]


# ------------------------------------------------------------------ the unregistered-email branch

def test_unregistered_email_is_refused_and_then_email_checked(logged_out_page):
    """BUY-LGN-15: the one contract check against the real backend - an address that is not
    registered answers HTTP 400 with data.code "not_registered", and the app follows it with
    GET user/emailCheck?email=…&primaryIdType=buyer.

    No passcode can be sent for an unknown address, so this costs nothing. DD_BUYER_LOGIN_UNREGISTERED_EMAIL
    pins the address; without it one is generated per run, which keeps the case from depending on
    data staying absent.
    """
    email = settings.buyer_login_unregistered_email or f"dd.automation.unknown{int(time.time())}@example.com"
    login = BuyerLoginPage(logged_out_page).open_login()

    with logged_out_page.expect_response(PASSCODE_URL) as passcode:
        with logged_out_page.expect_request(EMAIL_CHECK_URL) as email_check:
            login.submit_email(email)

    assert passcode.value.status == 400
    assert passcode.value.json()["data"]["code"] == "not_registered"
    query = parse_qs(urlsplit(email_check.value.url).query)
    assert query["email"] == [email]
    assert query["primaryIdType"] == ["buyer"]


def test_email_check_false_asks_for_a_professional_email(logged_out_page):
    """BUY-LGN-16: emailCheck data false keeps the buyer on /buyer/login with the register-with-a-
    professional-email helper."""
    login = BuyerLoginPage(logged_out_page).open_login()
    mock_json(logged_out_page, PASSCODE_API, passcode_not_registered())
    mock_json(logged_out_page, EMAIL_CHECK_API, email_check_body(False))

    login.submit_email(EMAIL)

    assert login.helper_message() == BuyerLoginCopy.NOT_PROFESSIONAL_EMAIL
    expect(logged_out_page).to_have_url(LOGIN_URL)
    login.expect_email_step()


def test_email_check_true_goes_to_onboarding_with_the_query(logged_out_page):
    """BUY-LGN-17: emailCheck data true hands the buyer to /buyer/onboarding, query string kept."""
    login = BuyerLoginPage(logged_out_page).open_login("?utm_source=automation")
    mock_json(logged_out_page, PASSCODE_API, passcode_not_registered())
    mock_json(logged_out_page, EMAIL_CHECK_API, email_check_body(True))

    login.submit_email(EMAIL)

    expect(logged_out_page).to_have_url(
        re.compile(re.escape(BUYER_ONBOARDING_PATH) + r"\?utm_source=automation"))


def test_failing_email_check_shows_something_went_bad(logged_out_page):
    """BUY-LGN-18: an emailCheck body whose status is not "200" shows "Something went bad!!"."""
    login = BuyerLoginPage(logged_out_page).open_login()
    mock_json(logged_out_page, PASSCODE_API, passcode_not_registered())
    mock_json(logged_out_page, EMAIL_CHECK_API, failure_body(status="500", message="Internal Server Error"))

    login.submit_email(EMAIL)

    assert login.helper_message() == BuyerLoginCopy.SOMETHING_WENT_BAD


def test_other_passcode_failures_show_the_backend_message(logged_out_page):
    """BUY-LGN-19: a failure code other than not_registered shows the backend message on step 1."""
    login = BuyerLoginPage(logged_out_page).open_login()
    mock_json(logged_out_page, PASSCODE_API,
              failure_body({"code": "blocked", "message": "Account locked"}))

    login.submit_email(EMAIL)

    assert login.helper_message() == "Account locked"
    login.expect_email_step()


# ------------------------------------------------------------------ step 2: Check Your Device

@pytest.mark.smoke
def test_passcode_success_opens_the_code_step(logged_out_page):
    """BUY-LGN-20, BUY-LGN-21, BUY-LGN-23, BUY-LGN-24, BUY-LGN-25: "Check Your Device", the sentence
    naming only the email (the response carries mobile: null), the field and the "Verify & Login" CTA."""
    login, _ = open_code_step(logged_out_page)

    expect(logged_out_page).to_have_url(LOGIN_URL)          # the step switch never changes the URL
    assert login.sentence_text() == expected_sentence(EMAIL)
    expect(login.field_label).to_have_text(BuyerLoginCopy.OTP_LABEL + "*")
    expect(login.otp_input).to_be_visible()                 # located by its placeholder
    expect(login.submit_button).to_have_text(BuyerLoginCopy.OTP_CTA)


def test_code_step_names_the_mobile_when_the_response_carries_one(logged_out_page):
    """BUY-LGN-22: a passcode response with a mobile makes step 2 name the email and that number."""
    login, _ = open_code_step(logged_out_page, mobile="9876543210")

    assert login.sentence_text() == expected_sentence(EMAIL, mobile="9876543210")


def test_empty_code_blocks_the_login_request(logged_out_page):
    """BUY-LGN-26: submitting step 2 empty puts the field in the error state and sends no POST user.

    The helper's wording for this case is a suspected bug (it claims the code was incorrect), so only
    the error state and the absent request are asserted.
    """
    login, _ = open_code_step(logged_out_page)
    sent = []
    mock_json(logged_out_page, LOGIN_API, login_success(EMAIL), sent=sent)

    login.submit()

    expect(login.field_in_error).to_have_count(1)
    expect(login.helper_text).to_be_visible()
    logged_out_page.wait_for_timeout(1_500)
    assert sent == []
    login.expect_code_step()


def test_code_submit_posts_the_login_payload(logged_out_page):
    """BUY-LGN-27: POST user carries {email, passcode, device}. Answered locally, so no session is created."""
    login, _ = open_code_step(logged_out_page)
    sent = []
    mock_json(logged_out_page, LOGIN_API, failure_body({"message": "Automation: rewritten response"}), sent=sent)

    login.submit_code(CODE)

    expect(login.helper_text).to_be_visible(timeout=15_000)      # the app has handled the answer
    assert len(sent) == 1
    assert set(sent[0]) == {"email", "passcode", "device"}
    assert sent[0]["email"] == EMAIL
    assert sent[0]["passcode"] == CODE
    assert isinstance(sent[0]["device"], str) and sent[0]["device"]


def test_rejected_code_keeps_the_code_step_and_shows_the_message(logged_out_page):
    """BUY-LGN-28: the backend message appears under the code field and the buyer stays on step 2.

    The failure is a rewritten `POST user` response, never a real wrong passcode: any lockout or
    throttle on the backend is unverified (module.md open question 2).
    """
    message = "Automation: the passcode you entered is not valid"
    login, _ = open_code_step(logged_out_page)
    mock_json(logged_out_page, LOGIN_API, failure_body({"message": message}))

    login.submit_code("000000")

    assert login.helper_message() == message
    login.expect_code_step()
    assert login.local_storage(TOKEN_KEY)[TOKEN_KEY] is None


def test_edit_email_returns_to_step_one_keeping_the_email(logged_out_page):
    """BUY-LGN-29: the pencil beside the email reopens step 1 with the email, and the code is cleared."""
    login, _ = open_code_step(logged_out_page)
    login.otp_input.fill(CODE)

    login.edit_email_icon.click()

    login.expect_email_step()
    expect(login.email_input).to_have_value(EMAIL)
    expect(login.helper_text).to_have_count(0)

    login.submit()                       # the same email opens step 2 again
    login.expect_code_step()
    expect(login.otp_input).to_have_value("")


def test_resend_posts_again_with_resend_true(logged_out_page):
    """BUY-LGN-30, BUY-LGN-31: "Click here" re-posts the passcode with resend: true and snackbars
    "Passcode Sent"."""
    login, sent = open_code_step(logged_out_page)

    login.resend_link.click()

    login.expect_snackbar(BuyerLoginCopy.PASSCODE_SENT)
    assert sent == [{"email": EMAIL, "userType": 3},
                    {"email": EMAIL, "userType": 3, "resend": True}]


def test_failed_resend_shows_try_again_later(logged_out_page):
    """BUY-LGN-32: a resend the backend refuses snackbars "Please try again later"."""
    login, sent = open_code_step(logged_out_page,
                                 passcodes=[passcode_success(), failure_body(message="Failure")])

    login.resend_link.click()

    login.expect_snackbar(BuyerLoginCopy.RESEND_FAILED)
    assert len(sent) == 2


def test_successful_resend_after_a_rejected_code_clears_the_field(logged_out_page):
    """BUY-LGN-33: once a code has been rejected, a successful resend empties the code field."""
    login, _ = open_code_step(logged_out_page, passcodes=[passcode_success(), passcode_success()])
    mock_json(logged_out_page, LOGIN_API, failure_body({"message": "Automation: rejected"}))
    login.submit_code("000000")
    assert login.helper_message() == "Automation: rejected"

    login.resend_link.click()

    login.expect_snackbar(BuyerLoginCopy.PASSCODE_SENT)
    expect(login.otp_input).to_have_value("")


def test_a_requested_passcode_reopens_the_code_step(logged_out_page):
    """BUY-LGN-49: coming back to /buyer/login after a passcode was requested in this session prefills
    the email, re-sends a passcode on mount and opens step 2 with no click.

    The stored state (authorizationStore.passcodeSuccessData) is memory-only - store.subscribe blanks
    it before persisting - so leaving and returning has to happen inside the running app. pushState
    plus popstate is how react-router sees an in-app navigation; nothing is injected into the DOM.
    """
    login, sent = open_code_step(logged_out_page)

    logged_out_page.evaluate(
        f"""() => {{
            history.pushState({{}}, '', '{BUYER_ONBOARDING_PATH}');
            window.dispatchEvent(new PopStateEvent('popstate'));
        }}""")
    expect(logged_out_page).to_have_url(re.compile(re.escape(BUYER_ONBOARDING_PATH)))
    logged_out_page.evaluate("() => history.back()")

    expect(logged_out_page).to_have_url(LOGIN_URL)
    login.expect_code_step()
    # The signup screen auto-sends from the same stored state, so only the last call is this mount's.
    assert len(sent) > 1
    assert sent[-1] == {"email": EMAIL, "userType": 3, "resend": False}


def test_sign_up_here_clears_the_stored_passcode_state(logged_out_page):
    """BUY-LGN-50: "Sign up here" drops that stored state, so the next /buyer/login starts at step 1."""
    login, sent = open_code_step(logged_out_page)
    login.edit_email_icon.click()        # "Sign up here" only renders on step 1
    login.expect_email_step()

    login.signup_link.click()
    expect(logged_out_page).to_have_url(re.compile(re.escape(BUYER_ONBOARDING_PATH)))
    logged_out_page.evaluate("() => history.back()")

    expect(logged_out_page).to_have_url(LOGIN_URL)
    login.expect_email_step()
    expect(login.code_step_heading).to_have_count(0)
    assert len(sent) == 1                # no passcode was re-sent on mount


def test_listing_uid_prefills_the_email_and_opens_the_code_step(logged_out_page):
    """BUY-LGN-51: /buyer/login?listingUid=<uuid> posts buyer/linkInfo and opens step 2 on the
    returned email. linkInfo is answered locally, so no real listing uid is needed."""
    login = BuyerLoginPage(logged_out_page)
    link_calls, passcodes = [], []
    mock_json(logged_out_page, LINK_INFO_API, success_body({"email": EMAIL}), sent=link_calls)
    mock_json(logged_out_page, PASSCODE_API, passcode_success(), sent=passcodes)

    login.open_login_at(f"?listingUid={LISTING_UID}")

    login.expect_code_step()
    assert link_calls == [{"listingUid": LISTING_UID}]
    assert passcodes == [{"email": EMAIL, "userType": 3}]
    assert login.sentence_text() == expected_sentence(EMAIL)


# ------------------------------------------------------------------ what a login writes, and where it lands
# `user` and `buyer/status` are answered locally: the account gets no device session, and both
# branches of the verified / not-verified split can be checked without knowing which kind of buyer
# DD_BUYER_LOGIN_EMAIL is (module.md open question 1).

def test_successful_login_writes_the_session(logged_out_page):
    """BUY-LGN-34, BUY-LGN-35, BUY-LGN-36, BUY-LGN-37, BUY-LGN-38: authToken, buyerId, the keys a
    login clears, and the login response in Redux."""
    login = BuyerLoginPage(logged_out_page).open_login()
    # The keys a real pre-login screen would be carrying, so "removes them" is a real assertion.
    login.set_local_storage({SESSION_ID_KEY: "automation-pre-login-session",
                             SELLER_UID_KEY: "automation-seller-uid",
                             SAVED_PROFILE_KEY: '{"email":"seeded@example.com"}',
                             SAVE_LOGIN_MODAL_SHOWN_KEY: "true"})

    mocked_login(login)

    expect(logged_out_page).to_have_url(re.compile(BUYER_LANDING_DESKTOP), timeout=30_000)
    stored = login.local_storage(TOKEN_KEY, SESSION_ID_KEY, BUYER_ID_KEY, SELLER_UID_KEY,
                                 SAVED_PROFILE_KEY, SAVE_LOGIN_MODAL_SHOWN_KEY)
    assert stored[TOKEN_KEY] == SESSION                 # BUY-LGN-34
    assert stored[SESSION_ID_KEY] is None               # BUY-LGN-35
    assert stored[BUYER_ID_KEY] == BUYER_UID            # BUY-LGN-36
    assert stored[SELLER_UID_KEY] is None               # BUY-LGN-36
    assert stored[SAVED_PROFILE_KEY] is None            # BUY-LGN-37
    assert stored[SAVE_LOGIN_MODAL_SHOWN_KEY] is None   # BUY-LGN-37
    response = login.login_response()                   # BUY-LGN-38
    assert response["userType"] == 3
    assert response["isBuyer"] is True
    assert response["email"] == EMAIL
    assert response["sessionId"] == SESSION


def test_buyer_status_is_requested_before_the_redirect(logged_out_page):
    """BUY-LGN-39: buyer/status is called after POST user and before the buyer is routed on."""
    login = BuyerLoginPage(logged_out_page)
    calls = login.watch_api_calls()
    login.open_login()

    mocked_login(login)

    expect(logged_out_page).to_have_url(re.compile(BUYER_LANDING_DESKTOP), timeout=30_000)
    assert [call for call in calls if call in ("user", "buyer/status")] == ["user", "buyer/status"]


def test_verified_buyer_lands_on_recommendations(logged_out_page):
    """BUY-LGN-40: a verified buyer with no in-app previous path lands on /buyer/recommendations at
    desktop width."""
    login = BuyerLoginPage(logged_out_page).open_login()

    mocked_login(login, buyer_status="verified")

    expect(logged_out_page).to_have_url(re.compile(BUYER_LANDING_DESKTOP), timeout=30_000)


def test_verified_buyer_lands_on_browse_on_a_small_screen(logged_out_page):
    """BUY-LGN-41: the same login at 390x844 (<= 1180px) ends on /buyer/browse."""
    logged_out_page.set_viewport_size({"width": 390, "height": 844})
    login = BuyerLoginPage(logged_out_page).open_login()

    mocked_login(login, buyer_status="verified")

    expect(logged_out_page).to_have_url(re.compile(BUYER_LANDING_MOBILE), timeout=30_000)


@pytest.mark.parametrize("status", ["not_verified", "pending"])
def test_buyer_without_verification_lands_on_profile(logged_out_page, status):
    """BUY-LGN-42 (not_verified), BUY-LGN-44 (any other status, no cuecardlisting previous path):
    the buyer is sent to /buyer/profile."""
    login = BuyerLoginPage(logged_out_page).open_login()

    mocked_login(login, buyer_status=status)

    expect(logged_out_page).to_have_url(re.compile(BUYER_PROFILE_PATH), timeout=30_000)


def test_not_verified_buyer_returns_to_a_shared_card_path(logged_out_page):
    """BUY-LGN-43: a not_verified buyer whose previous in-app path is under /buyer/sharedcard goes
    back to that path instead of /buyer/profile."""
    login = BuyerLoginPage(logged_out_page).open_login()
    login.set_previous_path(SHARED_CARD_PATH)
    expect(login.email_input).to_be_visible()

    mocked_login(login, buyer_status="not_verified")

    expect(logged_out_page).to_have_url(re.compile(re.escape(SHARED_CARD_PATH)), timeout=30_000)


def test_bounced_buyer_returns_to_the_route_that_bounced_them(logged_out_page):
    """BUY-LGN-45: opening a protected buyer route logged out bounces to /buyer/login, and a verified
    login returns to that route."""
    login = BuyerLoginPage(logged_out_page).open_after_bounce(BOUNCED_PATH)

    mocked_login(login, buyer_status="verified")

    expect(logged_out_page).to_have_url(re.compile(re.escape(BOUNCED_PATH)), timeout=30_000)


def test_a_bounced_profile_path_is_ignored(logged_out_page):
    """BUY-LGN-46: /buyer/profile as the bounced-from path is dropped for the default landing route."""
    login = BuyerLoginPage(logged_out_page).open_after_bounce(BUYER_PROFILE_PATH)

    mocked_login(login, buyer_status="verified")

    expect(logged_out_page).to_have_url(re.compile(BUYER_LANDING_DESKTOP), timeout=30_000)


# ------------------------------------------------------------------ already authenticated
# The session is seeded into this throwaway context (localStorage + the persisted Redux state the
# app boots from). No real login, and auth/buyer.json is neither read nor written.

def test_a_live_session_never_sees_the_login_form(logged_out_page):
    """BUY-LGN-47: /buyer/login with a live buyer session redirects to the buyer's landing route."""
    login = BuyerLoginPage(logged_out_page).open_login()

    login.seed_live_session({"status": "verified", "onboardingStage": 2})

    expect(logged_out_page).to_have_url(re.compile(BUYER_LANDING_DESKTOP), timeout=30_000)
    expect(login.email_input).to_have_count(0)


@pytest.mark.parametrize("verification", [{"status": "verified"},
                                          {"status": "verified", "onboardingStage": 1}],
                         ids=["no-onboarding-stage", "stage-1"])
def test_a_live_session_mid_onboarding_goes_to_onboarding(logged_out_page, verification):
    """BUY-LGN-48: a live session whose verification state has no onboardingStage, or stage 1, is sent
    to /buyer/onboarding."""
    login = BuyerLoginPage(logged_out_page).open_login()

    login.seed_live_session(verification)

    expect(logged_out_page).to_have_url(re.compile(re.escape(BUYER_ONBOARDING_PATH)), timeout=30_000)


# ------------------------------------------------------------------ the one real login (run it last)

@pytest.mark.live_login
def test_live_buyer_login_lands_on_a_buyer_screen(logged_out_page):
    """BUY-LGN-12, BUY-LGN-20, BUY-LGN-27, BUY-LGN-34, BUY-LGN-39 end to end against the backend.

    The only test in this module that touches the account: submitting step 1 sends ONE real passcode,
    and the login creates a device session that can evict a saved auth/buyer.json - re-run
    `python scripts/save_auth_state.py buyer` afterwards.

    Which landing page is correct is still open (module.md open question 1: is DD_BUYER_LOGIN_EMAIL a
    verified buyer or not), so any buyer landing route is accepted here; /buyer/recommendations vs
    /buyer/profile is pinned by the rewritten-status tests above instead. `buyer/status` answering
    HTTP 502 (oddity 5) also lands the buyer on one of these routes.
    """
    if not settings.buyer_login_email:
        pytest.skip("DD_BUYER_LOGIN_EMAIL is not set: no registered QA buyer to log in as")
    if not settings.buyer_login_otp:
        pytest.skip("DD_BUYER_LOGIN_OTP is not set: no passcode to submit")

    login = BuyerLoginPage(logged_out_page)
    calls = login.watch_api_calls()
    login.open_login()

    with logged_out_page.expect_request(PASSCODE_URL) as passcode:
        login.submit_email(settings.buyer_login_email)
    assert passcode.value.post_data_json == {"email": settings.buyer_login_email, "userType": 3}
    login.expect_code_step()

    with logged_out_page.expect_response(LOGIN_API_URL) as response:
        login.submit_code(settings.buyer_login_otp)
    body = response.value.json()
    if body.get("status") != "200":
        pytest.fail(f"POST user refused DD_BUYER_LOGIN_OTP: {body}")

    expect(logged_out_page).to_have_url(
        re.compile(r"/buyer/(recommendations|browse|profile|onboarding)"), timeout=30_000)
    assert login.local_storage(TOKEN_KEY)[TOKEN_KEY]
    assert [call for call in calls if call in ("user", "buyer/status")] == ["user", "buyer/status"]
