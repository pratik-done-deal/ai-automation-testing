"""Find the existing automation a change can affect. Deterministic: no AI, no Figma, no network.

Signals (any mix):
    --feature <slug>     a new feature's footprint from specs/features/<slug>/feature.yml
    --src PATH           app files or folders the change touches (repeatable)
    --diff A...B         add the src/ files changed in a git range, e.g. main...feature/x
    --endpoint E         API paths, e.g. deal/capture/interest/update
    --route R            app routes, e.g. /deals/:companyId?
    --copy TEXT          UI copy the change removes or rewords (the OLD text)

    python -m impact.find --feature seller-bulk-accept
    python -m impact.find --src src/Container/SellerDealsAndInvestors/ --copy "Accept investor interest?"

Matches, each with the reason it matched:
  entries       a module or feature whose footprint overlaps (src, endpoint, route)
  requirements  the module spec or analysis cites a touched file, or a matched test names it
  tests         a test reaching a symbol whose literals hold a touched endpoint, route or copy text
  symbols       locators, page objects, constants and utils holding those literals
  design steps  saved Figma refs (flow steps) showing a touched copy text

A match is a candidate, not a verdict: impact-analyzer decides update / superseded / still valid.
The new feature's own tests (its req_prefix) are left out.
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))

from impact.index import SuiteIndex  # noqa: E402
from paths import APP_ROOT, SPECS  # noqa: E402
from utils.registry import load_registry  # noqa: E402

_CODE_REF = re.compile(r"`([\w./-]+\.(?:jsx?|tsx?))(?::[\d,\- ]+)?`")


def _norm_src(path):
    return str(path).strip().lstrip("./").removeprefix(str(APP_ROOT) + "/")


def _src_overlap(a, b):
    """Same file, or one is a folder (ending in /) containing the other."""
    a, b = _norm_src(a), _norm_src(b)
    return a == b or (a.endswith("/") and b.startswith(a)) or (b.endswith("/") and a.startswith(b))


def _route_prefix(route):
    return route.split(":", 1)[0].rstrip("/?") or "/"


def _endpoint_re(endpoint):
    return re.compile(r"(?<![\w-])" + re.escape(endpoint.strip("/")) + r"(?![\w/-])")


def _route_re(route):
    return re.compile(r"(?<![\w-])" + re.escape(_route_prefix(route)) + r"(?![\w-])")


def _copy_hit(copy, literal):
    c, lit = copy.lower().strip(), literal.lower().strip()
    return c in lit or (len(lit) >= 12 and lit in c)


def _requirement_evidence(entry):
    """{requirement id: {cited app files}} from a module spec or a feature analysis table."""
    spec = entry.dir / "module.md" if entry.kind == "module" else None
    if spec is None:
        analysis = entry.docs.get("analysis")
        spec = SPECS / analysis if analysis else None
    if spec is None or not spec.exists() or not entry.req_prefix:
        return {}
    evidence = {}
    row_re = re.compile(rf"^\|\s*({re.escape(entry.req_prefix)}-\d+)\s*\|")
    for line in spec.read_text().splitlines():
        m = row_re.match(line)
        if m:
            evidence.setdefault(m.group(1), set()).update(_CODE_REF.findall(line))
    return evidence


def _flow_texts(entry):
    """{step id: [texts in its saved spec.json]} for an entry with saved Figma refs."""
    refs = entry.dir / "refs"
    out = {}
    if not refs.exists():
        return out
    for spec in sorted(refs.glob("*.spec.json")):
        texts, stack = [], [json.loads(spec.read_text())]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if node.get("type") == "TEXT" and (node.get("text") or "").strip():
                    texts.append(node["text"].strip())
                stack.extend(node.get("children") or [])
        out[spec.name.removesuffix(".spec.json")] = texts
    return out


def _git_diff_src(rng):
    result = subprocess.run(["git", "diff", "--name-only", rng, "--", "src/"], cwd=APP_ROOT,
                            capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"git diff {rng} failed: {result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line]


def find(src=(), endpoints=(), routes=(), copy=(), exclude_prefix=None, exclude_slug=None):
    entries = {s: e for s, e in load_registry().items() if s != exclude_slug}
    index = SuiteIndex()
    result = {"entries": defaultdict(list), "requirements": defaultdict(list), "tests": defaultdict(list),
              "symbols": defaultdict(list), "design_steps": defaultdict(list)}

    # 1. footprint overlap, and requirements whose spec evidence cites a touched file
    for slug, entry in entries.items():
        fp = entry.footprint
        for s in src:
            for own in fp.get("src", []):
                if _src_overlap(s, own):
                    result["entries"][slug].append(f"src {_norm_src(s)} ~ {own}")
        for e in endpoints:
            if e.strip("/") in (x.strip("/") for x in fp.get("endpoints", [])):
                result["entries"][slug].append(f"endpoint {e}")
        for r in routes:
            if _route_prefix(r) in (_route_prefix(x) for x in fp.get("routes", [])):
                result["entries"][slug].append(f"route {r}")
        for req, cited in _requirement_evidence(entry).items():
            for s in src:
                name = _norm_src(s)
                for c in cited:
                    # a cited "Folder/index.js" also matches a touched folder ".../Folder/"
                    in_folder = name.endswith("/") and "/" in c and f"/{c.split('/')[0]}/" in f"/{name}"
                    if name.endswith(c) or in_folder:
                        result["requirements"][req].append(f"spec cites {c}, touched by {name}")

    # 2. suite symbols holding a touched endpoint / route / copy
    patterns = ([(f"endpoint {e}", _endpoint_re(e).search) for e in endpoints]
                + [(f"route {r}", _route_re(r).search) for r in routes]
                + [(f'copy "{c}"', lambda lit, c=c: _copy_hit(c, lit)) for c in copy])
    hit_symbols = defaultdict(set)
    for signal, match in patterns:
        for qualname, symbol in index.symbols.items():
            if any(match(lit) for lit in symbol.literals):
                hit_symbols[qualname].add(signal)
    for qualname, signals in hit_symbols.items():
        symbol = index.symbols[qualname]
        if not qualname.startswith("test_cases."):
            result["symbols"][f"{qualname}  ({symbol.path}:{symbol.line})"].extend(sorted(signals))

    # 3. tests reaching those symbols
    for test in index.tests:
        if exclude_prefix and any(r.startswith(exclude_prefix + "-") for r in test.requirements):
            continue
        reached = index.reach(test)
        for qualname, signals in hit_symbols.items():
            if qualname in reached:
                via = " -> ".join(q.split(".")[-1] for q in reached[qualname][1:]) or "the test itself"
                for signal in sorted(signals):
                    result["tests"][test.nodeid].append(f"{signal} via {via}")
        if test.nodeid in result["tests"]:
            for req in test.requirements:
                result["requirements"][req].append(f"named by matched test {test.nodeid}")

    # 4. design refs showing a touched copy text
    for slug, entry in entries.items():
        for step, texts in _flow_texts(entry).items():
            for c in copy:
                if any(_copy_hit(c, t) for t in texts):
                    result["design_steps"][f"{slug}:{step}"].append(f'copy "{c}"')

    return {k: dict(v) for k, v in result.items()}, {t.nodeid: t for t in index.tests}


def _print_markdown(result, tests_meta):
    def section(title, rows, fmt):
        print(f"\n## {title} ({len(rows)})\n")
        if not rows:
            print("none")
            return
        for key in sorted(rows):
            print(fmt(key, rows[key]))

    def reasons(items, limit=4):
        unique = list(dict.fromkeys(items))
        more = f" (+{len(unique) - limit} more)" if len(unique) > limit else ""
        return "; ".join(unique[:limit]) + more

    section("Modules / features whose footprint overlaps", result["entries"],
            lambda k, v: f"- **{k}**: {reasons(v, 8)}")
    section("Requirements", result["requirements"], lambda k, v: f"- {k}: {reasons(v)}")
    section("Tests", result["tests"], lambda k, v: (
        f"- `{k}` [{', '.join(tests_meta[k].requirements) or 'no req id'}]"
        f" markers: {', '.join(sorted(tests_meta[k].markers))}\n    {reasons(v)}"))
    section("Suite symbols holding the touched literals", result["symbols"],
            lambda k, v: f"- `{k}`: {reasons(v)}")
    section("Design steps (saved Figma refs)", result["design_steps"], lambda k, v: f"- {k}: {reasons(v)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feature", help="new feature slug: use its footprint and leave its own tests out")
    parser.add_argument("--src", action="append", default=[])
    parser.add_argument("--diff", help="git range; adds the src/ files it changes")
    parser.add_argument("--endpoint", action="append", default=[])
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--copy", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    src, endpoints, routes = list(args.src), list(args.endpoint), list(args.route)
    prefix = None
    if args.feature:
        entry = load_registry().get(args.feature)
        if entry is None:
            sys.exit(f"No specs/features/{args.feature}/feature.yml")
        src += entry.footprint.get("src", [])
        endpoints += entry.footprint.get("endpoints", [])
        routes += entry.footprint.get("routes", [])
        prefix = entry.req_prefix or None
    if args.diff:
        src += _git_diff_src(args.diff)
    if not (src or endpoints or routes or args.copy):
        parser.error("give --feature or at least one of --src / --diff / --endpoint / --route / --copy")

    result, tests_meta = find(src, endpoints, routes, args.copy, exclude_prefix=prefix, exclude_slug=args.feature)
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print("# Impact candidates")
    print(f"\nsignals: {len(src)} src, {len(endpoints)} endpoints, {len(routes)} routes, {len(args.copy)} copy")
    _print_markdown(result, tests_meta)


if __name__ == "__main__":
    main()
