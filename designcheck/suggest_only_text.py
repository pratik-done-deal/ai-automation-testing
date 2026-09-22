"""List the Figma texts of a step that also appear literally in src/, i.e. fixed UI copy.

For pages whose content depends on the company or user (cue cards, tables), `only_text` in flow.yaml
should hold just these, so live data never shows up as "missing copy".

    python -m designcheck.suggest_only_text data-room-document-request buyer-1-cue-card-before
    python -m designcheck.suggest_only_text data-room-document-request --all-page-steps

Prints a YAML `only_text:` line per step (paste it into flow.yaml). Uses `git grep`, so it only
sees tracked source files.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from designcheck.checker import _norm, _text_layers  # noqa: E402
from designcheck.flow import REPO_ROOT, Flow  # noqa: E402

_DATA_LIKE = re.compile(r"\d|₹")


def in_source(text):
    result = subprocess.run(["git", "grep", "-q", "-F", "-i", text, "--", "src"],
                            cwd=REPO_ROOT, capture_output=True)
    return result.returncode == 0


def fixed_texts(flow, step_id):
    spec = flow.spec_path(step_id)
    if not spec.exists():
        return None
    seen, out = set(), []
    for layer in _text_layers(json.loads(spec.read_text()), []):
        text = _norm(layer["text"])
        if text.lower() in seen or _DATA_LIKE.search(text) or len(text) > 60:
            continue
        seen.add(text.lower())
        if in_source(text):
            out.append(text)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("steps", nargs="*")
    parser.add_argument("--all-page-steps", action="store_true", help="every step with scope: page")
    args = parser.parse_args()

    flow = Flow(args.slug)
    step_ids = args.steps or [s.id for s in flow.steps.values() if args.all_page_steps and s.scope == "page"]
    for step_id in step_ids:
        texts = fixed_texts(flow, step_id)
        if texts is None:
            print(f"# {step_id}: no spec.json yet (run designcheck.sync_refs first)")
            continue
        print(f"# {step_id}: {len(texts)} fixed UI texts found in src/")
        print("    only_text: " + json.dumps(texts, ensure_ascii=False))


if __name__ == "__main__":
    main()
