---
description: New feature → requirements analysis → impact on existing tests (approval) → design checkpoints → functional + design tests
argument-hint: <figma-section-url> <prd file path or pasted PRD text> [feature slug] [git range of the feature's code]
---

The feature track: a PRD plus its Figma become tests, and the tests of the modules the feature
changes are updated with your approval. The AI work happens once, here. Afterwards `pytest … --design`
re-checks everything with no AI and no Figma calls.

Inputs from the user:

$ARGUMENTS

## 0. Prepare
- Choose a kebab-case slug, e.g. `data-room-document-request`. Use the user's, if given.
- If the PRD was pasted, save it to `automation/specs/prd/<slug>.md`. Subagents can't see this conversation.
- If the PRD is only a Google Docs link, ask for the text first. Those links are private.

## 1. Analyze (prd-analyzer subagent)
Pass the PRD path, the Figma URL, and "purpose: tests". It writes `automation/specs/prd/<slug>.analysis.md`.

## 2. Checkpoint 1: requirements (you, here)
Show the checkpoint status and the **blocking** questions, numbered. If `WAITING`, stop and ask the
user to answer or say "proceed with assumptions". Record the answers in the analysis document.

## 3. Impact on existing tests (impact-analyzer subagent)
Pass the slug, the analysis path, the Figma URL(s) and the git range if given. It registers
`automation/specs/features/<slug>/feature.yml` and writes `impact.md` next to it — a proposal only.
Skip this step only when the registry has no other entry.

## 4. Checkpoint 2: approve the impact (you, here). ALWAYS STOP
Even when nothing is `decide`, stop. Show:
- the summary line and the modules affected
- the numbered **changed** / **removed** rows: old requirement, old → new, tests affected
- the plumbing edits and superseded design steps, briefly
- the decisions needed, numbered

Ask the user to approve all, approve with exceptions ("all except 3, 7"), change rows, or answer the
decisions. Don't continue until they reply. Then fill impact.md's `## Approval` section with the
approved, changed and rejected rows and today's date, and set `Status: APPROVED` (or `REJECTED` when
every row is rejected: the next steps then write only the new feature's tests).
If impact.md found nothing affected, say so in one line and continue without waiting.

## 5. Map the design (design-mapper subagent)
Pass the slug, the analysis path, the Figma URL and the impact.md path. It writes
`automation/specs/features/<slug>/flow.yaml`, saves `refs/` by script, drafts `known_differences.yml`,
and marks approved redesigned steps of older flows `superseded_by: <slug>`.
- If `FIGMA_TOKEN` is missing or the rate limit was hit, show the user the exact `sync_refs` command.
  Test writing can continue: steps without refs are reported as such at run time.

## 6. Write the tests (test-case-writer subagent)
Pass the analysis path, the flow.yaml path, the impact.md path (it applies only approved rows), the
PRD path, the Figma URL, the target folder `automation/` and the user's constraints. New behaviour
that isn't live yet is marked `pending_feature("<slug>")`.

## 7. Report to the user
- Coverage table: requirement → tests / manual / not_implemented_yet.
- **Existing tests changed:** superseded tests, their new pending versions, plumbing edits.
- Design checkpoints: step → test.
- Files created or changed.
- Run commands in order: login setup, then `pytest <tests> --design --headed`, phase 1 / phase 2 when
  a later role's login depends on an earlier action, `DD_DESIGN_STRICT=1` for release gates.
- **When it ships:** run `/ship-feature <slug>`, which folds these requirements into the module specs
  and flips the markers.
- Open questions and gaps.

Don't run the tests yourself unless the user asks: they create real deals.
