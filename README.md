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

## Handy commands

```bash
pytest -m smoke                          # quick check after a deploy
pytest -m "not destructive"              # read-only: creates no deals
pytest -m "not not_implemented_yet"      # skip PRD items that aren't built yet
pytest tests/buyer/test_express_interest_slots.py::test_add_second_slot   # one test
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
| `DD_OUTSIDE_PREF_COMPANY_UID` | outside-preference tests | Only opened, never submitted. |
| `DD_SELLER_COMPANY_ID`, `DD_BUYER_DISPLAY_NAME` | phase 2 | Optional. Blank = the logged-in seller's own company and the newest Interest Received row. |
| `DD_ADMIN_DEAL_*_UID` | admin tests | Existing deals, read-only. |

A test that is missing data **skips** rather than fails.

## Coverage map

| PRD item | Tests |
|---|---|
| Story 1: buyer requests documents | `tests/buyer/test_document_request_modal.py`, `test_request_after_submit.py`, `e2e/test_phase1_buyer_requests.py` |
| Only existing doc types, no free text | `test_options_come_only_from_existing_document_list`, `api/…::test_free_text_or_unknown_types_are_rejected` |
| One-time capture / lock | `test_backend_rejects_adding_documents_after_lock`, `api/…::test_second_submission_cannot_extend_request`, `api/…::test_request_locked_after_modal_closed_empty` |
| Edge case: close without selecting | `test_close_without_selection_creates_no_request`, `api/…::test_empty_list_creates_no_request` |
| Buyer sees docs and status (pending/fulfilled) | `test_request_after_submit.py`, phase 2 `test_04`, `test_05` |
| Story 3: seller sees the request while accepting | `seller/test_accept_interest_modal.py`, phase 2 `test_01`, `test_02` |
| Not mandatory: seller isn't blocked | `test_accept_is_not_blocked_by_unfulfilled_non_deck_requests`, phase 2 `test_02` |
| Fulfilment no matter who uploads | phase 2 `test_02` (seller UI), `test_05` (API upload) |
| Edge case: non-requested upload | phase 2 `test_03` |
| Edge case: partial upload keeps request open | phase 2 `test_04` |
| Single deal note holds the request | phase 2 `test_06` |
| Story 4: admin Data Room | phase 2 `test_07`, `admin/test_admin_document_request.py` |
| Story 5: biz user skips the step | `admin/…::test_biz_user_moving_deal_never_sees_document_request_step` |
| Slot step (Figma calendar / time / outside preferences) | `tests/buyer/test_express_interest_slots.py` |

### Marked `not_implemented_yet` (expected to fail until built)

- **Admin > Deal > Data Room "Topics for the intro call" card**: no frontend code exists for it yet.
- **Buyer deals tab showing requested docs with pending/fulfilled status**: not built yet (the detailed cue card already has it).

### Not automated (check manually)

- **Seller express-interest / intro-pending email** (Story 2): documents and note appear only when a request exists.
- **Daily AI summary** (fulfilled vs. still-open diff): runs as a daily backend job and can't be checked in a single run.
- **Pending-action reminder attached to the note, and on_hold pause/resume**: runs on the backend scheduler with no UI surface.

## Known design / PRD / code gaps (raise with product)

1. PRD section 7 lists 8 document types; the buyer modal offers only 4 (Pitchdeck, MIS, Cap Table, Audited Financials) because `SuccessView.DOCUMENT_REQUEST_OPTIONS` comments out the rest. The tests follow the code and still check that every option is in the PRD list.
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
