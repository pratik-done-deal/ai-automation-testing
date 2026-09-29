"""Shared fixtures: one browser context per role, API clients, browse-picked companies and test files."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import os  # noqa: E402
from collections import Counter  # noqa: E402

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # noqa: E402

try:                       # the suite runs with or without it; --alluredir needs the plugin
    import allure          # noqa: E402
except ImportError:
    allure = None

from config import settings  # noqa: E402
from designcheck.checker import DesignRun  # noqa: E402
from pages.buyer_module.buyer_browse_page import BuyerBrowsePage  # noqa: E402
from utils.api_client import DoneDealApi  # noqa: E402
from utils.flows import express_interest_on  # noqa: E402
from utils.registry import entry_for_requirement, is_shipped, load_registry, requirement_pattern  # noqa: E402
from utils.run_state import load_all  # noqa: E402
from utils.sessions import (  # noqa: E402
    OPEN_CONTEXTS, STATE_BY_ROLE, new_anonymous_page, new_role_page, require_state, reset_page,
)


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


@pytest.fixture
def biz_user_page(browser):
    """A biz user (userType 4) page; skips while auth/biz_user.json is missing (star-seller-fundraising)."""
    yield from _role_page(browser, "biz_user")


@pytest.fixture(scope="module")
def _logged_out_context(browser):
    """ONE logged-out context per test file. Opening a context per test is the slowest thing a
    suite can do, and with --headed it opens a window per test."""
    ctx, page = new_anonymous_page(browser)
    yield ctx, page
    ctx.close()


@pytest.fixture
def logged_out_page(_logged_out_context):
    """The file's logged-out page, reset before each test: no routes, cookies, storage or watchers
    from the test before it. Tests navigate themselves (there is no screen-load request to await)."""
    ctx, page = _logged_out_context
    reset_page(ctx, page)
    return page


@pytest.fixture(scope="module")
def _admin_module_context(browser):
    """ONE logged-in admin context per test file (skips the whole file without auth/admin.json)."""
    ctx, page = new_role_page(browser, "admin")
    yield ctx, page
    ctx.close()


@pytest.fixture
def admin_module_page(_admin_module_context):
    """The file's admin page, with the previous test's routes and listeners removed (the login stays).
    Tabs the previous test opened (e.g. a cue card opened from the Sellers list) are closed, and
    context-wide routes dropped. Tests navigate themselves."""
    ctx, page = _admin_module_context
    for other in ctx.pages:
        if other is not page:
            other.close()
    ctx.unroute_all(behavior="ignoreErrors")
    reset_page(ctx, page, keep_session=True)
    return page


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


ROLE_FOLDERS = {"buyer_test_cases": "buyer", "seller_test_cases": "seller",
                "admin_test_cases": "admin", "biz_user_test_cases": "biz_user",
                "api": "api", "e2e": "e2e"}


def pytest_collection_modifyitems(config, items):
    _apply_role_markers(items)
    _apply_lifecycle(config, items)
    # Phase 2's journey accepts the deal, which removes it from Interest Received. Run the
    # read-only seller accept-modal tests before it, while that row is still there.
    items.sort(key=lambda item: "test_phase2_" in item.nodeid)


def _apply_role_markers(items):
    """test_cases/<role>_test_cases/... gets its role marker automatically, so no module needs
    pytestmark just for that. A module can still add buyer/api/destructive markers itself."""
    for item in items:
        for folder in Path(item.fspath).parts:
            role = ROLE_FOLDERS.get(folder)
            if role:
                item.add_marker(getattr(pytest.mark, role))


# ---------------------------------------------------------------- feature lifecycle
# When a new feature changes behaviour an existing test checks, the old test is kept and the new
# version is added next to it:
#   @pytest.mark.superseded_by("<slug>")   old behaviour: runs until <slug> ships, then is skipped
#   @pytest.mark.pending_feature("<slug>") new behaviour: strict xfail until <slug> ships, then runs
# "Shipped" is specs/features/<slug>/feature.yml `status`, or DD_SHIPPED / DD_UNSHIPPED for one run.
# An XPASS on a pending test means the feature is live here: mark it shipped.

def _lifecycle_slug(item, mark):
    slug = mark.args[0] if mark.args else None
    if slug not in load_registry():
        raise pytest.UsageError(f"{item.nodeid}: @pytest.mark.{mark.name}({slug!r}) names no "
                                f"specs/features/<slug>/feature.yml")
    return slug


def _apply_lifecycle(config, items):
    pending, superseded = [], []
    for item in items:
        for mark in item.iter_markers("pending_feature"):
            slug = _lifecycle_slug(item, mark)
            if not is_shipped(slug):
                pending.append(slug)
                item.add_marker(pytest.mark.xfail(
                    strict=True, raises=(AssertionError, PlaywrightTimeoutError),
                    reason=f"pending_feature: {slug} isn't shipped here. If this passes, set status: shipped "
                           f"in specs/features/{slug}/feature.yml (or run with DD_SHIPPED={slug})"))
        for mark in item.iter_markers("superseded_by"):
            slug = _lifecycle_slug(item, mark)
            if is_shipped(slug):
                superseded.append(slug)
                item.add_marker(pytest.mark.skip(reason=f"superseded_by: {slug} has shipped and replaced "
                                                        f"this behaviour (kept for history)"))
    config._lifecycle = (Counter(pending), Counter(superseded))


# ---------------------------------------------------------------- Allure labels
# Tests are labelled from the requirement ids in their docstring, so no test needs decorators and
# the report groups by the same modules and features the coverage report uses.
#   feature = the module / feature that owns the requirement   (Buyer Login (email + OTP))
#   story   = the test file                                     (buyer login)
#   tags    = every requirement id the test names               (BUY-LGN-07, BUY-LGN-08)

REQUIREMENT_RE = requirement_pattern()


@pytest.fixture(autouse=True)
def _allure_labels(request):
    if allure is None:
        return
    function = getattr(request.node, "function", None)
    ids = sorted(set(REQUIREMENT_RE.findall(function.__doc__ or ""))) if function else []
    entry = next((e for e in map(entry_for_requirement, ids) if e), None)
    role = next((m.name for m in request.node.iter_markers() if m.name in ROLE_FOLDERS.values()), None)
    allure.dynamic.feature(entry.name if entry else (role or "suite"))
    allure.dynamic.story(request.node.module.__name__.split(".")[-1].removeprefix("test_").replace("_", " "))
    for req in ids:
        allure.dynamic.tag(req)


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
                if allure is not None:
                    allure.attach.file(str(path), name=f"{page.url}", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
    if item.config.getoption("--pause-on-failure") and item.config.getoption("headed"):
        pages = [page for ctx in OPEN_CONTEXTS for page in ctx.pages]
        if pages:  # the most recently opened tab is the one the test was driving
            pages[-1].bring_to_front()
            pages[-1].pause()


# ---------------------------------------------------------------- design checks (no AI, no Figma calls)
# design.check("<flow step id>") compares the page with specs/features/<slug>/refs/<step>.spec.json (+ .png).
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
    """Bound to the module's DESIGN_FEATURE (a folder name under specs/features/)."""
    return _DesignFixture(request.config._design_run, getattr(request.module, "DESIGN_FEATURE", None))


def pytest_sessionfinish(session):
    run = session.config._design_run
    session.config._design_reports = run.finish() if run.enabled else []
    if run.strict and any(high for _, _, high in session.config._design_reports):
        session.exitstatus = 1


def pytest_terminal_summary(terminalreporter, config):
    pending, superseded = getattr(config, "_lifecycle", (Counter(), Counter()))
    if pending or superseded:
        terminalreporter.section("feature lifecycle")
        for slug, count in sorted(pending.items()):
            terminalreporter.write_line(f"{slug}: not shipped here, {count} pending_feature test(s) run as xfail")
        for slug, count in sorted(superseded.items()):
            terminalreporter.write_line(f"{slug}: shipped, {count} superseded test(s) skipped")
    reports = getattr(config, "_design_reports", [])
    if not reports:
        return
    terminalreporter.section("design check")
    for feature, report, high in reports:
        terminalreporter.write_line(f"{feature}: {high} high-severity issue(s) -> {report}")
