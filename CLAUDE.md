@AGENTS.md

## Claude Code specifics
- The pipeline commands are slash commands (`/new-feature-tests`, `/analyze-prd`, ...) from
  `.claude/commands/`, and each step runs as the subagent of the same name from `.claude/agents/`.
- Those files are shared with Codex (see AGENTS.md): keep them free of Claude-only wording, and put
  anything that must differ between the tools in AGENTS.md's tool sections.
