"""Coverage report: what the registry says exists vs what the suite actually tests. No AI.

    python -m impact.coverage              # table per module / feature
    python -m impact.coverage --gaps       # only requirements with no live test
    python -m impact.coverage --out specs/COVERAGE.md

Requirement states:
  live         at least one test that runs today
  pending      only tests marked pending_feature (waiting for a feature to ship)
  superseded   only tests marked superseded_by a shipped feature (kept for history)
  xfail        only tests marked not_implemented_yet
  manual       the spec marks it manual (emails, schedulers, AI summaries, metrics)
  uncovered    no test names it
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))

from impact.index import SuiteIndex  # noqa: E402
from paths import SPECS  # noqa: E402
from utils.registry import entry_for_requirement, load_registry  # noqa: E402

STATES = ("live", "pending", "superseded", "xfail", "manual", "uncovered")


def _spec_requirements(entry):
    """[(id, one-line text, manual?)] from the entry's requirement table, in file order."""
    spec = entry.dir / "module.md"
    if not spec.exists():
        analysis = entry.docs.get("analysis")
        spec = SPECS / analysis if analysis else None
    if spec is None or not spec.exists() or not entry.req_prefix:
        return []
    row_re = re.compile(rf"^\|\s*({re.escape(entry.req_prefix)}-\d+)\s*\|\s*([^|]*)\|(.*)$")
    out, seen = [], set()
    for line in spec.read_text().splitlines():
        m = row_re.match(line)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append((m.group(1), m.group(2).strip(), "manual" in m.group(3).lower()))
    return out


def _state(tests, manual):
    if not tests:
        return "manual" if manual else "uncovered"
    for test in tests:
        markers = test.markers
        if not ({"pending_feature", "superseded_by", "not_implemented_yet", "xfail"} & set(markers)):
            return "live"
    if any("pending_feature" in t.markers for t in tests):
        return "pending"
    if any("superseded_by" in t.markers for t in tests):
        return "superseded"
    return "xfail"


def report(gaps_only=False):
    index = SuiteIndex()
    registry = load_registry()
    lines = ["# Coverage", ""]
    totals = Counter()

    for slug, entry in sorted(registry.items(), key=lambda kv: (kv[1].kind, kv[0])):
        requirements = _spec_requirements(entry)
        rows, counts = [], Counter()
        for req, text, manual in requirements:
            tests = index.tests_for_requirement(req)
            state = _state(tests, manual)
            counts[state] += 1
            totals[state] += 1
            if gaps_only and state not in ("uncovered", "pending"):
                continue
            nodes = "<br>".join(f"`{t.nodeid}`" for t in tests) or "—"
            rows.append(f"| {req} | {text[:80]} | {state} | {nodes} |")
        summary = ", ".join(f"{counts[s]} {s}" for s in STATES if counts[s])
        lines += [f"## {entry.name} (`{slug}`, {entry.kind}, {entry.status})", "",
                  f"{len(requirements)} requirements: {summary or 'none in the spec'}", ""]
        if rows:
            lines += ["| ID | Requirement | State | Tests |", "|---|---|---|---|", *rows, ""]

    unlinked = [t.nodeid for t in index.tests if not t.requirements]
    lines += ["## Totals", "",
              ", ".join(f"{totals[s]} {s}" for s in STATES if totals[s]) or "no requirements registered",
              "", f"Tests naming no requirement id: {len(unlinked)}"]
    lines += [f"- `{n}`" for n in unlinked]

    orphans = sorted({r for t in index.tests for r in t.requirements if entry_for_requirement(r) is None})
    if orphans:
        lines += ["", "## Requirement ids with no registry entry", "",
                  "These prefixes are in tests but in no module.yml / feature.yml:", ""]
        lines += [f"- {r}" for r in orphans]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gaps", action="store_true", help="only uncovered and pending requirements")
    parser.add_argument("--out", help="write to this path (relative to automation/) instead of stdout")
    args = parser.parse_args()
    text = report(gaps_only=args.gaps)
    if args.out:
        path = AUTOMATION / args.out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n")
        print(f"wrote {path.relative_to(AUTOMATION)}")
    else:
        print(text)


if __name__ == "__main__":
    main()
