"""Text of saved Figma refs, and what a new frame changes on the same screen. No AI, no network.

    python -m impact.figma_texts data-room-document-request                       # every step's texts
    python -m impact.figma_texts data-room-document-request --step seller-2-accept-modal
    python -m impact.figma_texts data-room-document-request --step seller-2-accept-modal --new new.spec.json
    python -m impact.figma_texts data-room-document-request --step seller-2-accept-modal --new new_texts.txt

--new takes the new frame either as a spec.json (node designcheck/figma.mjs spec ..., needs
FIGMA_TOKEN) or as a text file with one visible text per line, e.g. the text nodes from the Figma
MCP get_metadata output. Removed texts are the OLD copy to pass to `impact.find --copy`.
"""
import argparse
import json
import sys
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTOMATION))

from impact.find import _flow_texts  # noqa: E402
from utils.registry import load_registry  # noqa: E402


def _norm(text):
    return " ".join(text.split())


def _texts_of(path):
    path = Path(path)
    if path.suffix == ".json":
        texts, stack = [], [json.loads(path.read_text())]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if node.get("type") == "TEXT" and (node.get("text") or "").strip():
                    texts.append(node["text"])
                stack.extend(node.get("children") or [])
        return texts
    return [line for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("--step")
    parser.add_argument("--new", help="new frame: spec.json or a text file (one text per line)")
    args = parser.parse_args()

    entry = load_registry().get(args.slug)
    if entry is None:
        sys.exit(f"{args.slug} is not in the registry (specs/modules/ or specs/features/)")
    steps = _flow_texts(entry)
    if not steps:
        sys.exit(f"No saved refs in {entry.dir}/refs/")
    if args.step:
        if args.step not in steps:
            sys.exit(f"No refs/{args.step}.spec.json. Steps with refs: {', '.join(steps)}")
        steps = {args.step: steps[args.step]}

    if not args.new:
        for step, texts in steps.items():
            print(f"{step} ({len(texts)} texts)")
            for text in dict.fromkeys(_norm(t) for t in texts):
                print(f"  {text}")
        return

    if not args.step:
        parser.error("--new needs --step")
    old = {_norm(t) for t in steps[args.step]}
    new = {_norm(t) for t in _texts_of(args.new)}
    print(f"# {args.slug}:{args.step} vs {args.new}")
    print(f"\nremoved or reworded ({len(old - new)}): pass these to impact.find --copy")
    for text in sorted(old - new):
        print(f"  - {text}")
    print(f"\nadded ({len(new - old)})")
    for text in sorted(new - old):
        print(f"  + {text}")
    print(f"\nunchanged: {len(old & new)}")


if __name__ == "__main__":
    main()
