# Impact of Hot Lead Refinement & Engagement Visibility on existing automation
Status: APPROVED
Signals: footprint (/admin/leads, /admin/deals, /buyer/cue-card/:uid) + old-copy search | git range: none: no code yet (engagement UI baseline is `qa` commit d8166b264, not on `main`) | modules affected: none mapped (admin-leads ADM-LDS and admin-deals ADM-DLS are `todo` in specs/modules/README.md)

## Summary
0 existing requirements affected: supersede 0, edit 0, undecided 0.
0 test files to change, 0 new tests from this step (new HLE tests come from test-case-generator), 0 shared symbols to touch.

The suite has no coverage of the admin Investor Leads listing (Hot Leads / Expired Hot Leads toggles, flame icon), the Unverified Deals tab, its engagement columns, "-" cells or the engagement modal. None of the old copy the feature reworks ("CC Views", "Doc Views", "Engagement for", "POC Email", "Hot Lead", "Expired Hot", "Unverified Deals") appears in any constant, locator, page object, test or design step. Everything this feature changes is new coverage, not a change to existing coverage.

## Files to change
| # | File | New or edit | What changes | Why |
|---|---|---|---|---|
| - | (none) | - | - | No existing test, page object, locator or constant asserts behaviour this feature changes. |

## Affected requirements
| # | Old req | Old behaviour | New behaviour (new id) | Verdict | Evidence |
|---|---|---|---|---|---|
| - | (none) | - | - | - | No module or feature requirement covers hot-lead logic or deal engagement. `impact.index --req` / `--copy` return nothing for these. |

## Shared symbols
| # | Symbol (file:line) | Edit | Why it stays backward compatible |
|---|---|---|---|
| - | (none) | - | - |

## Checked and unaffected
1. `test_cases/admin_test_cases/test_admin_document_request.py::test_biz_edit_deal_state_has_no_document_request_step` (DR-23, DR-24): leave. It opens `/admin/deals` on the default All Deals tab and clicks the first `.deal-action-container` action. The feature changes only the Unverified Deals tab, and All Deals keeps its name in Figma. `Copy.ADMIN_EDIT_DEAL_TITLE` ("Edit deal state for D") is not touched by the feature.
2. `test_cases/admin_test_cases/test_admin_document_request.py::test_biz_user_cue_card_has_no_express_interest_or_request_step` (DR-23): leave. The admin cue card is not in scope.
3. `test_cases/admin_test_cases/test_admin_document_request.py::test_data_room_topics_card_only_when_request_exists` (DR-46/47, xfail): leave. It covers the deal-notes Data Room tab, not the listing.
4. `pages/admin_module/admin_deal_page.py` (`AdminDealPage`, `AdminCueCardPage`): leave. Deal-notes page and admin cue card only; nothing covers the listing or its modal.
5. `constants.py` `Copy.ADMIN_*` (lines 119-123): leave. None of the constants names an engagement column, the modal, or a hot-lead label.
6. `test_cases/buyer_test_cases/test_buyer_journey.py` (ordered journey), `test_cases/e2e/test_phase1_buyer_requests.py`, `test_phase2_*`: leave. They open cue cards from `/buyer/browse` via View Listing. `NewCueCard` calls `useBatchTimeTracker()` for every buyer on `qa` (src/Component/NewCueCard/index.js:129), so these runs already send time-spent data, but no test asserts on it or on hot status. The C1/C2 hot-lead change is backend-only and changes no buyer-visible behaviour. Data side effect only; see decision 2.
7. `pages/buyer_module/buyer_browse_page.py`, `buyer_cue_card_page.py`: leave. Navigation and cue-card fetch are unchanged; no `pocUid` handling in the suite.
8. `test_cases/api/test_document_request_api.py`: leave. Deal capture/interest payloads are unchanged by this feature.
9. `buyer-login` module (BUY-LGN-51/52, `pocUid` prefill): leave. POC deep links may pass through `/buyer/login?pocUid=`, but the feature does not change login. `/buyer/login` was left out of the footprint on purpose, because it only matched unrelated login tests.
10. `test_cases/seller_test_cases/test_accept_interest_modal.py`: leave. The seller surface is not touched. Seller hot logic is unchanged (C4).
11. Design track: `specs/features/data-room-document-request/flow.yaml` step `admin-1-data-room` covers the deal-notes Data Room tab, not Unverified Deals. No flow step covers a redesigned screen.

## Decisions needed
1. **deferrable**: No admin auth state exists (`automation/auth/` holds only `buyer.json`). The existing `admin_page` tests, and every new HLE admin test, skip or fail until someone runs `python scripts/save_auth_state.py admin`. That doesn't block this proposal, but the admin screens were never walked, so the "no impact" verdict rests on the suite plus `qa` code only.
2. **deferrable**: The buyer journey and phase 1 express interest on companies with the shared test buyer, so those leads are hot through express_interest for 14 days. The new HLE negative cases (HLE-04, HLE-10, HLE-12) need a buyer lead the existing suite has not touched. Should test-case-generator require a dedicated buyer/POC account for HLE flows, separate from `buyer.json`, so the two don't interfere? (Recommended: yes.)
3. **deferrable**: Should `admin-leads` (ADM-LDS) and `admin-deals` (ADM-DLS) be mapped with /map-module before or after this feature ships? Until one is mapped, `modules:` stays empty and /ship-feature has no module spec to fold HLE requirements into.

## Approval
2026-09-27. No rows to approve: no existing test, page object, locator or constant is affected, so the pipeline continued without waiting (per /new-feature-tests step 4).
- Decision 1 (admin auth state): acknowledged. The HLE admin tests need `python scripts/save_auth_state.py admin` before they can run.
- Decision 2 (dedicated buyer/POC account for HLE flows): assumed yes, as recommended. The HLE hot-lead flows use a buyer lead the existing suite doesn't touch, kept separate from `buyer.json`.
- Decision 3 (map admin-leads / admin-deals): deferred until after this feature. `modules:` stays empty for now.
