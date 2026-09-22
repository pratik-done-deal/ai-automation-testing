"""Shared fixtures: one browser context per role, API clients, browse-picked companies and test files."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from config import settings  # noqa: E402
from pages.buyer_browse_page import BuyerBrowsePage  # noqa: E402
from pages.buyer_cue_card_page import BuyerCueCardPage  # noqa: E402
from utils.api_client import DoneDealApi  # noqa: E402
from utils.flows import express_interest_on  # noqa: E402
from utils.run_state import load_all  # noqa: E402
from utils.sessions import OPEN_CONTEXTS, STATE_BY_ROLE, new_role_page, require_state  # noqa: E402


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


# ---------------------------------------------------------------- companies picked from /buyer/browse

@pytest.fixture(scope="session")
def browse_used():
    """Cue card uids already claimed: earlier phase 1 runs plus anything picked in this session."""
    return set(load_all())


# ---------------------------------------------------------------- buyer journeys: one cue card, no reloads
# A journey module opens ONE cue card via View Listing and runs its tests in order on that tab,
# each picking up where the previous one stopped (marker `incremental`).

@pytest.fixture(scope="session")
def buyer_browse(browser, browse_used):
    """The session's single buyer context, sitting on /buyer/browse."""
    ctx, page = new_role_page(browser, "buyer")
    browse = BuyerBrowsePage(page).open_browse()
    browse.seen = set(browse_used)
    yield browse
    ctx.close()


@pytest.fixture(scope="session")
def journey_card(buyer_browse, browse_used):
    """(uid, cue_card, modal): an in-preference company, Express Interest modal open. Opened once."""
    opened = buyer_browse.open_journey_card(browse_used, outside_pref=False, limit=10)
    if not opened:
        pytest.skip("No in-preference company offering Express Interest on /buyer/browse")
    return opened


@pytest.fixture(scope="session")
def outside_pref_journey_card(buyer_browse, browse_used):
    """(uid, cue_card, modal): a company outside the buyer's preferences, modal open. Opened once."""
    if settings.outside_pref_company_uid:
        uid = settings.outside_pref_company_uid
        cue_card = BuyerCueCardPage(buyer_browse.page.context.new_page()).open_cue_card(uid)
        return uid, cue_card, cue_card.click_express_interest()
    opened = buyer_browse.open_journey_card(browse_used, outside_pref=True, limit=8)
    if not opened:
        pytest.skip("No outside-preference company in the first /buyer/browse listings; "
                    "set DD_OUTSIDE_PREF_COMPANY_UID")
    return opened


@pytest.fixture
def fresh_listing(buyer_page, browse_used):
    """(uid, cue_card) for a company opened from /buyer/browse via View Listing. Tests using it consume it."""
    return BuyerBrowsePage(buyer_page).open_browse().open_next_fresh_listing(browse_used)


# ---------------------------------------------------------------- buyer at the document request step

@pytest.fixture
def live_success_view(fresh_listing):
    """SuccessView after a real express interest (destructive: uses up the company)."""
    uid, cue_card = fresh_listing
    return express_interest_on(cue_card, uid)


# ---------------------------------------------------------------- files

def _write_pdf(path):
    path.write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )
    return path


@pytest.fixture(scope="session")
def make_pdf(tmp_path_factory):
    """make_pdf("mis") -> a small PDF with a distinct name, so rows and share toggles can tell files apart."""
    folder = tmp_path_factory.mktemp("docs")
    return lambda tag: _write_pdf(folder / f"automation-{tag}.pdf")


@pytest.fixture(scope="session")
def seller_company_id():
    # Optional: without it /deals opens the logged-in seller's own company.
    return settings.seller_company_id


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
    if "incremental" in item.keywords:
        item.parent._journey_failed = item.name
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


def pytest_runtest_setup(item):
    # Journey steps build on each other: after a real failure, skip the rest instead of cascading.
    failed = getattr(item.parent, "_journey_failed", None)
    if failed and "incremental" in item.keywords:
        pytest.skip(f"earlier journey step failed: {failed}")
