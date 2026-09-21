"""Shared fixtures: one browser context per role, API clients, and test data pools."""
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from config import settings  # noqa: E402
from utils.api_client import DoneDealApi  # noqa: E402
from utils.flows import run_express_interest  # noqa: E402
from utils.sessions import OPEN_CONTEXTS, STATE_BY_ROLE, new_role_page, require_state  # noqa: E402


def _require(value, name):
    if not value:
        pytest.skip(f"{name} is not configured in automation/.env")
    return value


# ---------------------------------------------------------------- browser contexts per role

def _role_page(browser, role):
    ctx, page = new_role_page(browser, role)
    yield page
    ctx.close()


@pytest.fixture
def buyer_page(browser):
    yield from _role_page(browser, "buyer")


@pytest.fixture
def seller_page(browser):
    yield from _role_page(browser, "seller")


@pytest.fixture
def admin_page(browser):
    yield from _role_page(browser, "admin")


# ---------------------------------------------------------------- API clients

@pytest.fixture(scope="session")
def buyer_api(playwright):
    api = DoneDealApi(playwright, settings.api_url, require_state(STATE_BY_ROLE["buyer"], "buyer"))
    yield api
    api.dispose()


@pytest.fixture(scope="session")
def seller_api(playwright):
    api = DoneDealApi(playwright, settings.api_url, require_state(STATE_BY_ROLE["seller"], "seller"))
    yield api
    api.dispose()


@pytest.fixture(scope="session")
def admin_api(playwright):
    api = DoneDealApi(playwright, settings.api_url, require_state(STATE_BY_ROLE["admin"], "admin"))
    yield api
    api.dispose()


# ---------------------------------------------------------------- test data

class _UidPool:
    """Hands out each fresh cue card uid once per run; an express interest can only happen once per company."""

    def __init__(self, uids):
        self._uids = list(uids)
        self._lock = threading.Lock()

    def take(self):
        with self._lock:
            if not self._uids:
                pytest.skip("DD_FRESH_COMPANY_UIDS exhausted: add more uids or reset the buyer's deals")
            return self._uids.pop(0)


@pytest.fixture(scope="session")
def uid_pool():
    # The last uid is reserved for read-only checks (open modal, then cancel) and never submitted.
    return _UidPool(settings.fresh_company_uids[:-1])


@pytest.fixture
def fresh_company_uid(uid_pool):
    return uid_pool.take()


@pytest.fixture(scope="session")
def readonly_company_uid():
    if not settings.fresh_company_uids:
        pytest.skip("DD_FRESH_COMPANY_UIDS is not configured in automation/.env")
    return settings.fresh_company_uids[-1]


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory):
    path = tmp_path_factory.mktemp("docs") / "automation-sample.pdf"
    path.write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )
    return path


@pytest.fixture(scope="session")
def seller_company_id():
    # Optional: without it /deals opens the logged-in seller's own company.
    return settings.seller_company_id


@pytest.fixture(scope="session")
def buyer_display_name():
    # Optional: without it the seller tests use the newest Interest Received row.
    return settings.buyer_display_name


# ---------------------------------------------------------------- composite buyer flows

@pytest.fixture
def buyer_at_success_view(buyer_page, fresh_company_uid):
    return run_express_interest(buyer_page, fresh_company_uid)


def pytest_collection_modifyitems(items):
    # Phase 2's journey accepts the deal, which removes it from Interest Received. Run the
    # read-only seller accept-modal tests before it, while that row is still there.
    items.sort(key=lambda item: "test_phase2_" in item.nodeid)


SCREENSHOT_DIR = Path(__file__).parent / "reports" / "screenshots"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    # Save every open tab (browse page, cue card tab, seller, admin) as reports/screenshots/<test>-<n>.png
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in item.nodeid.split("::")[-1])
    shot = 0
    for ctx in list(OPEN_CONTEXTS):
        for page in ctx.pages:
            shot += 1
            path = SCREENSHOT_DIR / f"{safe_name}-{shot}.png"
            try:
                page.screenshot(path=str(path), full_page=True)
                report.sections.append(("screenshot", f"{page.url} -> {path}"))
            except Exception:
                pass
