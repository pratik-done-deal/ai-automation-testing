---
description: Analyze a PRD into a grounded requirements document, without writing tests or code
argument-hint: <prd file path or pasted PRD text> [platform URL] [figma-url] [feature slug]
---

Use the **prd-analyzer** subagent on:

$ARGUMENTS

- If the PRD was pasted in this conversation, save it to `automation/specs/prd/<slug>.md` first and pass
  that path. The subagent can't see this conversation.
- If the PRD is only a Google Docs link, ask the user to paste the text. Those links are private.
- Pass the platform URL (default `https://qa.done.deals/`): the agent walks the live app to learn how
  things work today.
- **Figma is optional.** Don't ask for it — plenty of features change no design.

When it finishes, show the user:
- the analysis file path and its `Status`
- the blocking questions, numbered
- the counts (requirements by type, how many are `manual`, how many already exist today)
- the top gaps

Then ask whether to answer the questions now, or carry on through `/new-feature-tests` for the rest of
the pipeline.
