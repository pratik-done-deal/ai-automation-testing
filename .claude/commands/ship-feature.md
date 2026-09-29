---
description: Mark a feature as shipped so its pending tests start running
argument-hint: <feature slug>
---

Run this when the feature is live on the environment the suite runs against. It flips the lifecycle
markers: `pending_feature("<slug>")` tests stop being xfail and start counting, and the
`superseded_by("<slug>")` tests they replaced get skipped and kept as history.

Inputs from the user:

$ARGUMENTS

## 1. Check it really shipped
Ask the user to run the feature's pending tests against the environment:
```bash
DD_SHIPPED=<slug> python -m pytest -m pending_feature -k <slug-or-file>
```
If they still fail, stop: it hasn't shipped. (A strict XPASS on a pending test during a normal run is
the same signal, the other way round.)

For a one-off run against an environment that's ahead or behind, `DD_SHIPPED=<slug>` and
`DD_UNSHIPPED=<slug>` override the status without editing anything.

## 2. Flip the status
Set `status: shipped` in `specs/features/<slug>/feature.yml`. That's the whole switch.

## 3. Fold into the module specs — only if `modules:` is non-empty
Most features leave `modules: []`, and then there is nothing to fold: say so and skip to step 4.

Otherwise, for each module listed, in `specs/modules/<module>/module.md`:
- add the feature's requirement rows to the module's table, **keeping their original ids** (DR-06 stays
  DR-06), with Source `feature:<slug>`
- mark each requirement the feature replaced as `superseded by <new id> (<slug>)` — keep the row, it's
  the history of that screen
- add the new tests to the traceability section
- append to `module.yml`:
  ```yaml
  changes:
    - by: <slug>
      date: <YYYY-MM-DD>
      shipped: <YYYY-MM-DD>
      requirements: {DR-06: added, BUY-CUE-04: superseded}
  ```

Never rewrite an older analysis. The feature folder stays as history: keep `analysis.md`, `impact.md`,
`test-cases.md` and anything under `refs/`.

## 4. Refresh and report
```bash
python -m impact.coverage --out specs/COVERAGE.md
```
Show the user:
- the tests that now run, and the superseded ones now skipped
- the requirements folded into which modules, if any
- the coverage totals before and after
