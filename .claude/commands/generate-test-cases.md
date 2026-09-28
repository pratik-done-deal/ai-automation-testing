---
description: Turn a feature's analysis into scenarios and test cases in plain English, for review before any script is written
argument-hint: <feature slug> [platform URL] [figma-url]
---

Run only the test-case step: the plain-English scenarios and cases your QA team reviews. No code.

Inputs from the user:

$ARGUMENTS

## 1. Check the inputs
- `automation/specs/prd/<slug>.analysis.md` must exist. If it doesn't, run `/analyze-prd` first — the
  analysis is the requirements source and its ids must be kept.
- `automation/specs/features/<slug>/impact.md` is optional but useful: its "Files to change" tells the
  generator which cases land in existing files. If it exists and isn't `APPROVED`, say so — the
  generator will treat it as a draft.
- If the analysis `Status` is `WAITING`, show its blocking questions and ask whether to answer them now
  or let the generator record them as assumptions.

## 2. Generate (test-case-generator subagent)
Pass the slug, the analysis path, the impact.md path if there is one, the platform URL (default
`https://qa.done.deals/`) and the Figma URL if there is one.

## 3. Review in the chat. ALWAYS STOP
**Paste the scenario overview, then every scenario with its test cases underneath, in full** — this is the review, don't summarise it.
Then show the happy flow as its ordered list of ids, the counts by priority, the requirements with no
case, and the assumptions.

Ask the user to approve, or to change or drop rows ("all except S2-03", or "drop S3"). Apply their edits to
`automation/specs/features/<slug>/test-cases.md`, fill its `## Review` section with the date, and set
`Status: APPROVED`.

## 4. Next
Once approved, the scripts come from **test-script-writer** — offer to run it, or point at
`/new-feature-tests` for the full pipeline.
