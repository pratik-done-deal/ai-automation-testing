"""Inventory of the application's routes: the denominator for coverage. Static, no AI.

Parses the <Route> declarations under APP_ROOT/src/Routes and src/RoutesStructure, resolves each
route's rendering component to the file that imports it, and says whether a module spec already
covers it (specs/modules/*/module.yml footprint).

    python -m impact.app_map                 # every route, grouped by role area
    python -m impact.app_map --uncovered     # only routes no module spec claims
    python -m impact.app_map --out specs/modules/INVENTORY.md
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))

from impact.find import _route_prefix  # noqa: E402
from paths import APP_ROOT  # noqa: E402
from utils.registry import modules  # noqa: E402

ROUTE_DIRS = ("src/Routes", "src/RoutesStructure")
ROUTE_RE = re.compile(r"<Route\b[^>]*?\bpath=['\"{]([^'\"}]+)['\"}]", re.S)
COMPONENT_RE = re.compile(r"<([A-Z][A-Za-z0-9_]*)\s*/?>")
IMPORT_RE = re.compile(r"""import\s+(?:{[^}]*\b(\w+)\b[^}]*}|(\w+))\s+from\s+['"]([^'"]+)['"]""")
LAZY_RE = re.compile(r"""(?:const|let)\s+(\w+)\s*=\s*(?:React\.)?lazy\(\s*\(\)\s*=>\s*import\(\s*['"]([^'"]+)['"]""")

AREA_BY_PREFIX = (("/admin", "admin"), ("/buyer", "buyer"))
# Wrappers between <Route> and the screen: guards, trackers, layouts.
SKIP_COMPONENTS = {"ProtectedRoute", "NonProtectedRoute", "WithTracker", "Suspense", "Navigate",
                   "Outlet", "Route", "Routes", "React", "Fragment", "ErrorBoundary"}
SKIP_SUFFIXES = ("AuthGuard", "Guard", "Protect", "Layout", "Wrapper", "Provider")


def _imports(text):
    """{local name: import path} for both plain and lazy imports."""
    out = {name: path for name, path in LAZY_RE.findall(text)}
    for named, default, path in IMPORT_RE.findall(text):
        out.setdefault(named or default, path)
    return out


def _route_files():
    for folder in ROUTE_DIRS:
        base = APP_ROOT / folder
        if base.exists():
            yield from sorted(p for p in base.rglob("*.js") if "node_modules" not in p.parts)


def _base_path(file_path, text):
    """Best guess at the prefix a file's routes hang under, from its parent <Route path=...>."""
    name = file_path.name
    if "Admin" in name:
        return "/admin"
    if "Buyer" in name:
        return "/buyer"
    if "Seller" in name or name == "index.js":
        return ""
    return "" if "path=\"/\"" in text else ""


def routes():
    """[(route, area, component, file)] for every <Route path=...> in the app."""
    found = []
    for path in _route_files():
        text = path.read_text(errors="ignore")
        imports = _imports(text)
        base = _base_path(path, text)
        for match in ROUTE_RE.finditer(text):
            raw = match.group(1).strip()
            if raw in ("*",):
                continue
            route = raw if raw.startswith("/") else f"{base}/{raw}".replace("//", "/")
            tail = text[match.end():match.end() + 1500]
            component = next((c for c in COMPONENT_RE.findall(tail)
                              if c not in SKIP_COMPONENTS and not c.endswith(SKIP_SUFFIXES)), "")
            area = next((a for prefix, a in AREA_BY_PREFIX if route.startswith(prefix)), "seller/public")
            found.append((route, area, component, imports.get(component, ""),
                          str(path.relative_to(APP_ROOT))))
    return sorted(set(found))


def covered_routes():
    """{route prefix: module slug} from the module specs' footprints."""
    out = {}
    for slug, entry in modules().items():
        for route in entry.footprint.get("routes", []):
            out[_route_prefix(route)] = slug
    return out


def report(uncovered_only=False):
    covered = covered_routes()
    by_area = defaultdict(list)
    for route, area, component, source, file in routes():
        slug = covered.get(_route_prefix(route))
        if uncovered_only and slug:
            continue
        by_area[area].append((route, component, source or file, slug))

    lines = ["# Application route inventory", "",
             f"Read from {APP_ROOT}/src. A route counts as covered when a module spec's footprint "
             "lists it.", ""]
    total = sum(len(v) for v in by_area.values())
    lines += [f"{total} routes{' with no module spec' if uncovered_only else ''}.", ""]
    for area in sorted(by_area):
        lines += [f"## {area} ({len(by_area[area])})", "",
                  "| Route | Renders | Source | Module spec |", "|---|---|---|---|"]
        for route, component, source, slug in sorted(by_area[area]):
            lines.append(f"| `{route}` | {component or '—'} | `{source}` | {slug or '**none**'} |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--uncovered", action="store_true", help="only routes no module spec claims")
    parser.add_argument("--out", help="write to this path (relative to automation/) instead of stdout")
    args = parser.parse_args()
    text = report(uncovered_only=args.uncovered)
    if args.out:
        path = AUTOMATION / args.out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n")
        print(f"wrote {path.relative_to(AUTOMATION)}")
    else:
        print(text)


if __name__ == "__main__":
    main()
