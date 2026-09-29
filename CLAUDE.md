# ai-automation-testing

UI automation for **donedeal-web** (the Done Deal web app): pytest + Playwright tests, written by a
pipeline of Claude agents from each feature's PRD. The same suite also lives as `automation/` inside
the donedeal-web repo; `paths.py` works from either place.

## Where the app code is
The agents read donedeal-web's source (`src/...`) to check copy, selectors and changed files. It is the
checkout at `DD_APP_ROOT` (`.env`), by default `../donedeal-web`, which `.claude/settings.json` gives
Claude access to. A path like `src/Component/...` in an agent or spec means that checkout, not this repo.

## New feature: the pipeline (`/new-feature-tests`)
1. **prd-analyzer** → `specs/prd/<slug>.analysis.md` (requirement ids like SSF-01, open questions). Stop: the user answers.
2. **impact-analyzer** → `specs/features/<slug>/impact.md` + `feature.yml`. Stop: the user approves.
3. **test-case-generator** → `specs/features/<slug>/test-cases.md` (plain English). Stop: the user approves.
4. **test-script-writer** → locators, page objects and tests in this repo.

Single steps: `/analyze-prd`, `/impact-check`, `/generate-test-cases`. Existing screens: `/map-module`
(surface-mapper) then `/module-tests`. Figma checkpoints (opt-in): `/design-checks`. After release:
`/ship-feature` flips `feature.yml` to shipped so `pending_feature` tests run as normal tests.

## Layout
`locators/<role>/` selectors · `pages/<role>_module/` page objects · `test_cases/<role>_test_cases/`,
`test_cases/e2e/` tests · `utils/` data helpers · `constants.py` UI copy · `conftest.py` shared fixtures
(one logged-in context per role, failure screenshots) · `impact/` impact tools · `designcheck/` Figma
checks · `specs/` modules, features, PRDs.

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
```
