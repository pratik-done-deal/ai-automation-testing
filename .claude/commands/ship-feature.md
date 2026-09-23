---
description: Mark a feature as shipped: fold its requirements into the module specs, flip the lifecycle markers, refresh coverage
argument-hint: <feature slug>
---

Run this when a feature is live on the environment the suite runs against. It turns the feature from
a pending change into part of the modules' living specs.

Inputs from the user:

$ARGUMENTS

## 1. Check it really shipped
From `automation/`:
```bash
DD_SHIPPED=<slug> python -m pytest -m "pending_feature" --collect-only -q
```
Ask the user to run that feature's pending tests against the environment. If they still fail, stop:
it hasn't shipped. (A strict XPASS on a pending test during a normal run is the same signal.)

## 2. Flip the status
Set `status: shipped` in `automation/specs/features/<slug>/feature.yml`.
From now on its `pending_feature` tests run and the `superseded_by` tests they replaced are skipped.

## 3. Fold the requirements into the module specs
For each module in the feature's `modules:` list, in `automation/specs/modules/<module>/module.md`:
- Add the feature's requirement rows to the module's requirement table, **keeping their original ids**
  (DR-06 stays DR-06) and setting Source to `feature:<slug>`.
- Mark each requirement the feature replaced as `superseded by <new id> (<slug>)`. Keep the row: it's
  the history of that screen.
- Update the traceability section with the new tests.
- Add to `module.yml`:
  ```yaml
  changes:
    - by: <slug>
      date: <YYYY-MM-DD>
      shipped: <YYYY-MM-DD>
      requirements: {DR-06: added, BUY-CUE-04: superseded}
  ```
The feature folder stays as history: don't delete `analysis.md`, `impact.md`, `flow.yaml` or `refs/`.

## 4. Design refs
Steps in older flows marked `superseded_by: <slug>` now stop being checked automatically. Confirm the
new feature's own flow has a step for each screen it replaced.

## 5. Refresh and report
```bash
python -m impact.coverage --out specs/COVERAGE.md
```
Show the user:
- the requirements folded into which modules
- the tests that now run, and the superseded ones now skipped
- the coverage totals before and after
