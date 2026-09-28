"""Test data and run chains for star-seller-fundraising (SSF), read from DD_SSF_SELLERS in .env.

    DD_SSF_SELLERS=F-ready:<uid>,F-nodeck:<uid>,A-ready:<uid>,...

Names are the seller names of test-cases.md section 6 (case-insensitive). A missing name skips the
cases that need it, naming the variable. Some sellers are produced by an earlier case of the same
run (F-ready becomes F-star after S1-04); `produced_or_env` covers both.
"""
import json

import pytest

from config import settings
from utils.network import failure_body
from utils.registry import is_shipped

SLUG = "star-seller-fundraising"
VAR = "DD_SSF_SELLERS"

# Why a seller can't be prepared on QA today (test-cases.md section 6). Shown in the skip.
BLOCKED = {
    "F-NOCONSENT": "where the pitch deck consent setting is turned off is not known",
    "F-CALL": "how a 1-on-1 seller call is marked completed on QA is not known (needs a recipe from dev)",
    "F-DEALCALL": "how to give a seller only a buyer deal call on QA is not known (needs a recipe from dev)",
    "F-CANCELLED": "how a 1-on-1 seller call is cancelled on QA is not known (needs a recipe from dev)",
    "F-SCHEDULED": "a seller with only a scheduled, not completed 1-on-1 call must be set up by hand",
    "L-STAR": "a legacy star (funding, highlights, no pitch deck) must be starred BEFORE the release reaches QA",
}

# Cases that passed in this run, for the chains in test-cases.md section 6.
_DONE = {}
# Sellers whose missing document an earlier case of this run uploaded: {uid: case}.
_CONSUMED = {}


def _sellers():
    pairs = {}
    for part in (settings.ssf_sellers or "").split(","):
        if ":" in part:
            key, value = part.split(":", 1)
            if key.strip() and value.strip():
                pairs[key.strip().upper()] = value.strip()
    return pairs


def seller(name, case):
    uid = _sellers().get(name.upper())
    if not uid:
        why = BLOCKED.get(name.upper())
        pytest.skip(f"{case}: set {VAR}={name}:<cue card uid>" + (f" (BLOCKED: {why})" if why else ""))
    return uid


def done(case, uid=None):
    _DONE[case] = uid


def require_done(case, needs):
    if needs not in _DONE:
        pytest.skip(f"{case}: needs {needs} to have passed earlier in this run")
    return _DONE[needs]


def produced_or_env(case, name, produced_by):
    """The seller `name` from .env, else the one `produced_by` turned into it in this run."""
    uid = _sellers().get(name.upper())
    if uid:
        return uid
    if produced_by in _DONE:
        return _DONE[produced_by]
    pytest.skip(f"{case}: set {VAR}={name}:<cue card uid>, or run {produced_by} first in the same run")


def star_seller(case, name, produced_by, consumes=False):
    """A star seller still missing its document: `<name>-<case>` from .env first (a seller of its own
    for that case), else `name` / what `produced_by` made of it this run, unless an earlier case of
    this run already uploaded the document to it. `consumes`: this case uploads it."""
    uid = _sellers().get(f"{name}-{case}".upper()) or produced_or_env(case, name, produced_by)
    if uid in _CONSUMED:
        pytest.skip(f"{case}: {_CONSUMED[uid]} already uploaded the missing document to {name} in this run; "
                    f"give {case} its own seller: {VAR}={name}-{case}:<cue card uid>")
    if consumes:
        _CONSUMED[uid] = case
    return uid


def require_shipped(case, why):
    """For pending cases that would destroy data no retry can bring back while the feature is absent."""
    if not is_shipped(SLUG):
        pytest.skip(f"{case}: runs only once {SLUG} is on QA ({why})")


def hold_objective_save_until_shipped(page):
    """While the feature isn't on QA, answer the objective save with a failure so a pending
    objective-block case (strict xfail) can't really change a star seller's objective. The app's
    callback reloads the page on any answer, so nothing is stored. Off once the feature ships."""
    if is_shipped(SLUG):
        return

    def handler(route):
        body = route.request.post_data or ""
        if route.request.method == "PUT" and '"objective"' in body:
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps(failure_body(message="held by automation")))
        return route.fallback()

    page.route("**/company/update/admin", handler)
