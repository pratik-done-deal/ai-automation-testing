---
description: New feature → requirements analysis → design checkpoints → functional + design tests (prd-analyzer → design-mapper → test-case-writer)
argument-hint: <figma-section-url> <prd file path or pasted PRD text> [feature slug]
---

Set up automated functional **and** design testing for a new feature. The AI work happens once, here.
After this, `pytest … --design` re-checks everything with no AI and no Figma calls.

Inputs from the user:

$ARGUMENTS

## 0. Prepare
- Choose a kebab-case slug, e.g. `data-room-document-request`. Use the user's, if given.
- If the PRD was pasted, save it to `docs/prd/<slug>.md`. Subagents can't see this conversation.
- If the PRD is only a Google Docs link, ask for the text first. Those links are private.

## 1. Analyze (prd-analyzer subagent)
Pass the PRD path, the Figma URL, and "purpose: tests". It writes `docs/prd/<slug>.analysis.md`.

## 2. Checkpoint (you, here)
Show the checkpoint status and the **blocking** questions, numbered. If `WAITING`, stop and ask the
user to answer or say "proceed with assumptions". Record the answers in the analysis document.

## 3. Map the design (design-mapper subagent)
Pass the slug, the analysis path and the Figma URL. It writes `docs/features/<slug>/flow.yaml`,
saves `refs/` by script and drafts `known_differences.yml`.
- If it reports that `FIGMA_TOKEN` is missing or the rate limit was hit, show the user the exact
  `sync_refs` command to run. Test writing can continue: steps without refs are reported as such
  at run time.

## 4. Write the tests (test-case-writer subagent)
Pass:
- the analysis path
- the flow.yaml path
- the PRD path and the Figma URL
- the target folder (default `automation/`)
- the user's constraints

It places a `design.check()` at each flow step's `when`.

## 5. Report to the user
- The coverage table: requirement → tests / manual / not_implemented_yet.
- The design checkpoints: step → test.
- The files created.
- The run commands, in order: login setup, then
  `pytest <tests> --design --headed`, phase 1 / phase 2 when a later role's login depends on an earlier
  action, and `DD_DESIGN_STRICT=1` for release gates.
- Open questions and gaps.

Don't run the tests yourself unless the user asks: they create real deals.
