"""Response rewriting so UI rules can be checked against any existing deal without creating new ones."""
import json


def _rewrite(node, mutate):
    if isinstance(node, dict):
        if "dealStatus" in node:
            mutate(node)
        for value in node.values():
            _rewrite(value, mutate)
    elif isinstance(node, list):
        for value in node:
            _rewrite(value, mutate)


def rewrite_deal_rows(page, mutate):
    """Apply `mutate(deal_dict)` to every deal object in JSON API responses the page receives."""

    def handler(route):
        if route.request.resource_type not in ("xhr", "fetch"):
            return route.continue_()
        response = route.fetch()
        try:
            body = response.json()
        except Exception:
            return route.fulfill(response=response)
        _rewrite(body, mutate)
        route.fulfill(response=response, body=json.dumps(body), headers={**response.headers, "content-type": "application/json"})

    page.route("**/api/**", handler)


def with_requested_docs(doc_types):
    return lambda deal: deal.__setitem__("requestedDocuments", list(doc_types))


def without_requested_docs(deal):
    deal.pop("requestedDocuments", None)
