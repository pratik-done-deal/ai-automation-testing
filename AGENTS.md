# ai-automation-testing

UI automation for **donedeal-web** (the Done Deal web app): pytest + Playwright tests, written by a
pipeline of AI agents from each feature's PRD. The pipeline runs in **Claude Code** and in **Codex**
from the same instruction files and produces the same files. The same suite also lives as
`automation/` inside the donedeal-web repo; `paths.py` works from either place.

This file is read by Codex directly and by Claude Code through `CLAUDE.md`. Keep shared rules here.

## Where the app code is
The agents read donedeal-web's source (`src/...`) to check copy, selectors and changed files. It is the
checkout at `DD_APP_ROOT` (`.env`), by default `../donedeal-web`. A path like `src/Component/...` in an
agent or spec means that checkout, not this repo.

## New feature: the pipeline (`new-feature-tests`)
1. **prd-analyzer** → `specs/prd/<slug>.analysis.md` (requirement ids like SSF-01, open questions). Stop: the user answers.
2. **impact-analyzer** → `specs/features/<slug>/impact.md` + `feature.yml`. Stop: the user approves.
3. **test-case-generator** → `specs/features/<slug>/test-cases.md` (plain English). Stop: the user approves.
4. **test-script-writer** → locators, page objects and tests in this repo.

Single steps: `analyze-prd`, `impact-check`, `generate-test-cases`. Existing screens: `map-module`
(surface-mapper) then `module-tests`. Figma checkpoints (opt-in): `design-checks`. After release:
`ship-feature` flips `feature.yml` to shipped so `pending_feature` tests run as normal tests.

### One set of instructions for both tools
- **Commands:** `.claude/commands/<command>.md`, the orchestration and the review stops.
- **Agents (steps):** `.claude/agents/<agent>.md`, what each step does and the exact format of its output.

The folder is named `.claude` for Claude Code's sake; Codex reads the same files (see below). Change a
step's behaviour or format in that one file, never in a tool-specific copy.

### Same output from either tool
- Each step writes its file in the format its agent file defines, then runs
  `python scripts/check_pipeline.py <analysis|impact|test-cases|scripts> <slug>` and fixes every error
  until it prints `OK`. After filling an `## Approval` or `## Review` section, run it again.
- A step works only from the files and inputs its agent file lists, never from memory of the chat.
- Stops are the same in both tools: stop, show what the command says to show, and wait for the user.
- Questions go into the document and the step's final report, not to the user mid-step.
- If an input the user gave can't be read (a Figma link with no Figma tool, a private Google Doc, a
  missing login), stop and say so. Don't carry on without it: the other tool would have read it.

## Running the pipeline in Codex
Codex has no slash commands or subagents for this repo, so:

- **Starting a command:** the user types the command name **without a slash**, e.g.
  `new-feature-tests specs/prd/top-picks.md` or `generate-test-cases star-seller-fundraising`.
  Read `.claude/commands/<command>.md` and follow it. `$ARGUMENTS` in it means the text the user typed
  after the command name. Ignore the YAML front matter at the top of each file.
- **"Use the X subagent":** read `.claude/agents/X.md` and carry out that step yourself, as its
  instructions say. Treat it as a fresh start: re-read the inputs it lists from disk instead of relying
  on earlier turns. Finish with its "Final report to the caller", then continue the command (the
  "caller" is you).
- **Stops:** where a command says stop, end your turn and wait for the user's reply.
- **Figma:** the agents use the Figma MCP tools (`get_metadata`, `get_screenshot`,
  `get_design_context`). Configure the Figma MCP server in Codex (README: "Running the pipeline in
  Codex").
- **Network and the app checkout:** `scripts/explore.py` and the tests reach QA over the network, and
  the agents read `../donedeal-web`. Codex must run with network access and with that folder writable
  or readable (README).

## Running the pipeline in Claude Code
Type the command as a slash command (`/new-feature-tests ...`). Each step runs as the subagent of the
same name. `.claude/settings.json` gives Claude access to `../donedeal-web`.

## Layout
`locators/<role>/` selectors · `pages/<role>_module/` page objects · `test_cases/<role>_test_cases/`,
`test_cases/e2e/` tests · `utils/` data helpers · `constants.py` UI copy · `conftest.py` shared fixtures
(one logged-in context per role, failure screenshots) · `impact/` impact tools · `designcheck/` Figma
checks · `specs/` modules, features, PRDs · `scripts/check_pipeline.py` output format checks.

## Conventions the user set
- **Pick test data by browsing the app**, not from uids in `.env` (e.g. `utils/ssf_browse.py`: Sellers
  list → tab → search the S-id → Actions "View").
- **No email or inbox tests**; those stay manual.
- Buyer → seller flows run as **phase 1 / phase 2** (a seller's login exists only after a buyer's interest).
- Mark tests that change data `destructive`; never delete QA data the user didn't agree to.
- Open browsers only through the suite's fixtures/helpers (`new_role_page`, `admin_module_page`, ...), so a
  failing test's tabs are screenshotted into Allure *Tear down → failure_screenshots*.

## Running
```bash
source .venv/bin/activate
python scripts/save_auth_state.py admin          # saved logins go to auth/ (git-ignored)
pytest test_cases/... --headed                    # watch it; DD_APP_URL picks QA or localhost
DD_SHIPPED=<slug> pytest ...                      # treat an unshipped feature as shipped (local app)
allure serve reports/allure                       # report; reports/report.html also exists
python scripts/check_pipeline.py all <slug>       # check a feature's pipeline files
```
