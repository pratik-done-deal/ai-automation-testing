"""Save a feature's Figma frames as local references (spec.json + png). Run once per design change.

    cd automation
    FIGMA_TOKEN=figd_... python -m designcheck.sync_refs data-room-document-request
    python -m designcheck.sync_refs data-room-document-request --only buyer-3a-success-no-docs --force
    python -m designcheck.sync_refs data-room-document-request --spec-only

Existing files are kept unless --force. Commit specs/features/<slug>/refs/ afterwards: test runs read
only these files, so they never call Figma (personal tokens are heavily rate-limited).
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from designcheck.flow import Flow  # noqa: E402


def _figma(command, flow, step, out):
    result = subprocess.run(
        ["node", str(HERE / "figma.mjs"), command, "--url", flow.figma_file, "--node", step.figma_node,
         "--out", str(out)] + (["--scale", "1"] if command == "image" else []),
        capture_output=True, text=True)
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        if "429" in message:
            sys.exit(f"Figma rate limit hit at {step.id}. Wait and re-run; saved files are kept.\n{message}")
        print(f"  ! {step.id} {command}: {message[:300]}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("--only", nargs="*", help="step ids to sync (default: all)")
    parser.add_argument("--force", action="store_true", help="overwrite saved files")
    parser.add_argument("--spec-only", action="store_true", help="skip PNG exports")
    args = parser.parse_args()

    if not os.getenv("FIGMA_TOKEN"):
        sys.exit("FIGMA_TOKEN is not set (Figma → Settings → Security → Personal access tokens).")
    flow = Flow(args.slug)
    (flow.dir / "refs").mkdir(parents=True, exist_ok=True)

    for step in flow.steps.values():
        if args.only and step.id not in args.only:
            continue
        if not step.figma_node:
            print(f"  - {step.id}: no figma_node in flow.yaml, skipped")
            continue
        jobs = [("spec", flow.spec_path(step.id))] + ([] if args.spec_only else [("image", flow.png_path(step.id))])
        for command, out in jobs:
            if out.exists() and not args.force:
                print(f"  = {out.relative_to(flow.dir)} (kept)")
            elif _figma(command, flow, step, out):
                print(f"  + {out.relative_to(flow.dir)}")


if __name__ == "__main__":
    main()
