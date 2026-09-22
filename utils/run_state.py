"""Hands deal details from phase 1 (buyer) to phase 2 (seller), which runs later with the seller's session.

run_state/phase1.json maps cue card uid -> {title, deal_id, company_id, requested, note}.
A record with `requested: []` is the "closed without a request" deal (DR-13/18/31/47).
"""
import json

import pytest

from config import ROOT, settings

PHASE1_FILE = ROOT / "run_state" / "phase1.json"


def load_all() -> dict:
    return json.loads(PHASE1_FILE.read_text()) if PHASE1_FILE.exists() else {}


def save_record(uid: str, record: dict):
    PHASE1_FILE.parent.mkdir(parents=True, exist_ok=True)
    records = load_all()
    records[uid] = record
    PHASE1_FILE.write_text(json.dumps(records, indent=2))


def has_request(record) -> bool:
    return bool(record.get("requested"))


def latest(with_request: bool):
    """The newest phase 1 record of that kind (records are written in run order), or None."""
    matching = [{"uid": uid, **rec} for uid, rec in load_all().items() if has_request(rec) == with_request]
    return matching[-1] if matching else None


def phase2_record(with_request=True) -> dict:
    """The phase 1 record for the seller whose session is saved now.

    DD_PHASE2_SELLER_CUE_CARD_UID picks it. Without it, the only record of the wanted kind is used.
    """
    records = load_all()
    if not records:
        pytest.skip(f"No phase 1 results at {PHASE1_FILE}; run `pytest -m phase1` first")
    kind = "with a document request" if with_request else "closed without a request"
    uid = settings.phase2_seller_cue_card_uid
    if uid:
        if uid not in records:
            pytest.skip(f"{uid} is not in {PHASE1_FILE}; phase 1 covered: {', '.join(records)}")
        if has_request(records[uid]) != with_request:
            pytest.skip(f"DD_PHASE2_SELLER_CUE_CARD_UID={uid} is not the deal {kind}")
        return {"uid": uid, **records[uid]}

    candidates = [u for u, rec in records.items() if has_request(rec) == with_request]
    if not candidates:
        pytest.skip(f"Phase 1 recorded no deal {kind}")
    if len(candidates) > 1 or not with_request:
        # The no-request deal belongs to a different seller, so it always needs an explicit uid.
        pytest.skip(f"Set DD_PHASE2_SELLER_CUE_CARD_UID to the deal {kind} whose seller is logged in "
                    f"(candidates: {', '.join(candidates)})")
    return {"uid": candidates[0], **records[candidates[0]]}
