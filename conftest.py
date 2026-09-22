"""Shared fixtures: one browser context per role, API clients, browse-picked companies and test files."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import os  # noqa: E402

from config import settings  # noqa: E402
from designcheck.checker import DesignRun  # noqa: E402
from pages.buyer_browse_page import BuyerBrowsePage  # noqa: E402
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
# each picking up where the previous one stopped. A failing step doesn't stop the others.

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
    """(uid, cue_card, None): the first company on /buyer/browse that still offers Express Interest,
    opened once. The journey fills the founder note whenever the modal asks for one."""
    uid, cue_card = buyer_browse.open_next_fresh_listing(buyer_browse.seen)
    browse_used.add(uid)
    sys.__stdout__.write(f"\n  journey card: {cue_card.title} | uid {uid}\n")
    return uid, cue_card, None


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
    if item.config.getoption("--pause-on-failure") and item.config.getoption("headed"):
        pages = [page for ctx in OPEN_CONTEXTS for page in ctx.pages]
        if pages:  # the most recently opened tab is the one the test was driving
            pages[-1].bring_to_front()
            pages[-1].pause()


# ---------------------------------------------------------------- design checks (no AI, no Figma calls)
# design.check("<flow step id>") compares the page with docs/features/<slug>/refs/<step>.spec.json (+ .png).
# Off unless --design / DD_DESIGN_CHECK=1. Differences never fail a test; DD_DESIGN_STRICT=1 fails the run
# at the end when any feature has high-severity design issues.

def pytest_addoption(parser):
    parser.addoption("--design", action="store_true", help="run design checks against the saved Figma refs")
    parser.addoption("--pause-on-failure", action="store_true",
                     help="with --headed: when a test fails, keep the browser as it is and open the Playwright "
                          "Inspector; click Resume to go on with the next test")


def pytest_configure(config):
    enabled = config.getoption("--design") or os.getenv("DD_DESIGN_CHECK") == "1"
    config._design_run = DesignRun(enabled=enabled, strict=os.getenv("DD_DESIGN_STRICT") == "1")


class _DesignFixture:
    def __init__(self, run, slug):
        self._run, self._slug = run, slug

    def check(self, step_id, page, scope=None):
        """Screenshot and compare this moment with flow step `step_id` (a no-op without --design)."""
        if not self._slug:
            raise RuntimeError("Set DESIGN_FEATURE = '<slug>' in the test module to use design.check()")
        return self._run.check(self._slug, page, step_id, scope)


@pytest.fixture(scope="module")
def design(request):
    """Bound to the module's DESIGN_FEATURE (a folder name under docs/features/)."""
    return _DesignFixture(request.config._design_run, getattr(request.module, "DESIGN_FEATURE", None))


def pytest_sessionfinish(session):
    run = session.config._design_run
    session.config._design_reports = run.finish() if run.enabled else []
    if run.strict and any(high for _, _, high in session.config._design_reports):
        session.exitstatus = 1


def pytest_terminal_summary(terminalreporter, config):
    reports = getattr(config, "_design_reports", [])
    if not reports:
        return
    terminalreporter.section("design check")
    for feature, report, high in reports:
        terminalreporter.write_line(f"{feature}: {high} high-severity issue(s) -> {report}")
