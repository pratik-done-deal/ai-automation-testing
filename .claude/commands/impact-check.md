---
description: Check which existing automated tests a new feature (or code change) affects, without writing tests
argument-hint: <feature slug> [git range, e.g. main...feature/x] [figma-url]
---

Run only the impact step, e.g. when a feature's design or code changed after its tests were written.

Inputs from the user:

$ARGUMENTS

1. The feature needs `specs/prd/<slug>.analysis.md`. If it doesn't exist, suggest
   `/analyze-prd` first. For a quick look without an analysis, run from the repo root:
   `python -m impact.find --route <route> --copy "<old text>"` and show the candidates.
2. Use the **impact-analyzer** subagent with the slug, the analysis path, the git range and the Figma URL
   if there is one.
3. Show the summary, **the "Files to change" table in full**, the numbered `supersede` rows and the
   decisions, then **stop for approval**.
4. After approval, fill impact.md's `## Approval` section, set `Status: APPROVED`, and run
   `python scripts/check_pipeline.py impact <slug>`. Ask whether to
   apply it now with **test-script-writer** — and, if the feature also redesigns screens an existing
   `flow.yaml` covers, whether to run `/design-checks <slug>`.
