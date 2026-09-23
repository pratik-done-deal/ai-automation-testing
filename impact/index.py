"""Index of the suite for impact analysis and coverage. Static (ast): nothing is imported or run.

For every test it records the requirement ids it names (DR-06, BUY-CUE-01), its markers, its
design.check() steps, and every symbol it reaches: locators, page objects, constants, utils and
fixtures, followed through conftest. Each symbol keeps its string literals, so copy and endpoints
can be traced back to the tests that depend on them.

    python -m impact.index                      # requirements and tests per module / feature
    python -m impact.index --req DR-06 DR-07    # tests that name these requirements
    python -m impact.index --test test_chip     # what one test reaches
"""
import argparse
import ast
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))

from utils.registry import entry_for_requirement, load_registry, requirement_pattern  # noqa: E402

SOURCE_DIRS = ("locators", "pages", "utils", "data", "test_cases")
SOURCE_FILES = ("constants.py", "conftest.py", "config.py")
TEST_ROOT = "test_cases"


@dataclass
class Symbol:
    """A top-level function, class, class attribute or assignment of one suite module."""
    qualname: str                      # e.g. pages.buyer_module.buyer_cue_card_page.BuyerCueCardPage
    path: str
    line: int
    literals: set = field(default_factory=set)
    uses: set = field(default_factory=set)        # qualnames this symbol refers to
    fixtures: list = field(default_factory=list)  # argument names (fixtures, for functions)


@dataclass
class TestInfo:
    nodeid: str
    symbol: Symbol
    requirements: list
    markers: dict                      # marker name -> first positional arg (or None)
    design_steps: list
    design_feature: str = ""


def _module_name(path):
    return ".".join(path.relative_to(AUTOMATION).with_suffix("").parts)


def _literals(node):
    """String constants inside node, leaving out docstrings and other bare string statements."""
    bare = {id(sub.value) for sub in ast.walk(node)
            if isinstance(sub, ast.Expr) and isinstance(sub.value, ast.Constant)}
    return {sub.value for sub in ast.walk(node)
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value.strip()
            and id(sub) not in bare}


def _referenced(node):
    """Names and dotted attribute chains used inside node: {"Copy", "Copy.CLOSE", "settings", ...}."""
    out = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            out.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            chain, cur = [sub.attr], sub.value
            while isinstance(cur, ast.Attribute):
                chain.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                chain.append(cur.id)
                chain.reverse()
                for i in range(2, len(chain) + 1):
                    out.add(".".join(chain[:i]))
    return out


def _marker(decorator):
    """@pytest.mark.name / @pytest.mark.name("arg") -> (name, arg)."""
    call = decorator if isinstance(decorator, ast.Call) else None
    target = call.func if call else decorator
    if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Attribute)
            and target.value.attr == "mark"):
        arg = None
        if call and call.args and isinstance(call.args[0], ast.Constant):
            arg = call.args[0].value
        return target.attr, arg
    return None


def _design_steps(node):
    return [sub.args[0].value for sub in ast.walk(node)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "check"
            and isinstance(sub.func.value, ast.Name) and sub.func.value.id == "design"
            and sub.args and isinstance(sub.args[0], ast.Constant)]


def _is_fixture(decorator):
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return isinstance(target, ast.Attribute) and target.attr == "fixture"


class SuiteIndex:
    def __init__(self):
        self.symbols = {}                          # qualname -> Symbol
        self.fixtures = defaultdict(dict)          # module -> {fixture name: qualname}; "conftest" is global
        self.tests = []
        self.req_re = requirement_pattern()
        for path in self._files():
            self._index_module(path)
        self._reach_cache = {}

    @staticmethod
    def _files():
        files = [AUTOMATION / name for name in SOURCE_FILES if (AUTOMATION / name).exists()]
        for folder in SOURCE_DIRS:
            if (AUTOMATION / folder).exists():
                files += sorted(p for p in (AUTOMATION / folder).rglob("*.py") if "__pycache__" not in p.parts)
        return files

    def _index_module(self, path):
        module = _module_name(path)
        source = path.read_text()
        tree = ast.parse(source)
        rel = str(path.relative_to(AUTOMATION))
        lines = source.splitlines()

        imports = {}  # local name -> qualname
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                for alias in node.names:
                    imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.asname or alias.name] = alias.name
        local = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                local[node.name] = f"{module}.{node.name}"
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        local[target.id] = f"{module}.{target.id}"

        def resolve(names):
            out = set()
            for name in names:
                head, _, rest = name.partition(".")
                base = local.get(head) or imports.get(head)
                if base:
                    out.add(f"{base}.{rest}" if rest else base)
            return out

        def add(qualname, node, fixtures=()):
            self.symbols[qualname] = Symbol(qualname, rel, node.lineno, _literals(node),
                                            resolve(_referenced(node)), list(fixtures))

        module_markers = {}
        design_feature = ""
        is_test_module = module.startswith(TEST_ROOT + ".")
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                add(f"{module}.{node.name}", node, [a.arg for a in node.args.args])
                if any(_is_fixture(d) for d in node.decorator_list):
                    scope = "conftest" if module == "conftest" else module
                    self.fixtures[scope][node.name] = f"{module}.{node.name}"
                if node.name.startswith("test_") and is_test_module:
                    self._add_test(rel, module, node, lines, module_markers, design_feature)
            elif isinstance(node, ast.ClassDef):
                # Class attributes are symbols of their own, so a test using Copy.CLOSE doesn't match
                # every other Copy string. A class with methods (a page object) depends on all of them.
                attrs = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                add(f"{module}.{node.name}.{target.id}", item)
                                attrs.append(f"{module}.{node.name}.{target.id}")
                body = [item for item in node.body if not isinstance(item, ast.Assign)]
                has_methods = any(isinstance(item, ast.FunctionDef) for item in body)
                cls = ast.Module(body=body, type_ignores=[])
                self.symbols[f"{module}.{node.name}"] = Symbol(
                    f"{module}.{node.name}", rel, node.lineno, _literals(cls),
                    resolve(_referenced(cls)) | (set(attrs) if has_methods else set()))
                for item in body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_") and is_test_module:
                        self._add_test(rel, module, item, lines, module_markers, design_feature, node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    add(f"{module}.{target.id}", node)
                    if target.id == "pytestmark":
                        values = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
                        module_markers.update(m for m in map(_marker, values) if m)
                    elif target.id == "DESIGN_FEATURE" and isinstance(node.value, ast.Constant):
                        design_feature = node.value.value

    def _add_test(self, rel, module, node, lines, module_markers, design_feature, cls=None):
        name = f"{cls}::{node.name}" if cls else node.name
        qualname = f"{module}.{cls}.{node.name}" if cls else f"{module}.{node.name}"
        symbol = self.symbols.get(qualname) or Symbol(qualname, rel, node.lineno, _literals(node), set(),
                                                      [a.arg for a in node.args.args])
        self.symbols[qualname] = symbol
        start = min([d.lineno for d in node.decorator_list] + [node.lineno])
        text = "\n".join(lines[start - 1:node.end_lineno])
        markers = dict(module_markers)
        markers.update(m for m in map(_marker, node.decorator_list) if m)
        self.tests.append(TestInfo(nodeid=f"{rel}::{name}", symbol=symbol,
                                   requirements=sorted(set(self.req_re.findall(text))), markers=markers,
                                   design_steps=_design_steps(node), design_feature=design_feature))

    def reach(self, test):
        """Every suite symbol a test depends on: {qualname: the path of qualnames from the test}."""
        if test.nodeid in self._reach_cache:
            return self._reach_cache[test.nodeid]
        module = test.symbol.qualname.rsplit(".", 1)[0]
        seen = {test.symbol.qualname: [test.symbol.qualname]}
        queue = [test.symbol.qualname]
        while queue:
            current = queue.pop(0)
            symbol = self._lookup(current)
            if symbol is None:
                continue
            nexts = set(symbol.uses)
            for arg in symbol.fixtures:
                fixture = self.fixtures[module].get(arg) or self.fixtures["conftest"].get(arg)
                if fixture:
                    nexts.add(fixture)
            for nxt in sorted(nexts):
                target = self._lookup(nxt)
                if target is None:      # stdlib, playwright, pytest
                    continue
                if target.qualname not in seen:
                    seen[target.qualname] = seen[current] + [target.qualname]
                    queue.append(target.qualname)
        self._reach_cache[test.nodeid] = seen
        return seen

    def _lookup(self, qualname):
        # "pages.x.Page.method" isn't indexed on its own: fall back to the enclosing class.
        while qualname:
            if qualname in self.symbols:
                return self.symbols[qualname]
            qualname = qualname.rpartition(".")[0]
        return None

    def tests_for_requirement(self, req_id):
        return [t for t in self.tests if req_id in t.requirements]


def _summary(index):
    by_entry = defaultdict(lambda: defaultdict(list))
    unlinked = []
    for test in index.tests:
        if not test.requirements:
            unlinked.append(test.nodeid)
        for req in test.requirements:
            entry = entry_for_requirement(req)
            by_entry[entry.slug if entry else "(unregistered prefix)"][req].append(test.nodeid)
    registry = load_registry()
    for slug, reqs in sorted(by_entry.items()):
        entry = registry.get(slug)
        kind = f"{entry.kind}, {entry.status}" if entry else "unknown"
        tests = {t for nodes in reqs.values() for t in nodes}
        print(f"{slug} [{kind}]: {len(reqs)} requirements, {len(tests)} tests")
    print(f"tests naming no requirement id: {len(unlinked)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--req", nargs="*", help="requirement ids")
    parser.add_argument("--test", help="substring of a test node id")
    args = parser.parse_args()
    index = SuiteIndex()

    if args.req:
        for req in args.req:
            print(f"{req}:")
            for test in index.tests_for_requirement(req):
                print(f"  {test.nodeid}  markers={sorted(test.markers)}")
    elif args.test:
        for test in (t for t in index.tests if args.test in t.nodeid):
            print(test.nodeid)
            print(f"  requirements: {', '.join(test.requirements) or '-'}")
            print(f"  markers: {test.markers}")
            print(f"  design steps: {test.design_steps or '-'}")
            reached = sorted(q for q in index.reach(test) if not q.startswith(test.symbol.qualname))
            print(f"  reaches ({len(reached)}): " + ", ".join(reached))
    else:
        _summary(index)


if __name__ == "__main__":
    main()
