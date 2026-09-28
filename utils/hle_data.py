"""Test data for hot-lead-engagement-visibility, read from DD_HLE_* in .env (see .env.example).

Every value is keyed by the test case it feeds, e.g.
    DD_HLE_POC_LINKS=S7-01:https://.../buyer/deeplink?listingUid=..&pocUid=..,S7-03:<POC A>|<POC B>
    DD_HLE_LEAD_NAMES=S7-01:Acme Capital,S7-03:Beta Partners
A missing value skips the case, naming the variable; a value an earlier run used (run_state/hle.json)
skips it too, because that lead is no longer fresh.
"""
import pytest

from config import settings
from utils.run_state import hle_used


def _by_case(raw):
    """"S7-01:value,S8-01:value" -> {"S7-01": "value"}. Only the first colon splits, so URLs survive."""
    pairs = {}
    for part in (raw or "").split(","):
        if ":" in part:
            key, value = part.split(":", 1)
            if key.strip() and value.strip():
                pairs[key.strip().upper()] = value.strip()
    return pairs


def lead_name(case):
    name = _by_case(settings.hle_lead_names).get(case)
    if not name:
        pytest.skip(f"{case}: set DD_HLE_LEAD_NAMES={case}:<the lead's name on Investor Leads>")
    return name


def poc_links(case, count=1):
    """The case's first `count` POC deep links (POC A first), all unused."""
    links = [link.strip() for link in _by_case(settings.hle_poc_links).get(case, "").split("|") if link.strip()]
    if len(links) < count:
        pytest.skip(f"{case}: set DD_HLE_POC_LINKS={case}:" + "|".join(f"<POC {c} link>" for c in "AB"[:count])
                    + f" ({count} POC deep link(s) of one never-hot buyer lead)")
    for link in links[:count]:
        _require_unused(case, link, "DD_HLE_POC_LINKS")
    return links[:count]


def teaser_link(case):
    link = settings.hle_teaser_unlocked_link.strip()
    if not link:
        pytest.skip(f"{case}: set DD_HLE_TEASER_UNLOCKED_LINK (an unlocked investment teaser a never-hot lead's POC can open)")
    _require_unused(case, link, "DD_HLE_TEASER_UNLOCKED_LINK")
    return link


def fresh_company_uid(case):
    used = hle_used()
    uids = [u.strip() for u in settings.hle_fresh_company_uids.split(",") if u.strip()]
    fresh = [u for u in uids if u not in used]
    if not fresh:
        pytest.skip(f"{case}: set DD_HLE_FRESH_COMPANY_UIDS to cue card uids the DD_HLE_BUYER_STATE buyer "
                    f"has not expressed interest in" + (" (all listed ones are used)" if uids else ""))
    return fresh[0]


def require_hle_buyer_state(case):
    if not settings.hle_buyer_state.exists():
        pytest.skip(f"{case}: no dedicated HLE buyer session at {settings.hle_buyer_state}; set DD_HLE_BUYER_STATE "
                    f"and run: python scripts/save_auth_state.py hle_buyer")


def _require_unused(case, value, variable):
    record = hle_used().get(value)
    if record:
        pytest.skip(f"{case}: {variable} value was already used by {record.get('case')} on {record.get('at')}; "
                    f"give {case} a fresh never-hot lead")
