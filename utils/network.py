"""Response rewriting and mocking, so UI rules can be checked without changing any deal's state.

Playwright runs matching routes newest-first, so register the broad `rewrite_deal_rows` before
narrower ones such as `rewrite_seller_documents`.
"""
import json
import re


def rewrite_json(page, pattern, mutate):
    """Fetch the real response for `pattern` and fulfil it with `mutate(body)` applied in place."""

    def handler(route):
        if route.request.resource_type not in ("xhr", "fetch"):
            return route.fallback()
        response = route.fetch()
        try:
            body = response.json()
        except Exception:
            return route.fulfill(response=response)
        mutate(body)
        route.fulfill(response=response, body=json.dumps(body),
                      headers={**response.headers, "content-type": "application/json"})

    page.route(pattern, handler)


def mock_json(page, pattern, body, sent=None):
    """Answer `pattern` with `body` without hitting the backend; request JSON bodies go to `sent`."""

    def handler(route):
        if sent is not None:
            sent.append(route.request.post_data_json)
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    page.route(pattern, handler)


def success_body(data=None, message=None):
    body = {"status": "200", "data": data if data is not None else {}}
    if message:
        body["message"] = message
    return body


# ------------------------------------------------------------------ deals (deal/query rows)

def _each_deal(node, mutate):
    if isinstance(node, dict):
        if "dealStatus" in node:
            mutate(node)
        for value in node.values():
            _each_deal(value, mutate)
    elif isinstance(node, list):
        for value in node:
            _each_deal(value, mutate)


def rewrite_deal_rows(page, mutate):
    """Apply `mutate(deal_dict)` to every deal object in JSON API responses the page receives."""
    rewrite_json(page, "**/api/**", lambda body: _each_deal(body, mutate))


def with_requested_docs(doc_types):
    # deal/query carries requestedDocuments as plain strings (useIntroductionSetup.js:167).
    return lambda deal: deal.__setitem__("requestedDocuments", list(doc_types))


def without_requested_docs(deal):
    deal.pop("requestedDocuments", None)


def with_investor_note(text):
    # utils.getInvestorMessage reads deal.investorNote.description.
    return lambda deal: deal.__setitem__("investorNote", {"description": text})


# ------------------------------------------------------------------ seller data room (document/query)

def fake_doc(doc_type, n):
    return {"uid": f"automation-{doc_type}-{n}", "fileName": f"automation-{doc_type}-{n}.pdf", "docType": doc_type}


def fake_user_doc_map(files_per_type):
    """{doc_type: count} -> a document/query userDocMap with that many fake files per type."""
    return {doc_type: [fake_doc(doc_type, n) for n in range(1, count + 1)]
            for doc_type, count in files_per_type.items() if count}


def rewrite_seller_documents(page, files_per_type):
    """Replace the seller's data room as the Accept modal sees it (read-only: nothing is uploaded)."""
    user_doc_map = fake_user_doc_map(files_per_type)

    def mutate(body):
        body.setdefault("data", {})["userDocMap"] = user_doc_map

    rewrite_json(page, "**/document/query", mutate)
    return user_doc_map


# ------------------------------------------------------------------ seller slots (meeting/slots/seller)

FAKE_SLOTS = [
    {"id": 910001, "possibleDate": "2030-01-15", "startTime": [11, 0], "endTime": [11, 30]},
    {"id": 910002, "possibleDate": "2030-01-16", "startTime": [15, 0], "endTime": [15, 30]},
]


def mock_seller_slots(page, slots=FAKE_SLOTS):
    body = success_body({"meetingBookingRequired": bool(slots), "possibleMeetingList": list(slots)})
    mock_json(page, "**/meeting/slots/seller", body)


# ------------------------------------------------------------------ uploads (document/user/upload)

def mock_upload(page, user_doc_map, sent):
    """Pretend document/user/upload stored the file: add it to the fake data room and return its uid.

    `sent` collects the docType each upload carried (read from the multipart docData JSON).
    """

    def handler(route):
        body = route.request.post_data_buffer or b""
        match = re.search(rb'"docType"\s*:\s*"([^"]+)"', body)
        doc_type = match.group(1).decode() if match else ""
        sent.append(doc_type)
        doc = fake_doc(doc_type, len(user_doc_map.get(doc_type, [])) + 1)
        user_doc_map.setdefault(doc_type, []).append(doc)
        route.fulfill(status=200, content_type="application/json", body=json.dumps(success_body(doc["uid"])))

    page.route("**/document/user/upload", handler)
