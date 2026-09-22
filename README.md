# Data Room Document Request: UI automation

pytest + Playwright suite for the **Data Room Document Request Management** PRD
(Figma: *Sprint-Work > Data_Room_Document_Request*).

## How a run works

The seller's login only exists **after** the buyer expresses interest in their company, so a
run has two phases, with a gap in between for you to get the seller's credentials:

```
Phase 1 (buyer)              you                          Phase 2 (seller)
express interest + request   get seller credentials,      seller sees request, uploads,
docs on seller cue cards ->  save seller session      ->  accepts; buyer sees fulfilment;
writes run_state/phase1.json                              admin checks
```

## One-time setup

```bash
cd automation
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env

python scripts/save_auth_state.py buyer    # log in by hand in the browser, then press Enter
python scripts/save_auth_state.py admin    # use a biz user
```

Sessions are saved to `auth/` (git-ignored). Re-run the script when one expires.

## Phase 1: buyer (no seller login needed)

The buyer works from **/buyer/browse**, repeating for each company:

1. Click a mini cue card's **View Listing** (the cue card opens in a new tab).
2. **Express Interest** → pick the first free date and time → **Request Call**.
3. Tick MIS, Audited Financials and Cap Table → **Send request (3)**, then check the cue card shows them.
4. Close the tab, back to /buyer/browse, next card.

Companies the buyer already expressed interest in are skipped automatically.

```bash
pytest -m phase1 --headed                              # 1 company (default)
DD_BROWSE_INTEREST_COUNT=3 pytest -m phase1 --headed   # 3 companies
```

Each deal is printed (`recorded: S6604 : Fintech > Payments | uid … | deal …`) and saved to
`run_state/phase1.json`. Use that to get the right sellers' credentials.

## Phase 2: seller (after you have the seller's credentials)

```bash
python scripts/save_auth_state.py seller                          # log in as that seller
pytest -m phase2                                                  # phase 1 used one uid
DD_PHASE2_SELLER_CUE_CARD_UID=<uid1> pytest -m phase2             # phase 1 used several uids
```

With several sellers, repeat for each one: save that seller's session, then run with its uid.

## Buyer journey (one cue card, no reloads)

`tests/buyer/test_buyer_journey.py` opens **one** company from /buyer/browse and runs every buyer
check on that tab, in order: slot modal → **Request Call (real)** → document step → **Send request
(real)** → after-submit checks. Each test continues from where the previous one left the page. If a
step fails, the rest are skipped. It uses up one company per run and records it in
`run_state/phase1.json`, so phase 2 can use that deal.

## Handy commands

```bash
pytest -m smoke                          # quick check after a deploy
pytest -m "not destructive"              # read-only: creates no deals
pytest -m "not not_implemented_yet"      # skip PRD items that aren't built yet
pytest tests/buyer/test_buyer_journey.py --headed   # buyer journey: one cue card, tests in order, no reloads
pytest -m phase1 --headed --slowmo 300   # watch it in a visible browser
```

The HTML report is written to `reports/report.html`.

## Test data

Express interest can happen only once per buyer/company pair, so the tests use up data:

| Variable | Used by | Notes |
|---|---|---|
| `DD_BROWSE_INTEREST_COUNT` | phase 1 | How many companies to pick from /buyer/browse (default 1). Picked companies are recorded and never reused. |
| `DD_PHASE2_SELLER_CUE_CARD_UID` | phase 2 | Which phase 1 uid the saved seller session belongs to (only needed with several). |
| `DD_FRESH_COMPANY_UIDS` | buyer + api tests | One uid per destructive test (about 15 per full run). **The last uid is kept for read-only tests** and is never submitted. |
| `DD_SELLER_COMPANY_ID`, `DD_BUYER_DISPLAY_NAME` | phase 2 | Optional. Blank = the logged-in seller's own company and the newest Interest Received row. |
| `DD_ADMIN_DEAL_*_UID` | admin tests | Existing deals, read-only. |

A test that is missing data **skips** rather than fails.

## Coverage map

The requirement-by-requirement mapping (DR-01 to DR-53 → test functions) is in
[`docs/prd/data-room-document-request.test-plan.md`](../docs/prd/data-room-document-request.test-plan.md),
generated from the `DR-xx` ids referenced in each test.

### Marked `not_implemented_yet` (strict xfail: they fail until the feature is built)

- **DR-03**: the other 4 PRD doc types (Registration & Licenses, ITR, GST Filing, Credit rating) in the buyer step.
- **DR-04**: buyer options grouped into Company / Financial / Others.
- **DR-21**: buyer deals tab shows requested docs with pending/fulfilled status.
- **DR-22**: buyer can raise a request at introduction_pending. There's no design yet, so the test asserts the stored outcome.
- **DR-46 + DR-47** (one paired test): admin deal → Data Room "Topics for the intro call" card, shown only when a request exists.

Once one of these starts passing, strict xfail reports it as `XPASS(strict)`. Remove the marker then.

### Not automated (check manually)

- **Seller EI / intro-pending email** (DR-25 to DR-27): documents and note appear only when a request exists; per-doc upload status.
- **Daily AI summary** (DR-50): fulfilled vs. still-open diff from a daily backend job.
- **Pending-action reminder, on_hold pause/resume** (DR-49, DR-51): run on the backend scheduler with no UI.
- **Success metrics** (DR-52): there's no buyer "request sent" analytics event yet.

## Known design / PRD / code gaps (raise with product)

1. PRD section 8 lists 8 document types; the buyer modal offers only 4 (Pitchdeck, MIS, Cap Table, Audited Financials) because `SuccessView.DOCUMENT_REQUEST_OPTIONS` comments out the rest. The tests follow the code and still check that every option is in the PRD list.
2. Figma modal title reads "Express Interest in this company"; the app shows "Express Interest". The label reads "slots for meet" in Figma and "slots for meeting" in the app. Tests match either.
3. The seller accept modal always pins a mandatory Pitch Deck row, even when the buyer didn't request one.

## Structure

```
automation/
├── conftest.py          role contexts, API clients, test data pools
├── config.py            .env settings
├── constants.py         doc keys/labels and UI copy mirrored from src/
├── pages/               page objects (buyer cue card, slot modal, success modal, seller deals, accept modal, admin deal)
├── utils/               API client, response rewriting, shared flows, phase 1 → 2 hand-off
├── scripts/             save_auth_state.py
└── tests/{buyer,seller,admin,api,e2e}
```
