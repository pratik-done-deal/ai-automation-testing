---
description: Analyze a PRD (+ Figma) into a grounded requirements document, without writing tests or code
argument-hint: <prd file path or pasted PRD text> [figma-url ...] [feature name]
---

Use the **prd-analyzer** subagent on:

$ARGUMENTS

- If the PRD was pasted in this conversation, save it to `docs/prd/<feature-slug>.md` first and
  pass that path. The subagent can't see this conversation.
- If the PRD is only a Google Docs link, ask the user to paste the text. Those links are private.

When it finishes, show the user:
- the analysis file path
- the checkpoint status
- the blocking questions, numbered
- the top gaps

Then ask whether to answer the questions now or go on to `/test-cases`.
