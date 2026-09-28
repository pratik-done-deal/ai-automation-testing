"""Log in once by hand and save the session for the test suite.

Usage (from automation/):
    python scripts/save_auth_state.py buyer    # opens <app>/buyer/login
    python scripts/save_auth_state.py admin    # opens <app>/admin/login  (use a biz user)
    python scripts/save_auth_state.py seller   # optional: the test run asks for the seller login itself
    python scripts/save_auth_state.py hle_buyer  # a POC of the dedicated hot-lead buyer lead (HLE S6-01)
    python scripts/save_auth_state.py biz_user   # opens <app>/admin/login: a biz user (userType 4), star-seller-fundraising

Complete the login (OTP / LinkedIn) in the opened browser, then press Enter here.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import settings  # noqa: E402
from utils.sessions import LOGIN_PATHS, STATE_BY_ROLE as STATE_PATHS  # noqa: E402


def main(role):
    if role not in LOGIN_PATHS:
        sys.exit(f"role must be one of {', '.join(LOGIN_PATHS)}")
    target = STATE_PATHS[role]
    target.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(settings.app_url + LOGIN_PATHS[role])
        input(f"Log in as the {role} test account, then press Enter to save the session... ")
        context.storage_state(path=str(target))
        browser.close()
    print(f"Saved {role} session to {target}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
