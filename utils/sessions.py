"""Helpers shared by fixtures and module-scoped setups."""
from pathlib import Path

import pytest

from config import settings
from utils.api_client import find_key

VIEWPORT = {"width": 1440, "height": 900}
STATE_BY_ROLE = {"buyer": settings.buyer_state, "seller": settings.seller_state, "admin": settings.admin_state,
                 # hot-lead-engagement-visibility: a POC of a dedicated, never-hot buyer lead
                 "hle_buyer": settings.hle_buyer_state}
LOGIN_PATHS = {"buyer": "buyer/login", "seller": "login", "admin": "admin/login", "hle_buyer": "buyer/login"}


def require_state(path: Path, role: str) -> Path:
    if not path.exists():
        pytest.skip(f"No saved {role} session at {path}; run: python scripts/save_auth_state.py {role}")
    return path


# Every context opened through new_role_page, so a failing test can screenshot what was on screen.
OPEN_CONTEXTS = []


def _new_context(browser, **kwargs):
    ctx = browser.new_context(viewport=VIEWPORT, **kwargs)
    OPEN_CONTEXTS.append(ctx)
    ctx.on("close", lambda c: OPEN_CONTEXTS.remove(c) if c in OPEN_CONTEXTS else None)
    return ctx, ctx.new_page()


def new_role_page(browser, role):
    """Open a context logged in as `role`. Caller closes the returned context."""
    return _new_context(browser, storage_state=str(require_state(STATE_BY_ROLE[role], role)))


def new_anonymous_page(browser):
    """Open a context with no saved session, for the logged-out screens (login, signup).

    Never loads or writes auth/<role>.json: a login test must not disturb the saved sessions.
    """
    return _new_context(browser)


def cue_card_company_id(payload):
    data = payload.get("data") if isinstance(payload, dict) else None
    return (data or {}).get("id") or find_key(payload, "companyId")


# Listeners registered on a shared page (page.on(...)), so reset_page can take them off again.
_TRACKED_LISTENERS = {}


def track_listener(page, event, handler):
    """page.on(event, handler), remembered so the next reset removes it.

    A module-scoped page outlives the test that attached a watcher; without this the watchers of
    every earlier test keep firing for the rest of the file.
    """
    page.on(event, handler)
    _TRACKED_LISTENERS.setdefault(page, []).append((event, handler))


def reset_page(context, page, keep_session=False):
    """Give a shared context back the clean slate a fresh one would have.

    Routes, cookies, localStorage, sessionStorage and tracked listeners: everything a previous test
    could have left behind. The page keeps its URL; tests navigate themselves.

    keep_session=True (a logged-in module) drops only routes and listeners: the login lives in
    localStorage and cookies, so clearing them would log the role out.
    """
    for event, handler in _TRACKED_LISTENERS.pop(page, []):
        page.remove_listener(event, handler)
    page.unroute_all(behavior="ignoreErrors")
    if keep_session:
        return
    try:
        page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
    except Exception:
        pass  # about:blank, or a page that never reached an origin: nothing to clear
    context.clear_cookies()
