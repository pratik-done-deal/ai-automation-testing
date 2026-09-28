# Impact of Star Seller Marking — Fundraising Sellers on existing automation
Status: APPROVED
Signals: footprint (/admin/seller, /admin/notes/:uid) + 6 old-copy probes | git range: none: no code yet | modules affected: none mapped (admin-deal-notes ADM-DLN and admin-sellers ADM-SLR are `todo` in specs/modules/README.md)

## Summary
0 existing requirements affected: supersede 0, edit 0, undecided 0.
0 test files to change, 0 new tests from this step (new SSF tests come from test-case-generator), 3 shared symbols to touch additively (biz user session, rows 1-3), all prerequisites for new tests, not changes forced on old ones.

No test, page object, locator or constant in `automation/` touches the admin cue card (`/admin/notes/:uid`), the "Additional Details for this Seller" modal, star marking, the "Star seller requirements" panel, the investment teaser upload, the "Edit Company's Objective" modal or the "Cue card edit" modal. The feature lands on unautomated ground. Its behaviour changes (notably analysis section 3 row 4: the acquisition block toast "Please add an investment teaser in order to mark this seller as a Star Seller." becomes one combined "<item> is missing" message) have no existing assertion to supersede.

## Files to change
| # | File | New or edit | What changes | Why |
|---|---|---|---|---|
| 1 | automation/config.py | edit (additive) | add `biz_user_state: Path = ROOT / os.getenv("DD_BIZ_USER_STATE", "auth/biz_user.json")` next to `admin_state` (line 23), with a `# star-seller-fundraising` comment | no userType 4 session exists; SSF-03..08, 29, 34 and the biz half of SSF-09..35 need one |
| 2 | automation/utils/sessions.py | edit (additive) | add `"biz_user": settings.biz_user_state` to `STATE_BY_ROLE` (line 10) and `"biz_user": "admin/login"` to `LOGIN_PATHS` (line 13) | same; `save_auth_state.py` reads both maps, so it gains the role with no edit of its own |
| 3 | automation/conftest.py | edit (additive) | add a `biz_user_page` fixture beside `admin_page` (line 50): `yield from _role_page(browser, "biz_user")` | new SSF biz-user tests need a page; `require_state` skips them cleanly until auth/biz_user.json is saved |
| 4 | automation/specs/features/star-seller-fundraising/feature.yml | new (written) | registration, footprint /admin/seller and /admin/notes/:uid | step 1 of this agent |

Rows 1-3 are infrastructure for new tests and are proposed here only because they touch shared files; test-script-writer applies them along with the new SSF tests. None changes behaviour for an existing role.

## Affected requirements
| # | Old req | Old behaviour | New behaviour (new id) | Verdict | Evidence |
|---|---|---|---|---|---|
| — | none | — | — | — | no registered module or feature requirement covers star marking, the cue card rail, the objective modal or the teaser upload (`impact.index --req`, `impact.find --feature`, `--copy` probes: 0 requirements, 0 tests) |

## Shared symbols
| # | Symbol (file:line) | Edit | Why it stays backward compatible |
|---|---|---|---|
| 1 | `Settings.admin_state` neighbourhood, automation/config.py:23 | add `biz_user_state` | new field; `admin_state` and its env var untouched |
| 2 | `STATE_BY_ROLE`, `LOGIN_PATHS`, automation/utils/sessions.py:10,13 | add key `biz_user` | dict additions only; existing roles and `save_auth_state.py` usage unchanged |
| 3 | `admin_page` neighbourhood, automation/conftest.py:50 | add `biz_user_page` fixture | new fixture name; no existing test requests it |

## Checked and unaffected
- test_cases/admin_test_cases/test_admin_document_request.py (DR-23, DR-24, DR-46/47): uses `/admin/cue-card/:uid` and `/admin/deal-notes/:uid`, not `/admin/notes/:uid`; no star, objective or teaser assertions.
- pages/admin_module/admin_deal_page.py (AdminDealPage, admin cue card view at /admin/cue-card/:uid): different container and route from the admin notes cue card; no locator for the right rail, Additional Details or objective modal.
- test_cases/e2e/test_hot_lead_flows.py S7-02 (HLE-06) and utils/hle_data.py `teaser_link`: opens an already-unlocked investment teaser as a buyer; the feature changes neither teaser access nor buyer views, only the admin-side gate on objective change.
- test_cases/admin_test_cases/test_admin_deals_unverified_engagement.py HLE-17 (teaser doc views): counts views; star status and objective are not read.
- test_cases/admin_test_cases/test_admin_leads_hot_leads.py: "star"/"primary" hits are `enumerate(start=)` and the engagement Primary chip, unrelated.
- Seller Data Room / pitch deck tests (test_accept_interest_modal.py DR-29..31, test_phase2_seller_fulfils.py, test_phase2_no_request_deal.py): the seller-side "Pitch Deck *" row in the accept-interest modal is not changed; the new pitch deck upload surface is in the admin objective modal only.
- test_cases/buyer_test_cases/test_buyer_journey.py and test_phase1_buyer_requests.py: buyer browse and cue card; browse picking does not filter on star status, and star marking is not a buyer-visible flow in the analysis.
- test_cases/buyer_test_cases/test_buyer_login.py (buyer-login module, BUY-LGN-*): unrelated screens.
- utils/api_client.py `capture_interest` (`openToFunding`/`openToAcquisition`): buyer interest payload, not the seller's company objective.
- Design track: data-room-document-request flow.yaml steps buyer-1-cue-card-before and buyer-4-cue-card-after matched only on the shared phrase "Company Highlights" in the buyer cue card text list; the feature does not redesign the buyer cue card. No flow.yaml covers the admin cue card.

## Decisions needed
1. **non-blocking**: `scripts/save_auth_state.py` line 5 says to save `admin` with "a biz user", while the analysis confirmed auth/admin.json is userType 2 (no call/MIS row in the panel) and existing DR tests name the admin session "biz/admin". Proposed: keep auth/admin.json as the userType 2 admin and add a separate `biz_user` role (rows 1-3). Confirm, and provide a userType 4 QA login to save as auth/biz_user.json; until then every biz-user SSF test skips.
2. **non-blocking**: no module spec covers /admin/notes/:uid or /admin/seller. The new SSF tests will be the first automation there, with new page objects for the admin cue card rail, the Additional Details modal and the objective modal. Mapping `admin-deal-notes` (ADM-DLN) with /map-module later would give today's acquisition star rules (e.g. the one-item toast) module requirement ids; if mapped after this feature ships, map the combined message as current behaviour rather than as superseded history.

## Approval
Approved by the user on 2026-09-28 ("approve all").
- Approved: rows 1, 2, 3, 4.
- Changed: none.
- Rejected: none.
- Decision 1: keep auth/admin.json as the userType 2 admin, and add a separate `biz_user` role. The userType 4 QA login is still to be provided; biz-user tests skip until auth/biz_user.json is saved.
- Decision 2: accepted as proposed; mapping admin-deal-notes is left for later and is not part of this feature.
