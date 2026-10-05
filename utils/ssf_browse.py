"""Pick star-seller-fundraising (SSF) sellers by browsing the admin Sellers list, not from uids.

Each test case names the kind of seller it needs ("F-ready", "F-star", ...; test-cases.md
section 6). The picker walks the same list the admin sees under Sellers > "Star Sellers" or
"Non Star Sellers" (the tab's own request: star true / false, verified), reads each seller's cue
card (GET company/cue/card) and returns the first seller that fits and that no other role took in
this run. The visible part of the flow - Sellers > tab > search the S-id > Actions "View" - is done
by AdminSellerCueCardPage.open_seller.

Read-only: list and cue card reads with the saved admin session's token, plus a completed-call
lookup for roles where a completed seller call would change the result. Nothing is written.
Picks are remembered for the run, so every case of a role works on the same seller (S1-01..S1-07
all use one "F-ready"); a later run picks again and naturally skips sellers an earlier run used up
(a starred F-ready is no longer in "Non Star Sellers", an uploaded teaser no longer fits "F-star").
"""
import json
import os
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import urllib.request

import pytest

from config import settings

# python.org's macOS Python ships with no CA certificates until "Install Certificates.command" is run,
# so every API call fails with CERTIFICATE_VERIFY_FAILED. Use certifi's bundle when it is installed.
try:
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL = ssl.create_default_context()

FUNDING, ACQUISITION = "funding", "acquisition"
# How many sellers of a tab the picker may read before giving up on a role (DD_SSF_SCAN_LIMIT).
SCAN_LIMIT = int(os.getenv("DD_SSF_SCAN_LIMIT", "300"))
PAGE_SIZE = 50
WORKERS = 8   # cue cards read in parallel while scanning a page of the list


def _star(s):
    return s["star"] is True


def _non_star(s):
    return s["star"] is False   # the "Non Star Sellers" tab lists star == false only


# role -> (tab is star?, fits(facts), needs no completed seller call)
ROLES = {
    # non-star roles ("Non Star Sellers" tab)
    "F-ready": (False, lambda s: s["objective"] == FUNDING and s["hl"] >= 3 and s["deck"] and not s["teaser"], False),
    "F-nodeck": (False, lambda s: s["objective"] == FUNDING and s["hl"] >= 3 and not s["deck"], True),
    "F-empty": (False, lambda s: s["objective"] == FUNDING and s["hl"] < 3 and not s["deck"] and not s["mis"], True),
    "F-short": (False, lambda s: s["objective"] == FUNDING and s["deck"] and s["memo_n"] >= 3 and s["hl"] < 3, False),
    "F-open": (False, lambda s: s["objective"] == FUNDING and s["open"] and s["hl"] >= 3 and s["deck"] and not s["teaser"], False),
    "A-ready": (False, lambda s: s["objective"] == ACQUISITION and s["hl"] >= 3 and s["teaser"] and not s["deck"], False),
    "A-noteaser": (False, lambda s: s["objective"] == ACQUISITION and s["hl"] >= 3 and not s["teaser"], False),
    "A-empty": (False, lambda s: s["objective"] == ACQUISITION and s["hl"] < 3 and not s["teaser"], False),
    "F-mis": (False, lambda s: s["objective"] == FUNDING and s["hl"] >= 3 and s["deck"] and s["mis"] and not s["teaser"], False),
    "F-nomis": (False, lambda s: s["objective"] == FUNDING and s["hl"] >= 3 and s["deck"] and not s["mis"], True),
    "F-mis-nodeck": (False, lambda s: s["objective"] == FUNDING and s["hl"] >= 3 and s["mis"] and not s["deck"], False),
    "A-biz-nomis": (False, lambda s: s["objective"] == ACQUISITION and s["hl"] >= 3 and s["teaser"] and not s["mis"], True),
    "A-biz-mis": (False, lambda s: s["objective"] == ACQUISITION and s["hl"] >= 3 and s["teaser"] and s["mis"], False),
    "F-del": (False, lambda s: s["objective"] == FUNDING and s["hl"] >= 3 and s["deck"] and not s["teaser"], False),
    "Nonstar-funding": (False, lambda s: s["objective"] == FUNDING, False),
    # star roles ("Star Sellers" tab)
    "F-star": (True, lambda s: s["objective"] == FUNDING and not s["teaser"], False),
    "F-star-biz": (True, lambda s: s["objective"] == FUNDING and not s["teaser"], False),
    "A-star": (True, lambda s: s["objective"] == ACQUISITION and s["teaser"] and not s["deck"], False),
    "F-star-del": (True, lambda s: s["objective"] == FUNDING and s["deck"], False),
}

# Why some sellers can't be found by browsing: their state can't be read from the cue card.
BLOCKED = {
    "F-NOCONSENT": "where the pitch deck consent setting is turned off is not known",
    "F-CALL": "how a 1-on-1 seller call is marked completed on QA is not known (needs a recipe from dev)",
    "F-DEALCALL": "how to give a seller only a buyer deal call on QA is not known (needs a recipe from dev)",
    "F-CANCELLED": "how a 1-on-1 seller call is cancelled on QA is not known (needs a recipe from dev)",
    "F-SCHEDULED": "a seller with only a scheduled, not completed 1-on-1 call must be set up by hand",
    "L-STAR": "a legacy star (funding, highlights, no pitch deck) must be starred BEFORE the release reaches QA",
}

_FACTS = {}       # uid -> facts, for this run
# The login the picker browses as: the same one the test runs as, so it only picks sellers that
# login can see (a biz user sees only their own sellers). Set by browse_as(); admin by default.
_LOGIN = ["admin"]
_BY_LOGIN = {}    # login -> that login's picks and scan progress, for this run


def browse_as(login):
    """Browse as `login` ("admin" / "biz_user") from now on; each login keeps its own picks."""
    _LOGIN[0] = login


def _mine():
    return _BY_LOGIN.setdefault(_LOGIN[0], {
        "picked": {},                       # role -> uid
        "taken": set(),                     # uids given to a non-star role (one seller per role)
        "scanned": {True: [], False: []},   # tab -> uids read so far, in list order
        "next_page": {True: 1, False: 1},
        "exhausted": {True: False, False: False},
        "not_found": {},                    # role -> skip message, so later cases of it skip at once
        "token": None,
    })


# ---------------------------------------------------------------- HTTP (read-only)

def _token():
    mine = _mine()
    if not mine["token"]:
        login = _LOGIN[0]
        path = {"admin": settings.admin_state, "biz_user": settings.biz_user_state}[login]
        if not path.exists():
            pytest.skip(f"no {login} session at {path}: python scripts/save_auth_state.py {login}")
        state = json.loads(path.read_text())
        value = next((item["value"] for origin in state.get("origins", [])
                      for item in origin.get("localStorage", []) if item["name"] == "authToken"), None)
        if not value:
            pytest.skip(f"no authToken in {path}; save the {login} session again")
        mine["token"] = value.strip('"')
    return mine["token"]


def _call(path, body=None, soft=False):
    req = urllib.request.Request(settings.api_url + path, method="POST" if body is not None else "GET",
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", _token())
    req.add_header("sessionid", _token())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30, context=_SSL) as res:
            return json.loads(res.read().decode() or "{}")
    except urllib.error.HTTPError as error:
        if soft:
            return None
        # A 5xx here means the backend itself is down (the admin Sellers page fails the same way),
        # not a test problem; say so in one line instead of a urllib traceback per test.
        pytest.fail(f"backend error {error.code} on {settings.api_url}{path.split('?')[0]} while browsing "
                    f"for a seller" + (" - the backend looks down; open Admin > Sellers to check, rerun later"
                                        if error.code >= 500 else " - is the admin session still valid?"),
                    pytrace=False)


def _list_body(star):
    """The request the "Star Sellers" / "Non Star Sellers" tab sends (TabModels: star eq true / false)."""
    return {
        "searchCriteriaList": [{"filterKey": "star", "operation": "eq", "value": star},
                               {"filterKey": "verificationStatus", "operation": "in", "valueList": ["verified"]}],
        "dataOption": "all",
        "sortCriteria": {"direction": "DESC", "fieldName": "lastActivity", "value": "Recently active"},
    }


def _facts(card):
    memo = [m for m in (card.get("memo") or []) if isinstance(m, str)]
    docs = (card.get("docData") or {}).get("userDocMap") or {}
    star = (card.get("companyQualifiedData") or {}).get("star")
    return {
        "uid": card["companyId"],
        "id": card.get("id"),
        "sid": f"S{card.get('id')}",
        "objective": card.get("objective"),
        "open": bool(card.get("openToOtherObjective")),
        "star": True if star in (True, "true") else False if star in (False, "false") else None,
        "memo_n": len(memo),
        "hl": sum(1 for m in memo if len(m.strip()) >= 50),   # MIN_HIGHLIGHT_LENGTH
        "deck": bool(docs.get("pitch_deck")),
        "teaser": bool(docs.get("investment_teaser")),
        "mis": bool(docs.get("mis")),
    }


def describe(uid, soft=False):
    """Facts of one seller (S-id, star, objective, documents), read fresh from its cue card.
    soft: None instead of failing when the cue card can't be read (one bad seller while scanning)."""
    data = (_call(f"company/cue/card?companyId={uid}", soft=soft) or {}).get("data") or {}
    if not data.get("companyId"):
        if soft:
            return None
        raise AssertionError(f"no cue card for seller {uid}")
    _FACTS[uid] = _facts(data)
    return _FACTS[uid]


def _progress(text):
    """One line on the terminal while scanning (pytest captures stdout), so a long scan isn't mistaken for a hang."""
    sys.__stderr__.write(f"\r  [ssf] {text}".ljust(90))
    sys.__stderr__.flush()


def _completed_seller_calls(facts):
    body = {"searchCriteriaList": [{"filterKey": "referenceId", "operation": "eq", "value": facts["id"]},
                                   {"filterKey": "referenceType", "operation": "eq", "value": "seller"}],
            "dataOption": "all", "sortCriteria": {"direction": "ASC", "fieldName": "dateTime", "value": "Upcoming"},
            "criteriaMap": {"meetingStatus": "completed"}}
    return ((_call("meeting/query?page=1&size=1", body) or {}).get("data") or {}).get("totalElements") or 0


def _scan(star):
    """Yield the tab's sellers in list order: first the ones read already, then further pages."""
    mine = _mine()
    i = 0
    while True:
        seen = mine["scanned"][star]
        if i < len(seen):
            yield _FACTS[seen[i]]
            i += 1
            continue
        if mine["exhausted"][star] or len(seen) >= SCAN_LIMIT:
            return
        rows = ((_call(f"buyer/browse?page={mine['next_page'][star]}&size={PAGE_SIZE}", _list_body(star)) or {})
                .get("data") or {}).get("elements") or []
        mine["next_page"][star] += 1
        if not rows:
            mine["exhausted"][star] = True
            return
        with ThreadPoolExecutor(WORKERS) as pool:
            for facts in pool.map(lambda row: describe(row["companyId"], soft=True), rows):
                if facts:
                    seen.append(facts["uid"])
        _progress(f"read {len(seen)} sellers of \"{'Star' if star else 'Non Star'} Sellers\"")


# ---------------------------------------------------------------- picking

def pick(role, case, exclude=()):
    """The uid of a seller that fits `role`, found by browsing its tab. Skips when none fits."""
    key = role.upper()
    if key in BLOCKED:
        pytest.skip(f"{case}: no {role} seller can be browsed for (BLOCKED: {BLOCKED[key]})")
    if role not in ROLES:
        raise KeyError(f"unknown SSF seller role {role!r}")
    mine = _mine()
    if role in mine["picked"] and mine["picked"][role] not in exclude:
        return mine["picked"][role]
    if role in mine["not_found"]:
        pytest.skip(f"{case}: {mine['not_found'][role]}")

    star, fits, needs_no_call = ROLES[role]
    tab = "Star Sellers" if star else "Non Star Sellers"
    _progress(f"{case}: looking for a {role} seller in \"{tab}\"...")
    for facts in _scan(star):
        uid = facts["uid"]
        if uid in exclude or (not star and uid in mine["taken"]):
            continue
        if (facts["star"] is not star) or not fits(facts):
            continue
        if needs_no_call and _completed_seller_calls(facts):
            continue
        mine["picked"][role] = uid
        if not star:
            mine["taken"].add(uid)
        return uid
    mine["not_found"][role] = (f"no {role} seller found in the first {len(mine['scanned'][star])} of "
                               f"\"{tab}\" as {_LOGIN[0]} (raise DD_SSF_SCAN_LIMIT to look further)")
    pytest.skip(f"{case}: {mine['not_found'][role]}")


def forget(role):
    """Drop the run's pick for `role`, so the next case of that role browses for a fresh seller."""
    _mine()["picked"].pop(role, None)
