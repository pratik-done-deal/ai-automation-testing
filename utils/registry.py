"""The coverage registry: what this suite covers, and what state it's in.

Two kinds of entry, one shape:
  specs/modules/<module>/module.yml    a part of the platform, mapped once by surface-mapper.
                                       module.md next to it is its living spec.
  specs/features/<slug>/feature.yml    a PRD feature: a change to one or more modules. Once it ships,
                                       its requirements are folded into the module spec and the
                                       feature folder stays as history.

`status` matters for features only (in_development | shipped): tests marked pending_feature("<slug>")
are expected to fail until it ships, and tests marked superseded_by("<slug>") are skipped once it has.
Modules describe what is live, so they count as shipped.

Override the status for one run:
    DD_SHIPPED=slug-a,slug-b      treat these as shipped (e.g. QA has them already)
    DD_UNSHIPPED=slug-c           treat these as not shipped (e.g. an older branch)
"""
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from paths import FEATURES_DIR, MODULES_DIR  # noqa: E402

STATUSES = ("in_development", "shipped")


@dataclass
class Entry:
    slug: str
    name: str
    kind: str                      # "module" or "feature"
    req_prefix: str
    status: str
    dir: Path
    docs: dict = field(default_factory=dict)
    footprint: dict = field(default_factory=dict)
    modules: list = field(default_factory=list)   # features: the modules they change
    changes: list = field(default_factory=list)   # modules: the features that changed them

    @property
    def spec(self):
        """The living spec (module.md) or the feature's analysis."""
        return self.dir / "module.md" if self.kind == "module" else self.dir / "impact.md"


def _load(path, kind, default_status):
    data = yaml.safe_load(path.read_text()) or {}
    slug = data.get("slug") or path.parent.name
    if slug != path.parent.name:
        raise ValueError(f"{path}: slug {slug!r} doesn't match its folder name")
    status = data.get("status", default_status)
    if status not in STATUSES:
        raise ValueError(f"{path}: status must be one of {STATUSES}, not {status!r}")
    return Entry(slug=slug, name=data.get("name") or data.get("feature") or data.get("module") or slug,
                 kind=kind, req_prefix=data.get("req_prefix", ""), status=status, dir=path.parent,
                 docs=data.get("docs") or {}, footprint=data.get("footprint") or {},
                 modules=data.get("modules") or [], changes=data.get("changes") or [])


@lru_cache(maxsize=1)
def load_registry():
    """{slug: Entry} for every module.yml and feature.yml."""
    entries = {}
    for path in sorted(MODULES_DIR.glob("*/module.yml")):
        entries[path.parent.name] = _load(path, "module", "shipped")
    for path in sorted(FEATURES_DIR.glob("*/feature.yml")):
        if path.parent.name in entries:
            raise ValueError(f"{path.parent.name} is both a module and a feature slug")
        entries[path.parent.name] = _load(path, "feature", "in_development")
    return entries


def modules():
    return {s: e for s, e in load_registry().items() if e.kind == "module"}


def features():
    return {s: e for s, e in load_registry().items() if e.kind == "feature"}


def _env_list(name):
    return {s.strip() for s in os.getenv(name, "").split(",") if s.strip()}


def is_shipped(slug):
    if slug in _env_list("DD_UNSHIPPED"):
        return False
    if slug in _env_list("DD_SHIPPED"):
        return True
    entry = load_registry().get(slug)
    return bool(entry and entry.status == "shipped")


def requirement_pattern():
    """Regex for requirement ids of registered entries, e.g. DR-06 or BUY-CUE-01."""
    prefixes = sorted({e.req_prefix for e in load_registry().values() if e.req_prefix}, key=len, reverse=True)
    body = "|".join(map(re.escape, prefixes)) if prefixes else r"[A-Z][A-Z-]{0,12}"
    return re.compile(rf"\b(?:{body})-\d{{1,3}}\b")


def entry_for_requirement(req_id):
    """The module or feature a requirement id belongs to (longest matching prefix wins)."""
    candidates = [e for e in load_registry().values() if e.req_prefix and req_id.startswith(e.req_prefix + "-")]
    return max(candidates, key=lambda e: len(e.req_prefix), default=None)
