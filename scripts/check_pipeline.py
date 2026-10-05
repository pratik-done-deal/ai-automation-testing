"""Check a pipeline step's output against the format its agent file defines.

Every step of the pipeline (Claude Code or Codex) runs this after writing its file, and fixes what it
reports before handing over, so both tools produce documents with the same structure: the same
sections in the same order, the same table columns, the same id formats and allowed values.

    python scripts/check_pipeline.py analysis <slug>     # specs/prd/<slug>.analysis.md
    python scripts/check_pipeline.py impact <slug>       # specs/features/<slug>/feature.yml + impact.md
    python scripts/check_pipeline.py test-cases <slug>   # specs/features/<slug>/test-cases.md
    python scripts/check_pipeline.py scripts <slug>      # the tests in test_cases/ vs test-cases.md
    python scripts/check_pipeline.py all <slug>          # every step whose file exists

Exit 0 when clean (warnings allowed), 1 when there are errors. The formats are the ones in
.claude/agents/<agent>.md; change both together.
"""
import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"

REQ_ID = re.compile(r"^([A-Z][A-Z0-9]*)-\d{2,}$")
TC_ID = re.compile(r"^S(\d+)-(\d{2,})$")

ANALYSIS_SECTIONS = ["1. Summary", "2. How it works today", "3. What changes", "4. Requirements",
                     "5. Screens", "6. Flow and sequencing", "7. Open questions", "8. Gaps and risks"]
ANALYSIS_OPTIONAL = {"5. Screens"}   # omitted when the feature changes no screen
REQ_HEADER = ["ID", "Requirement (one sentence)", "Source", "Role", "Type", "Verify via", "Exists today"]
REQ_TYPES = {"flow", "rule", "gating", "lock", "edge-case", "copy", "non-functional"}
VERIFY_VIA = {"UI", "flow", "manual"}
EXISTS = {"yes", "no", "partial", "unknown", "n/a"}

IMPACT_SECTIONS = ["Summary", "Files to change", "Affected requirements", "Shared symbols",
                   "Checked and unaffected", "Decisions needed", "Approval"]
IMPACT_TABLES = {
    "Files to change": ["#", "File", "New or edit", "What changes", "Why"],
    "Affected requirements": ["#", "Old req", "Old behaviour", "New behaviour (new id)", "Verdict", "Evidence"],
    "Shared symbols": ["#", "Symbol (file:line)", "Edit", "Why it stays backward compatible"],
}
VERDICTS = {"supersede", "edit", "leave", "—", "-", ""}

TC_SECTIONS = ["1. Scenario overview", "2. The happy flow", "3. Scenarios and their test cases",
               "4. Detail blocks", "5. Requirement coverage", "6. Test data and run order",
               "7. Assumptions", "8. Review"]
OVERVIEW_HEADER = ["ID", "Scenario", "Role", "Test cases", "Priorities"]
CASE_HEADER = ["TC", "Title", "Steps", "Expected result", "Pri", "Type", "Req", "Run as"]
COVERAGE_HEADER = ["Req ID", "Requirement", "Test cases", "Covered"]
PRIORITIES = {"P0", "P1", "P2"}
CASE_TYPES = {"happy", "negative", "edge", "gating", "copy", "state"}
RUN_AS = {"auto", "manual"}
COVERED = {"yes", "manual", "no"}
NEW_REQ = "new — needs an id"

FEATURE_KEYS = ["name", "slug", "req_prefix", "status", "modules", "docs", "footprint"]
FEATURE_STATUS = {"in_development", "shipped"}


class Report:
    def __init__(self, label):
        self.label, self.errors, self.warnings = label, [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def print(self):
        state = "OK" if not self.errors else "FAILED"
        print(f"{state}  {self.label}" + (f"  ({len(self.errors)} errors)" if self.errors else ""))
        for msg in self.errors:
            print(f"  error: {msg}")
        for msg in self.warnings:
            print(f"  warning: {msg}")
        return not self.errors


# ------------------------------------------------------------------ markdown helpers

def split_row(line):
    """Cells of a markdown table row; `\\|` inside a cell is kept."""
    cells = re.split(r"(?<!\\)\|", line.strip())
    return [c.strip() for c in cells[1:-1]]


def sections(text, level="## "):
    """{heading: body} for one heading level, plus the headings in file order."""
    out, order, current = {}, [], None
    for line in text.splitlines():
        if line.startswith(level) and not line.startswith(level + "#"):
            current = line[len(level):].strip()
            order.append(current)
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v) for k, v in out.items()}, order


def tables(body):
    """Every table in a block of markdown, as (header, rows)."""
    found, block = [], []
    for line in body.splitlines() + [""]:
        if line.lstrip().startswith("|"):
            block.append(line)
            continue
        if len(block) >= 2 and re.fullmatch(r"[\s|:\-]+", block[1]):
            found.append((split_row(block[0]), [split_row(r) for r in block[2:]]))
        block = []
    return found


def check_order(report, order, expected, optional=()):
    wanted = [s for s in expected if s in order or s not in optional]
    for name in wanted:
        if name not in order:
            report.error(f'missing section "## {name}"')
    present = [s for s in order if s in wanted]
    if present != [s for s in wanted if s in order]:
        report.error(f"sections out of order: expected {wanted}, found {present}")


def header_line(report, lines, key, values=None):
    line = next((l for l in lines[:8] if l.startswith(key + ":")), None)
    if line is None:
        report.error(f'missing the "{key}:" line under the title')
        return None
    value = line[len(key) + 1:].strip()
    if values is not None and value not in values:
        report.error(f'"{key}: {value}" must be one of {sorted(values)}')
    return value


def first_word(cell):
    return re.split(r"[\s(,;]", cell.strip(), maxsplit=1)[0].strip("`*")


# ------------------------------------------------------------------ steps

def analysis_requirements(slug):
    """{req id: verify via} from the analysis's section 4, or {} when it can't be read."""
    path = SPECS / "prd" / f"{slug}.analysis.md"
    if not path.exists():
        return {}
    body = sections(path.read_text())[0].get("4. Requirements", "")
    for header, rows in tables(body):
        if header == REQ_HEADER:
            return {r[0]: r[5] for r in rows if len(r) == len(REQ_HEADER)}
    return {}


def check_analysis(slug):
    report = Report(f"analysis    specs/prd/{slug}.analysis.md")
    path = SPECS / "prd" / f"{slug}.analysis.md"
    if not path.exists():
        report.error("file not found")
        return report
    text = path.read_text()
    lines = text.splitlines()

    if not re.fullmatch(r"# .+ — requirements analysis", lines[0]):
        report.error('first line must be "# <Feature> — requirements analysis"')
    status = header_line(report, lines, "Status", {"WAITING", "READY"})
    slug_line = header_line(report, lines, "Slug")
    if slug_line is not None:
        if slug_line.split("|")[0].strip() != slug:
            report.error(f'"Slug:" line must start with "{slug}"')
        for key in ("Roles:", "PRD:", "Figma:"):
            if key not in slug_line:
                report.error(f'"Slug:" line is missing "{key}"')
    header_line(report, lines, "Explored")

    body, order = sections(text)
    check_order(report, order, ANALYSIS_SECTIONS, ANALYSIS_OPTIONAL)

    reqs = [t for t in tables(body.get("4. Requirements", "")) if t[0] == REQ_HEADER]
    if not reqs:
        report.error(f"section 4 needs a table with the columns {REQ_HEADER}")
    else:
        seen, prefixes = set(), set()
        for row in reqs[0][1]:
            if len(row) != len(REQ_HEADER):
                report.error(f"requirement row has {len(row)} cells, needs {len(REQ_HEADER)}: {row[:1]}")
                continue
            rid, _, _, _, rtype, via, exists = row
            m = REQ_ID.match(rid)
            if not m:
                report.error(f'requirement id "{rid}" must look like PREFIX-01')
                continue
            if re.fullmatch(r"S\d+", m.group(1)):
                report.error(f'prefix "{m.group(1)}" looks like a scenario id; pick another')
            prefixes.add(m.group(1))
            if rid in seen:
                report.error(f"requirement id {rid} is used twice")
            seen.add(rid)
            if rtype not in REQ_TYPES:
                report.error(f'{rid}: Type "{rtype}" must be one of {sorted(REQ_TYPES)}')
            if first_word(via) not in VERIFY_VIA:
                report.error(f'{rid}: Verify via "{via}" must start with one of {sorted(VERIFY_VIA)}')
            if first_word(exists) not in EXISTS:
                report.error(f'{rid}: Exists today "{exists}" must start with one of {sorted(EXISTS)}')
        if len(prefixes) > 1:
            report.error(f"requirement ids use more than one prefix: {sorted(prefixes)}")

    questions = body.get("7. Open questions", "")
    if status == "READY" and re.search(r"\*\*blocking\*\*", questions) and "Answers" not in order:
        report.error("Status is READY but section 7 has blocking questions and there is no "
                     '"## Answers" section; answer them or set Status: WAITING')
    if len(lines) > 450:
        report.warn(f"{len(lines)} lines; the agent asks for under ~400")
    return report


def check_impact(slug):
    report = Report(f"impact      specs/features/{slug}/feature.yml + impact.md")
    folder = SPECS / "features" / slug

    fpath = folder / "feature.yml"
    if not fpath.exists():
        report.error("feature.yml not found")
    else:
        feature = yaml.safe_load(fpath.read_text()) or {}
        for key in FEATURE_KEYS:
            if key not in feature:
                report.error(f"feature.yml is missing `{key}`")
        if feature.get("slug") != slug:
            report.error(f"feature.yml slug is {feature.get('slug')!r}, not {slug!r}")
        if feature.get("status") not in FEATURE_STATUS:
            report.error(f"feature.yml status must be one of {sorted(FEATURE_STATUS)}")
        if not isinstance(feature.get("modules"), list):
            report.error("feature.yml `modules` must be a list (use [] for none)")
        docs = feature.get("docs") or {}
        for key in ("prd", "analysis", "test_cases"):
            if key not in docs:
                report.error(f"feature.yml docs is missing `{key}`")
        footprint = feature.get("footprint") or {}
        for key in ("routes", "screens"):
            if not isinstance(footprint.get(key), list):
                report.error(f"feature.yml footprint.{key} must be a list")
        prefixes = {REQ_ID.match(r).group(1) for r in analysis_requirements(slug) if REQ_ID.match(r)}
        if prefixes and feature.get("req_prefix") not in prefixes:
            report.error(f"feature.yml req_prefix {feature.get('req_prefix')!r} doesn't match the "
                         f"analysis ids {sorted(prefixes)}")

    path = folder / "impact.md"
    if not path.exists():
        report.error("impact.md not found")
        return report
    text = path.read_text()
    lines = text.splitlines()
    if not re.fullmatch(r"# Impact of .+ on existing automation", lines[0]):
        report.error('first line must be "# Impact of <Feature> on existing automation"')
    status = header_line(report, lines, "Status", {"WAITING_APPROVAL", "APPROVED", "REJECTED"})
    signals = header_line(report, lines, "Signals")
    if signals is not None and "modules affected:" not in signals:
        report.error('"Signals:" line is missing "modules affected:"')

    body, order = sections(text)
    check_order(report, order, IMPACT_SECTIONS)
    for name, header in IMPACT_TABLES.items():
        found = [t for t in tables(body.get(name, "")) if t[0] == header]
        if not found:
            report.error(f'"## {name}" needs a table with the columns {header}')
            continue
        for row in found[0][1]:
            if len(row) != len(header):
                report.error(f'"{name}" row has {len(row)} cells, needs {len(header)}: {row[:2]}')
                continue
            if not re.fullmatch(r"\d+|—|-", row[0]):
                report.error(f'"{name}" rows are numbered 1, 2, 3 (or — for a "none" row): got {row[0]!r}')
            if name == "Affected requirements" and first_word(row[4]) not in VERDICTS:
                report.error(f'verdict "{row[4]}" must be supersede, edit or leave '
                             "(undecided rows go to Decisions needed)")
    approval = body.get("Approval", "").strip()
    if status in ("APPROVED", "REJECTED") and (not approval or approval.startswith("(filled by")):
        report.error(f"Status is {status} but the Approval section is not filled in")
    if status == "WAITING_APPROVAL" and approval and not approval.startswith("(filled by"):
        report.warn("Approval is filled in but Status is still WAITING_APPROVAL")
    return report


def parse_test_cases(slug):
    """(report-free) {tc id: {pri, run_as, req}} from test-cases.md section 3."""
    path = SPECS / "features" / slug / "test-cases.md"
    body = sections(path.read_text())[0].get("3. Scenarios and their test cases", "")
    cases = {}
    for header, rows in tables(body):
        if header == CASE_HEADER:
            for r in rows:
                if len(r) == len(CASE_HEADER):
                    cases[r[0]] = {"pri": r[4], "req": r[6], "run_as": r[7]}
    return cases


def check_test_cases(slug):
    report = Report(f"test-cases  specs/features/{slug}/test-cases.md")
    path = SPECS / "features" / slug / "test-cases.md"
    if not path.exists():
        report.error("file not found")
        return report
    text = path.read_text()
    lines = text.splitlines()
    if not re.fullmatch(r"# .+ — test cases", lines[0]):
        report.error('first line must be "# <Feature> — test cases"')
    status = header_line(report, lines, "Status", {"WAITING_REVIEW", "APPROVED"})
    slug_line = header_line(report, lines, "Slug")
    if slug_line is not None:
        if slug_line.split("|")[0].strip() != slug:
            report.error(f'"Slug:" line must start with "{slug}"')
        for key in ("Analysis:", "Impact:"):
            if key not in slug_line:
                report.error(f'"Slug:" line is missing "{key}"')
    covered_line = header_line(report, lines, "Requirements covered")

    body, order = sections(text)
    check_order(report, order, TC_SECTIONS)

    analysis = analysis_requirements(slug)
    if not analysis:
        report.warn("could not read the analysis requirements; requirement ids not cross-checked")

    overview = [t for t in tables(body.get("1. Scenario overview", "")) if t[0] == OVERVIEW_HEADER]
    planned = {}
    if not overview:
        report.error(f"section 1 needs a table with the columns {OVERVIEW_HEADER}")
    else:
        for row in overview[0][1]:
            if len(row) == len(OVERVIEW_HEADER):
                if not re.fullmatch(r"S\d+", row[0]):
                    report.error(f'scenario id "{row[0]}" must look like S1')
                planned[row[0]] = row[3]

    scen_body, scen_order = sections(body.get("3. Scenarios and their test cases", ""), "### ")
    scen_ids = []
    all_cases = {}
    for heading in scen_order:
        m = re.fullmatch(r"(S\d+) — .+", heading)
        if not m:
            report.error(f'scenario heading "### {heading}" must be "### S<n> — <scenario>"')
            continue
        sid = m.group(1)
        scen_ids.append(sid)
        block = scen_body[heading]
        if "**Role:**" not in block or "**Precondition:**" not in block:
            report.error(f"{sid}: needs a **Role:** · **Precondition:** · **Path:** line")
        found = [t for t in tables(block) if t[0] == CASE_HEADER]
        if not found:
            report.error(f"{sid}: needs a case table with the columns {CASE_HEADER}")
            continue
        rows = found[0][1]
        if sid in planned and planned[sid].isdigit() and int(planned[sid]) != len(rows):
            report.error(f"{sid}: overview says {planned[sid]} test cases, the table has {len(rows)}")
        for row in rows:
            if len(row) != len(CASE_HEADER):
                report.error(f"{sid}: case row has {len(row)} cells, needs {len(CASE_HEADER)}: {row[:1]}")
                continue
            tc, _, steps, _, pri, ctype, req, run_as = row
            m = TC_ID.match(tc)
            if not m or f"S{m.group(1)}" != sid:
                report.error(f'{sid}: case id "{tc}" must be {sid}-01, {sid}-02, ...')
            if tc in all_cases:
                report.error(f"case id {tc} is used twice")
            all_cases[tc] = row
            if pri not in PRIORITIES:
                report.error(f'{tc}: Pri "{pri}" must be one of {sorted(PRIORITIES)}')
            if ctype not in CASE_TYPES:
                report.error(f'{tc}: Type "{ctype}" must be one of {sorted(CASE_TYPES)}')
            if run_as not in RUN_AS:
                report.error(f'{tc}: Run as "{run_as}" must be auto or manual')
            ids = [r.strip() for r in req.split(",") if r.strip()]
            if not ids:
                report.error(f"{tc}: names no requirement")
            for rid in ids:
                if rid == NEW_REQ:
                    report.warn(f'{tc}: Req is "{NEW_REQ}"; raise it in the review')
                elif analysis and rid not in analysis:
                    report.error(f"{tc}: requirement {rid} is not in the analysis")
            if run_as == "auto" and steps.count("→") > 5:
                report.warn(f"{tc}: more than six steps; the agent asks for a detail block instead")
    if planned and list(planned) != scen_ids:
        report.error(f"scenarios in section 3 {scen_ids} don't match the overview {list(planned)}")

    happy = body.get("2. The happy flow", "")
    for tc in re.findall(r"\bS\d+-\d{2,}\b", happy):
        if tc not in all_cases:
            report.error(f"happy flow names {tc}, which is not a test case")
        elif all_cases[tc][4] != "P0":
            report.warn(f"happy flow names {tc}, which is {all_cases[tc][4]}, not P0")

    coverage = [t for t in tables(body.get("5. Requirement coverage", "")) if t[0] == COVERAGE_HEADER]
    if not coverage:
        report.error(f"section 5 needs a table with the columns {COVERAGE_HEADER}")
    else:
        listed = []
        for row in coverage[0][1]:
            if len(row) != len(COVERAGE_HEADER):
                continue
            listed.append(row[0])
            if first_word(row[3]) not in COVERED:
                report.error(f'{row[0]}: Covered "{row[3]}" must start with yes, manual or no')
            if first_word(row[3]) == "no" and len(row[3].split(None, 1)) < 2:
                report.error(f"{row[0]}: Covered is no with no reason")
        if analysis:
            missing = [r for r in analysis if r not in listed]
            extra = [r for r in listed if r not in analysis]
            if missing:
                report.error(f"section 5 is missing requirements from the analysis: {missing}")
            if extra:
                report.error(f"section 5 lists ids that are not in the analysis: {extra}")
            if listed and listed != [r for r in analysis if r in listed]:
                report.warn("section 5 is not in the analysis's order")
    if covered_line and analysis:
        m = re.match(r"(\d+) of (\d+)", covered_line)
        if not m:
            report.error('"Requirements covered:" must read "<n> of <m>  (<k> manual)"')
        elif int(m.group(2)) != len(analysis):
            report.error(f'"Requirements covered: ... of {m.group(2)}" but the analysis has {len(analysis)}')

    review = body.get("8. Review", "").strip()
    if status == "APPROVED" and (not review or review.startswith("(filled by")) and "Review" not in order:
        report.error("Status is APPROVED but the Review section is not filled in")
    return report


def feature_tests(prefix):
    """{tc id: [(file, function, markers, docstring)]} for the feature's tests.

    A feature's test files are the ones where some test's docstring names a <prefix>- requirement;
    every case-numbered test in those files counts (a `new — needs an id` case names no requirement).
    """
    found = {}
    names_prefix = re.compile(rf"\b{re.escape(prefix)}-\d{{2,}}\b")
    for path in sorted((ROOT / "test_cases").rglob("test_*.py")):
        tree = ast.parse(path.read_text())
        funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        if not any(names_prefix.search(ast.get_docstring(n) or "") for n in funcs):
            continue
        for node in funcs:
            doc = ast.get_docstring(node) or ""
            m = re.search(r"\((S\d+-\d{2,})[),]", doc) or re.match(r"test_s(\d+)_(\d{2,})_", node.name)
            if not m:
                continue
            tc = m.group(1) if m.lastindex == 1 else f"S{m.group(1)}-{m.group(2)}"
            markers = set()
            for dec in node.decorator_list:
                target = dec.func if isinstance(dec, ast.Call) else dec
                if isinstance(target, ast.Attribute):
                    markers.add(target.attr)
            found.setdefault(tc, []).append((path.relative_to(ROOT), node.name, markers, doc))
    return found


def check_scripts(slug):
    report = Report(f"scripts     test_cases/ vs specs/features/{slug}/test-cases.md")
    fpath = SPECS / "features" / slug / "feature.yml"
    tpath = SPECS / "features" / slug / "test-cases.md"
    if not fpath.exists() or not tpath.exists():
        report.error("needs feature.yml and test-cases.md")
        return report
    prefix = (yaml.safe_load(fpath.read_text()) or {}).get("req_prefix")
    if not prefix:
        report.error("feature.yml has no req_prefix")
        return report
    cases = parse_test_cases(slug)
    tests = feature_tests(prefix)
    for tc, case in cases.items():
        if case["run_as"] != "auto":
            continue
        if tc not in tests:
            report.error(f"{tc} ({case['pri']}) has no test: name it test_{tc.lower().replace('-', '_')}_<what> "
                         f"with a docstring that starts with its requirement ids")
            continue
        for path, name, markers, doc in tests[tc]:
            expected = f"test_{tc.lower().replace('-', '_')}_"
            if not name.startswith(expected):
                report.error(f"{path}::{name} covers {tc}; name it {expected}<what>")
            if case["pri"] == "P0" and "smoke" not in markers:
                report.error(f"{path}::{name} covers P0 case {tc} but has no @pytest.mark.smoke")
            if case["pri"] != "P0" and "smoke" in markers:
                report.warn(f"{path}::{name} is marked smoke but {tc} is {case['pri']}")
            reqs = [r.strip() for r in case["req"].split(",") if REQ_ID.match(r.strip())]
            if reqs and not any(r in doc for r in reqs):
                report.error(f"{path}::{name} docstring names none of {tc}'s requirements {reqs}")
    for tc, hits in tests.items():
        if tc not in cases:
            for path, name, _, _ in hits:
                report.warn(f"{path}::{name} names {tc}, which is not in test-cases.md")
    return report


STEPS = {"analysis": check_analysis, "impact": check_impact,
         "test-cases": check_test_cases, "scripts": check_scripts}


def main(argv):
    if len(argv) != 3 or argv[1] not in [*STEPS, "all"]:
        print(__doc__)
        return 2
    step, slug = argv[1], argv[2]
    if step == "all":
        folder = SPECS / "features" / slug
        exists = {"analysis": (SPECS / "prd" / f"{slug}.analysis.md").exists(),
                  "impact": (folder / "impact.md").exists(),
                  "test-cases": (folder / "test-cases.md").exists(),
                  "scripts": (folder / "test-cases.md").exists() and (folder / "feature.yml").exists()}
        run = [s for s in STEPS if exists[s]]
    else:
        run = [step]
    ok = all([STEPS[s](slug).print() for s in run])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
