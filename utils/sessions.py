"""Helpers shared by fixtures and module-scoped setups."""
from pathlib import Path

import pytest

from config import settings
from utils.api_client import find_key

VIEWPORT = {"width": 1440, "height": 900}
STATE_BY_ROLE = {"buyer": settings.buyer_state, "seller": settings.seller_state, "admin": settings.admin_state}
LOGIN_PATHS = {"buyer": "buyer/login", "seller": "login", "admin": "admin/login"}


def require_state(path: Path, role: str) -> Path:
    if not path.exists():
        pytest.skip(f"No saved {role} session at {path}; run: python scripts/save_auth_state.py {role}")
    return path


# Every context opened through new_role_page, so a failing test can screenshot what was on screen.
OPEN_CONTEXTS = []


def new_role_page(browser, role):
    """Open a context logged in as `role`. Caller closes the returned context."""
    ctx = browser.new_context(storage_state=str(require_state(STATE_BY_ROLE[role], role)), viewport=VIEWPORT)
    OPEN_CONTEXTS.append(ctx)
    ctx.on("close", lambda c: OPEN_CONTEXTS.remove(c) if c in OPEN_CONTEXTS else None)
    return ctx, ctx.new_page()


def cue_card_company_id(payload):
    data = payload.get("data") if isinstance(payload, dict) else None
    return (data or {}).get("id") or find_key(payload, "companyId")
