---
description: Opt-in: map a feature's Figma frames to automated design checkpoints (design-mapper), so pytest --design can compare screens
argument-hint: <feature slug> <figma-section-url>
---

The design track is **not part of the default pipeline**. Use it only when a feature's visual design
matters enough to check automatically, and a Figma link exists.

Inputs from the user:

$ARGUMENTS

## 1. Check the inputs
- `specs/prd/<slug>.analysis.md` must exist (`/analyze-prd` if not).
- A Figma URL is **required** here — without one there is nothing to compare against. Stop and ask.
- `FIGMA_TOKEN` must be set for the reference sync. If it's missing, the mapping still works; show the
  user the exact `sync_refs` command to run later.

## 2. Map the design (design-mapper subagent)
Pass the slug, the analysis path, the Figma URL and the impact.md path if there is one. It writes
`specs/features/<slug>/flow.yaml`, saves `refs/` by script, drafts `known_differences.yml`,
and marks approved redesigned steps of older flows `superseded_by: <slug>`.

## 3. Report
- The flow steps: id, screen, and the moment (`when`) each is checked.
- Steps whose refs failed to sync, with the command to fix them.
- Tell the user to pass the `flow.yaml` path to **test-script-writer** so it places the
  `design.check()` calls — scripts written without it have no design checkpoints.
- The run command: `pytest <tests> --design`, and `DD_DESIGN_STRICT=1` for a release gate.

Design differences never fail a functional test, and the checks do nothing unless `--design` is passed.
