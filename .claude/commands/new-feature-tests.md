---
description: PRD (+ optional Figma) → requirements → impact on existing tests → test cases in plain English → pytest + Playwright scripts. Three review stops.
argument-hint: <prd file path or pasted PRD text> [platform URL] [figma URL] [feature slug] [git range]
---

The whole QA pipeline for one new feature. It works **before the feature is built**: the PRD says what
is coming, the live platform says what exists now, and the output is a script the team runs the moment
the feature reaches QA to see whether the basics survived.

Four agents, three stops where you review something:

```
1. prd-analyzer        → <slug>.analysis.md          ⏸ answer its questions
2. impact-analyzer     → impact.md (files to change) ⏸ approve the changes
3. test-case-generator → test-cases.md (tables)      ⏸ approve the cases
4. test-script-writer  → pytest + Playwright         → one smoke command
```

Inputs from the user:

$ARGUMENTS

## 0. Pre-flight (you, in the chat) — ask before spending a subagent
- **PRD.** If it's only a Google Docs link, ask for the text: those links are private (HTTP 401). If it
  was pasted into the chat, save it to `specs/prd/<slug>.md` first — **subagents cannot see
  this conversation.**
- **Slug.** Kebab-case, e.g. `top-picks-expert-curated`. Use the user's if they gave one, otherwise
  propose one and say what you chose.
- **Platform URL.** Default `https://qa.done.deals/`. Confirm it if the feature lives elsewhere.
- **Figma is optional.** Don't ask for it. If there's no link, the analysis works from the PRD and the
  live app, which is right for features with no UI change.
- **Git range** (e.g. `main...feature/x`) only if the code already exists. Usually it doesn't.
- Ask about anything else only when a wrong guess would change what gets tested. One round of questions,
  not an interview.

## 1. Analyze the requirements (prd-analyzer subagent)
Pass the PRD **path**, the platform URL, the Figma URL if there is one, and the slug. It walks the live
app with `scripts/explore.py` and writes `specs/prd/<slug>.analysis.md`.

## 2. Stop: the requirements
Show the document path, the `Status`, and the **blocking** questions numbered. If `WAITING`, stop and
ask the user to answer them or say "proceed with assumptions". Write their answers into the analysis
under `## Answers`, or mark the questions as assumptions. If `READY`, say so and continue.

## 3. Impact on existing tests (impact-analyzer subagent)
Pass the slug, the analysis path, and the git range if there is one. It registers
`specs/features/<slug>/feature.yml` and writes `impact.md` — a proposal only.
Skip this step only when the registry has no other entry (nothing exists to affect).

## 4. Stop: approve the changes. ALWAYS STOP
Even when nothing is undecided, stop. Show:
- the summary line and the modules affected
- **the "Files to change" table in full** — this is what the user asked to see
- the `supersede` rows: old requirement, old → new, which tests
- the decisions needed, numbered

Ask the user to approve all, approve with exceptions ("all except 3, 7"), change rows, or answer the
decisions. Don't continue until they reply. Then fill impact.md's `## Approval` with the approved,
changed and rejected rows and today's date, and set `Status: APPROVED` (or `REJECTED` if every row is
rejected — then step 6 writes only the new feature's tests). Then run
`python scripts/check_pipeline.py impact <slug>` and fix what it reports.
If impact.md found nothing affected, say so in one line and continue without waiting.

## 5. Write the test cases (test-case-generator subagent)
Pass the slug, the analysis path, the approved impact.md path, the platform URL, and the Figma URL if
there is one. It writes `specs/features/<slug>/test-cases.md`: scenarios, the happy flow, and
the test cases in plain English, UI and flow only.

## 6. Stop: approve the test cases. ALWAYS STOP
**Paste the scenario overview, then every scenario with its test cases underneath, in full.** This is the review your
QA team actually cares about — don't summarise it. Then show:
- the happy flow as its ordered list of ids
- counts by priority, and how many cases are `manual`
- requirements with no case, and why
- the assumptions, numbered

Ask the user to approve, or to change or drop rows ("all except S2-03", or "drop S3"). Apply their edits to
test-cases.md, fill `## Review`, and set `Status: APPROVED`. Don't continue until they reply. Then run
`python scripts/check_pipeline.py test-cases <slug>` and fix what it reports.

## 7. Write the scripts (test-script-writer subagent)
Pass the approved test-cases.md path, the analysis path, the impact.md path, the slug, the PRD path, the
target folder (the repo root), and any constraint the user gave. Every P0 case gets the `smoke` marker;
behaviour that isn't live yet gets `pending_feature("<slug>")`.

The design track is **opt-in** — only pass a `flow.yaml` if the user ran `/design-checks <slug>` first.

## 8. Report
- Coverage: test case → test node id, or `manual`.
- **The smoke command**, exactly as the writer gave it, plus the login setup and any `.env` values.
- Existing tests changed: superseded, their new pending versions, and the edits.
- Files created or changed.
- Verification results, and how many tests were collected, plus the output of
  `python scripts/check_pipeline.py all <slug>`.
- Gaps and open questions.
- **When it ships:** run `/ship-feature <slug>` to flip the markers so the pending tests start running.

Don't run the tests yourself unless the user asks: they create real deals.
