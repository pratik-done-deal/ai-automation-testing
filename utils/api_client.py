"""Thin API client that reuses a saved browser session's auth token.

The web app sends the raw `authToken` from localStorage as both `Authorization`
and `sessionid` (no `Bearer ` prefix) - see src/utils/apiService.js.
"""
import json
from pathlib import Path

API_SUCCESS_CODE = "200"


def token_from_state(state_path: Path) -> str:
    state = json.loads(Path(state_path).read_text())
    for origin in state.get("origins", []):
        for item in origin.get("localStorage", []):
            if item["name"] == "authToken":
                return item["value"]
    raise RuntimeError(f"No authToken in {state_path}; re-run scripts/save_auth_state.py")


class DoneDealApi:
    def __init__(self, playwright, base_url: str, state_path: Path):
        token = token_from_state(state_path)
        self._ctx = playwright.request.new_context(
            base_url=base_url,
            extra_http_headers={"Authorization": token, "sessionid": token},
        )

    def dispose(self):
        self._ctx.dispose()

    @staticmethod
    def _unwrap(res):
        try:
            payload = res.json()
        except Exception:
            payload = {"raw": res.text()}
        return res.status, payload

    def post(self, path: str, body: dict):
        return self._unwrap(self._ctx.post(path, data=json.dumps(body), headers={"Content-Type": "application/json"}))

    def upload_document(self, file_path: Path, doc_type: str, category="company"):
        """Same multipart shape as the app's uploadDocument saga (file + docData JSON)."""
        file_path = Path(file_path)
        return self._unwrap(self._ctx.post("document/user/upload", multipart={
            "file": {"name": file_path.name, "mimeType": "application/pdf", "buffer": file_path.read_bytes()},
            "docData": json.dumps({"userDocArray": [{"docType": doc_type, "category": category}]}),
        }))

    # --- endpoints used by the document request feature (src/config/endpoint.js) ---

    def capture_interest(self, company_id, meet_slots, notes="", stage="express_interest", **extra):
        return self.post("deal/capture/interest", {
            "companyId": company_id,
            "meetSlots": meet_slots,
            "stage": stage,
            "interactionNotes": notes,
            "teamMembers": [],
            "openToFunding": True,
            "openToAcquisition": False,
            **extra,
        })

    def update_interest(self, company_id, notes="", team_members=None, requested_doc_types=None):
        body = {"companyId": company_id, "interactionNotes": notes, "teamMembers": team_members or []}
        if requested_doc_types is not None:
            body["requestedDocTypes"] = requested_doc_types
        return self.post("deal/capture/interest/update", body)


def is_success(payload) -> bool:
    return str(payload.get("status")) == API_SUCCESS_CODE


def find_key(obj, key):
    """Depth-first search for the first value stored under `key` in a JSON tree."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_key(value, key)
            if found is not None:
                return found
    return None


def requested_types(requested_documents):
    return [d.get("docType") if isinstance(d, dict) else d for d in (requested_documents or [])]
