"""Hands deal details from phase 1 (buyer) to phase 2 (seller), which runs later with the seller's session."""
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


def phase2_record() -> dict:
    """The phase 1 record for the seller whose session is saved now."""
    records = load_all()
    if not records:
        pytest.skip(f"No phase 1 results at {PHASE1_FILE}; run `pytest -m phase1` first")
    uid = settings.phase2_seller_cue_card_uid
    if not uid:
        if len(records) > 1:
            pytest.skip("Phase 1 covered several sellers; set DD_PHASE2_SELLER_CUE_CARD_UID to the one you're logged in as")
        uid = next(iter(records))
    if uid not in records:
        pytest.skip(f"{uid} is not in {PHASE1_FILE}; phase 1 covered: {', '.join(records)}")
    return {"uid": uid, **records[uid]}
