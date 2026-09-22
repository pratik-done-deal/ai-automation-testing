"""Loads a feature's design flow: docs/features/<slug>/{flow.yaml, refs/, known_differences.yml}."""
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO_ROOT / "docs" / "features"


@dataclass
class Step:
    id: str
    title: str
    scope: str = "page"
    role: str = ""
    figma_node: str = ""
    sample_text: list = field(default_factory=list)
    skip_text: list = field(default_factory=list)
    only_text: list = field(default_factory=list)
    when: str = ""  # where in the journey to call design.check (read by test-case-writer, not the checker)


@dataclass
class KnownDifference:
    step: str
    expected: str
    status: str
    note: str = ""

    def matches(self, step_id, expected_value):
        if self.step not in ("*", step_id):
            return False
        if self.expected.startswith("^"):
            return re.search(self.expected, expected_value or "") is not None
        return self.expected == (expected_value or "")


class Flow:
    def __init__(self, slug):
        self.slug = slug
        self.dir = FEATURES_DIR / slug
        data = yaml.safe_load((self.dir / "flow.yaml").read_text())
        self.feature = data.get("feature", slug)
        self.figma_file = data.get("figma_file", "")
        self.viewport = data.get("viewport", "")
        self.steps = {s["id"]: Step(**s) for s in data.get("steps", [])}
        known = self.dir / "known_differences.yml"
        self.known = [KnownDifference(**k) for k in (yaml.safe_load(known.read_text()) or [])] if known.exists() else []

    def step(self, step_id) -> Step:
        if step_id not in self.steps:
            raise KeyError(f"{step_id!r} is not a step in {self.dir / 'flow.yaml'}")
        return self.steps[step_id]

    def spec_path(self, step_id) -> Path:
        return self.dir / "refs" / f"{step_id}.spec.json"

    def png_path(self, step_id) -> Path:
        return self.dir / "refs" / f"{step_id}.png"

    def known_difference(self, step_id, expected_value):
        return next((k for k in self.known if k.matches(step_id, expected_value)), None)
