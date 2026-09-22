"""Compares the live page with a saved Figma frame (spec.json + optional png) and writes a report.

Per design.check() call (one flow step):
  1. screenshot the modal card or the full page      -> <run>/<step>/app.png
  2. for every text layer in the Figma spec, find the same text in the app and compare
     font family / size / weight / line height / color  -> issues
  3. pixel-diff against the Figma png, if one is saved -> diff.png + mismatch % (report only)

At the end of the session every feature gets reports/design/<slug>/<run>/report.html,
rendered by report.mjs from results.json. Nothing here calls Figma or an AI.
"""
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

from designcheck.flow import Flow

HERE = Path(__file__).resolve().parent
REPORTS_DIR = HERE.parent / "reports" / "design"

# The open modal's white card (ModalWrapper / SlotSchedulerModal: .global-modal-container > Box),
# falling back to MUI dialogs.
MODAL_CSS = ".global-modal-container > .MuiBox-root, .MuiDialog-paper, [role='dialog']"

SEVERITY_WEIGHT = {"high": 15, "medium": 5, "low": 1}
PIXEL_THRESHOLD = 38  # 0.15 * 255, same default as diff.mjs

# Sample data in Figma (numbers, amounts, dates, long sample notes) will not match live data.
_SAMPLE_HINT = re.compile(r"\d|₹|\bcr\b")
_SAMPLE_MAX_LEN = 80

_FIND_TEXTS_JS = """
(root, texts) => {
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  const visible = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const els = [root, ...root.querySelectorAll('*')].filter(visible);
  // Inputs have no innerText: their visible text is the placeholder (or the typed value).
  const textOf = new Map(els.map(e => [e, norm(e.matches('input, textarea')
      ? (e.value || e.getAttribute('placeholder')) : e.innerText)]));
  const deepest = (pred) => els.find(e => pred(textOf.get(e)) &&
      ![...e.children].some(c => textOf.has(c) && pred(textOf.get(c))));
  const describe = (e) => {
    const cs = getComputedStyle(e), r = e.getBoundingClientRect();
    return { text: textOf.get(e), fontFamily: cs.fontFamily, fontSize: cs.fontSize, fontWeight: cs.fontWeight,
             lineHeight: cs.lineHeight, color: cs.color, x: r.x, y: r.y + window.scrollY, w: r.width, h: r.height };
  };
  const out = {};
  for (const raw of texts) {
    const t = norm(raw), lower = t.toLowerCase();
    let e = deepest(v => v === t), how = 'exact';
    if (!e) { e = deepest(v => v.toLowerCase() === lower); how = 'case'; }
    if (!e) {
      const head = lower.split(' ').slice(0, 3).join(' ');
      e = head.length >= 4 ? deepest(v => v.toLowerCase().startsWith(head) && v.length < t.length * 2 + 20) : null;
      how = 'near';
    }
    out[raw] = e ? { how, ...describe(e) } : null;
  }
  return out;
}
"""


def _norm(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _hex(css_color):
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", css_color or "")
    return "#{:02x}{:02x}{:02x}".format(*map(int, m.groups())) if m else None


def _px(value):
    m = re.match(r"([\d.]+)px", value or "")
    return float(m.group(1)) if m else None


def _text_layers(node, out):
    if isinstance(node, dict):
        if node.get("type") == "TEXT" and _norm(node.get("text")):
            out.append(node)
        for child in node.get("children") or []:
            _text_layers(child, out)
    return out


class StepResult:
    def __init__(self, step, url):
        self.step, self.url = step, url
        self.issues, self.notes = [], []
        self.design = self.app = self.diff = None
        self.mismatch_pct = None

    def add(self, severity, category, element, expected, actual, box=None):
        self.issues.append({"severity": severity, "category": category, "element": element,
                            "expected": expected, "actual": actual, "file": "", "box": box})

    def as_dict(self):
        counts = {s: sum(i["severity"] == s for i in self.issues) for s in SEVERITY_WEIGHT}
        score = max(0, 100 - sum(SEVERITY_WEIGHT[s] * n for s, n in counts.items()))
        return {"id": self.step.id, "title": self.step.title, "url": self.url, "navOk": True,
                "design": self.design, "app": self.app, "diff": self.diff,
                "matchScore": score, "mismatchPct": self.mismatch_pct,
                "notes": " ".join(self.notes), "issues": self.issues}


class FeatureRun:
    def __init__(self, slug, stamp):
        self.flow = Flow(slug)
        self.dir = REPORTS_DIR / slug / stamp
        self.results = []

    def check(self, page, step_id, scope=None):
        step = self.flow.step(step_id)
        step_dir = self.dir / step_id
        step_dir.mkdir(parents=True, exist_ok=True)
        result = StepResult(step, page.url)
        self.results.append(result)

        page.evaluate("document.fonts.ready.then(() => true)")
        target = scope
        if target is None and step.scope == "modal":
            target = page.locator(MODAL_CSS).last
        origin = (0, 0)
        if target is not None:
            target.wait_for(state="visible", timeout=10_000)
            target.screenshot(path=str(step_dir / "app.png"))
            box = target.bounding_box()
            origin = (box["x"], box["y"] + page.evaluate("window.scrollY"))
        else:
            page.screenshot(path=str(step_dir / "app.png"), full_page=True)
        result.app = f"{step_id}/app.png"

        spec_file = self.flow.spec_path(step_id)
        if spec_file.exists():
            root = target if target is not None else page.locator("body")
            self._compare_spec(result, json.loads(spec_file.read_text()), root, origin)
        else:
            result.notes.append("No spec.json saved for this step: run designcheck.sync_refs.")

        png = self.flow.png_path(step_id)
        if png.exists():
            shutil.copy(png, step_dir / "design.png")
            result.design = f"{step_id}/design.png"
            result.mismatch_pct = _pixel_diff(png, step_dir / "app.png", step_dir / "diff.png")
            result.diff = f"{step_id}/diff.png"
        else:
            result.notes.append("No Figma PNG saved, so no pixel diff (style and copy were still compared).")
        return result

    def _compare_spec(self, result, spec, root, origin):
        step = result.step
        layers = _text_layers(spec, [])
        found = root.evaluate(_FIND_TEXTS_JS, [layer["text"] for layer in layers])
        accepted, sample_missing = [], []

        def record(severity, category, element, expected, actual, match=None):
            known = self.flow.known_difference(step.id, expected)
            if known and known.status == "accepted":
                accepted.append(f"{element}: {known.note}")
                return
            box = None
            if match:
                box = [round(match["x"] - origin[0]), round(match["y"] - origin[1]), round(match["w"]), round(match["h"])]
            result.add(severity, category, element, expected, actual, box)

        only = {_norm(t).lower() for t in step.only_text}
        for layer in layers:
            text = _norm(layer["text"])
            if only and text.lower() not in only:
                continue
            if any(re.search(p, text) for p in step.skip_text):
                continue
            if (any(re.search(p, text) for p in step.sample_text)
                    or bool(_SAMPLE_HINT.search(text)) or len(text) > _SAMPLE_MAX_LEN):
                sample_missing.append(text[:40])  # sample data: never matches live data reliably
                continue
            match = found.get(layer["text"])
            label = f'"{text[:50]}"'

            if match is None:
                record("high", "copy", label, text, "not found on the page")
                continue
            if match["how"] == "case" and layer.get("font", {}).get("case") is None:
                record("low", "copy", label, text, f'different case: "{match["text"]}"', match)
            elif match["how"] == "near":
                record("high", "copy", label, text, f'"{match["text"][:120]}"', match)
                continue  # a different element: its styles aren't comparable

            self._compare_style(record, label, layer, match)

        if accepted:
            result.notes.append("Accepted known differences: " + "; ".join(accepted) + ".")
        if sample_missing:
            result.notes.append(f"Figma sample data, not compared ({len(sample_missing)}): "
                                + ", ".join(f'"{t}"' for t in sample_missing[:6]) + ".")

    @staticmethod
    def _compare_style(record, label, layer, match):
        font = layer.get("font") or {}
        family = (font.get("family") or "").lower()
        if family and family not in (match["fontFamily"] or "").lower():
            record("medium", "typography", f"{label} font", font["family"], match["fontFamily"], match)
        size = _px(match["fontSize"])
        if font.get("size") and size is not None and abs(size - font["size"]) > 0.5:
            record("medium", "typography", f"{label} font size", f'{font["size"]}px', match["fontSize"], match)
        if font.get("weight") and str(font["weight"]) != str(match["fontWeight"]):
            record("medium", "typography", f"{label} font weight", str(font["weight"]), match["fontWeight"], match)
        line = _px(match["lineHeight"])
        if font.get("lineHeight") and line is not None and abs(line - font["lineHeight"]) > 1:
            record("low", "typography", f"{label} line height", f'{font["lineHeight"]}px', match["lineHeight"], match)
        fills = layer.get("fills") or []
        actual = _hex(match["color"])
        if fills and actual and fills[0].lower() != actual:
            record("medium", "color", f"{label} text color", fills[0].lower(), actual, match)


def _pixel_diff(design_png, app_png, out_png):
    """Report-only pixel diff (fonts render differently in Figma and browsers)."""
    app = Image.open(app_png).convert("RGB")
    design = Image.open(design_png).convert("RGB")
    if design.width != app.width:
        design = design.resize((app.width, round(design.height * app.width / design.width)))
    height = max(app.height, design.height)
    a = ImageOps.pad(app, (app.width, height), color="white", centering=(0, 0))
    d = ImageOps.pad(design, (app.width, height), color="white", centering=(0, 0))
    mask = ImageChops.difference(a, d).convert("L").point(lambda v: 255 if v > PIXEL_THRESHOLD else 0)
    changed = mask.histogram()[255]
    faded = Image.blend(ImageOps.grayscale(a).convert("RGB"), Image.new("RGB", a.size, "white"), 0.7)
    faded.paste(Image.new("RGB", a.size, (217, 45, 32)), mask=mask)
    faded.save(out_png)
    return round(100 * changed / (a.width * height), 2)


class DesignRun:
    """Session-wide collector; one FeatureRun per feature slug that tests check."""

    def __init__(self, enabled, strict):
        self.enabled, self.strict = enabled, strict
        self.stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.features = {}

    def check(self, slug, page, step_id, scope=None):
        if not self.enabled:
            return None
        if slug not in self.features:
            self.features[slug] = FeatureRun(slug, self.stamp)
        return self.features[slug].check(page, step_id, scope)

    def finish(self):
        """Write results.json + report.html per feature; returns [(report path, high issue count)]."""
        reports = []
        for run in self.features.values():
            results = {"feature": run.flow.feature, "viewport": run.flow.viewport,
                       "createdAt": datetime.now().isoformat(timespec="seconds"),
                       "reference": run.flow.figma_file, "steps": [r.as_dict() for r in run.results]}
            (run.dir / "results.json").write_text(json.dumps(results, indent=2))
            html = subprocess.run(["node", str(HERE / "report.mjs"), str(run.dir)],
                                  capture_output=True, text=True)
            report = html.stdout.strip() or f"(report.mjs failed: {html.stderr.strip()[:200]})"
            high = sum(i["severity"] == "high" for r in run.results for i in r.issues)
            reports.append((run.flow.feature, report, high))
        return reports
