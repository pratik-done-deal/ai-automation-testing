"""Test data and run chains for star-seller-fundraising (SSF).

Sellers are found by browsing, never from uids: each case names the kind of seller it needs
("F-ready", "F-star", ...; test-cases.md section 6) and utils.ssf_browse picks one from the admin
Sellers list ("Star Sellers" / "Non Star Sellers"). AdminSellerCueCardPage.open_seller then opens it
the way a user does: Sellers > tab > search the S-id > Actions "View". Some sellers are produced by
an earlier case of the same run (S1-04 stars an F-ready); `produced_or_env` falls back to those.
"""
import json

import pytest

from utils import ssf_browse
from utils.network import failure_body
from utils.registry import is_shipped

SLUG = "star-seller-fundraising"

# Cases that passed in this run, for the chains in test-cases.md section 6.
_DONE = {}
# Sellers whose missing document an earlier case of this run uploaded: {uid: case}.
_CONSUMED = {}


def seller(name, case):
    """A seller of kind `name`, browsed for (see utils.ssf_browse). Skips when none fits."""
    return ssf_browse.pick(name, case)


def done(case, uid=None):
    _DONE[case] = uid


def require_done(case, needs):
    if needs not in _DONE:
        pytest.skip(f"{case}: needs {needs} to have passed earlier in this run")
    return _DONE[needs]


def produced_or_env(case, name, produced_by):
    """A browsed seller of kind `name`, else the one `produced_by` turned into it in this run."""
    try:
        return ssf_browse.pick(name, case)
    except pytest.skip.Exception:
        if produced_by in _DONE:
            return _DONE[produced_by]
        raise


def star_seller(case, name, produced_by, consumes=False):
    """A star seller still missing its document, browsed for; never one an earlier case of this run
    uploaded the document to. `consumes`: this case uploads it, so later cases browse for another."""
    try:
        uid = ssf_browse.pick(name, case, exclude=set(_CONSUMED))
    except pytest.skip.Exception:
        uid = _DONE.get(produced_by)
        if not uid or uid in _CONSUMED:
            raise
    if consumes:
        _CONSUMED[uid] = case
        ssf_browse.forget(name)
    return uid


def require_shipped(case, why):
    """For pending cases that would destroy data no retry can bring back while the feature is absent."""
    if not is_shipped(SLUG):
        pytest.skip(f"{case}: runs only once {SLUG} is on QA ({why})")


def hold_objective_save_until_shipped(page):
    """While the feature isn't on QA, answer the objective save with a failure so a pending
    objective-block case (strict xfail) can't really change a star seller's objective. The app's
    callback reloads the page on any answer, so nothing is stored. Off once the feature ships.

    Routed on the whole context: the cue card opens in a new tab from the Sellers list ("View")."""
    if is_shipped(SLUG):
        return

    def handler(route):
        body = route.request.post_data or ""
        if route.request.method == "PUT" and '"objective"' in body:
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps(failure_body(message="held by automation")))
        return route.fallback()

    page.context.route("**/company/update/admin", handler)
