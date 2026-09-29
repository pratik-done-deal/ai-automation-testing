---
description: Map an existing module of the platform into a module spec (surface-mapper), with a review checkpoint
argument-hint: <module slug> [scope description] [figma-url if the design is current] [walk]
---

Backfill coverage for a part of the platform that was built before this pipeline. New features don't
come this way: they have a PRD and go through `/new-feature-tests`.

Inputs from the user:

$ARGUMENTS

## 1. Prepare
- Pick a kebab-case slug, e.g. `buyer-cue-card`, and a requirement prefix, e.g. `BUY-CUE`.
  Check `specs/modules/` and `python -m impact.index` so neither is already taken.
- If the user asked for a QA walk, check `auth/<role>.json` exists. If it doesn't, tell them
  to run `python scripts/save_auth_state.py <role>` and log in, then continue.
- Pass a Figma URL only if the user says that design is still current.

## 2. Map it (surface-mapper subagent)
Pass the slug, the prefix, the scope description, the Figma URL if current, and whether to walk it on
QA with which role. It writes `specs/modules/<slug>/module.md` and `module.yml`.

## 3. Checkpoint (you, here). ALWAYS STOP
Show the user:
- requirement counts by type, and the data cost line
- the **suspected bugs**, numbered — for each, ask: requirement or bug?
- the **blocking** questions, numbered
- anything the mapper couldn't check

Wait for the answers. Then record them in `module.md`: a bug becomes a row marked
`suspected bug — not asserted` with the reason, and answered questions move into the requirement
table. Don't let the writer start until this is done, because the ids are permanent.

## 4. Offer the next step
Ask whether to write the tests now with `/module-tests <slug>`.
