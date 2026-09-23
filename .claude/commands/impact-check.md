---
description: Check which existing automated tests a new feature (or code change) affects, without writing tests
argument-hint: <feature slug> [figma-url ...] [git range, e.g. main...feature/x]
---

Run only the impact step, e.g. when a feature's design or code changed after its tests were written.

Inputs from the user:

$ARGUMENTS

1. The feature needs `automation/specs/prd/<slug>.analysis.md`. If it doesn't exist, suggest
   `/analyze-prd` first. For a quick look without an analysis, run from `automation/`:
   `python -m impact.find --src <files> --endpoint <api> --copy "<old text>"` and show the candidates.
2. Use the **impact-analyzer** subagent with the slug, the analysis path, the Figma URLs and the git range.
3. Show the summary, the numbered changed/removed rows and the decisions, then **stop for approval**.
4. After approval, fill impact.md's `## Approval` section and set `Status: APPROVED`. Ask whether to
   apply it now with **test-case-writer**, plus **design-mapper** if design refs are superseded.
