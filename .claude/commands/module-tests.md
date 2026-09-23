---
description: Write pytest + Playwright tests for a mapped module (test-case-writer), from its module spec
argument-hint: <module slug> [roles or screens to focus on]
---

Turn a module spec into runnable tests. The module must already be mapped with `/map-module`.

Inputs from the user:

$ARGUMENTS

## 1. Check the spec is ready
- `automation/specs/modules/<slug>/module.md` and `module.yml` must exist.
  If they don't, run `/map-module <slug>` first.
- The spec's suspected bugs and blocking questions must be answered (the `/map-module` checkpoint).
  If any are open, show them and stop: ids and assertions depend on those answers.

## 2. Write the tests (test-case-writer subagent)
Pass:
- the module spec path, which is its requirements source — **keep its ids**
- the module.yml path (routes, endpoints, data cost)
- the design flow path if the module has one
- the target folder `automation/`, and the role folders its tests belong in
- the user's constraints, and the data cost limit ("don't consume more than N companies per run")

It writes locators, page objects and tests, and adds a traceability section to `module.md`.

## 3. Report
- Coverage table: requirement → tests / manual / not_implemented_yet.
- Files created, one line each.
- How to run it, including which session must be saved first.
- The data cost of one full run.
- Gaps and open questions.
- `python -m impact.coverage --gaps` after the run, so the user sees what's still uncovered.

Don't run the tests yourself unless the user asks: some create real deals.
