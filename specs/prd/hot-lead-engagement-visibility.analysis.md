# Hot Lead Refinement & Engagement Visibility — requirements analysis
Status: READY
Slug: hot-lead-engagement-visibility | Roles: admin (biz user), buyer lead POC (data setup only) | PRD: automation/specs/prd/hot-lead-engagement-visibility.md | Figma: https://www.figma.com/design/RWMCvpU1gf3ydyJxTyQwsA/Sprint-Work?node-id=43508-121328 (section "Engagement visibility": table frame 43508:119587, drill-down modal 43651:131869)
Explored: buyer:/buyer/browse (captured). admin:/admin/leads?tabIndex=1 and admin:/admin/deals?tabIndex=3 were NOT walked: no admin session (`automation/auth/admin.json` missing). Admin screens below are described from code on the `qa` branch and from Figma, and must be confirmed by a walk once the session exists.

## 1. Summary
Two changes for the biz user (admin) managing buyer leads:
1. **Hot-lead logic (backend only).** A buyer lead is no longer hot on a bare cue-card open (`discovery`). It is hot when status is express_interest / seller_express_interest / mandate_discovered, OR any POC spent 1+ min on the cue card or the unlocked investment teaser. Seller leads are unchanged. A scheduler evaluates this every 5 min; hot lasts 14 days. The Investor Leads "Hot Leads" toggle is not changed, only what it returns.
2. **Engagement visibility (UI).** Unverified Deals shows views and time spent (cue card and doc/teaser) per deal row, with a per-POC drill-down.

Important: part 2 **already exists on QA code** (commit d8166b264, 2026-08-26, on `qa`, not on `main`): "CC Views / Time" and "Doc Views / Time" columns plus an "Engagement for D<id>" POC modal. The PRD reads as if it is all new. See section 8.

## 2. How it works today
| Screen | Route | Role | Current behaviour | Capture |
|---|---|---|---|---|
| Leads > Investor Leads | /admin/leads?tabIndex=1 | admin | "Hot Leads" switch (flame icon, optional "N Expiring this week" pill). On: adds `{filterKey:"hotLead", operation:"notExpired"}` to POST `lead/query`. When on, a second switch "Expired Hot Leads" appears (`operation:"expired"`); the two are mutually exclusive. Rows show a flame icon with tooltip "Hot Lead" when `hotLead` is true, or "Expired Hot Lead" icon when not hot but `leadMetaData` present. Also shown on Company Leads (seller) tab. Switching tab resets both toggles. | not walked (code: src/Container/LeadContainer/index.js, leadTableModel.js:862) |
| Deals > Unverified Deals | /admin/deals?tabIndex=3&key=Unverified%20Deals | admin | Tabs today: All Deals, Active Deals, Scheduled Calls, Unverified Deals. Table columns: Deal ID, Buyer/Investor, Seller/Company, Lead Owner, Lead Type, Status, "CC Views / Time", "Doc Views / Time", Created At, Last Activity, Action. Default status filter: mandate_discovered, discovery, express_interest, unlocked investment teaser, seller_express_interest. API: `deal/unverified-deals`. | not walked (code: AdminDealsTabModel.js:150, AdminDealsTableModel.js:1584) |
| CC / Doc views cell | same | admin | Shows `<count> / <time>` where time is `ccMaxTime` / `docMaxTime` formatted as "X min Y sec". No data shows "-". If count > 0 and the row has `pocEngagementDetails`, the cell is a blue underlined link. | not walked |
| Engagement drill-down modal | same (modal) | admin | Title "Engagement for D<dealId>". Columns: POC Email, CC Views, CC Avg Time Spent, Doc Views, Doc Avg Time Spent. The time columns are fed from `ccMaxTime`/`docMaxTime` (max, not avg). Empty values show "-". "Close" button. Data comes from the listing row, so no fetch and no error state on this path. | not walked |
| Buyer cue card (deep link) | /buyer/... cue card with `pocUid` in URL | buyer POC | Active (tab-visible) time is tracked per POC via `useBatchTimeTracker` and sent on exit (beacon). This is the data source for the 1-min rule. | hl-buyer-browse (browse only; opening a cue card was not done) |

## 3. What changes
| # | Before (today) | After (PRD) | Delta |
|---|---|---|---|
| C1 | Buyer lead hot on bare `discovery` | Not hot on discovery alone | Backend logic; visible only through the Hot Leads toggle and flame icon |
| C2 | Time spent not a hot trigger | Any POC with 1+ min on cue card or unlocked teaser makes the lead hot for 14 days | Backend logic |
| C3 | Leads hot only via bare discovery | Lose hot at next run (become "Expired Hot Lead"?) | Behaviour change on existing data; backfill undecided (PRD s.10) |
| C4 | Seller lead hot logic | Unchanged | Regression check only |
| C5 | Unverified Deals: "CC Views / Time", "Doc Views / Time" showing count / max time | "Total Views" and "Avg Time Spent" (PRD); Figma keeps "CC Views / Time" and "Doc Views / Time" with an "N members" pill | Mostly exists; label and metric (max vs avg) unclear |
| C6 | Empty engagement shows "-" | Clear "not yet viewed" state | New copy, not in Figma |
| C7 | Drill-down opened by clicking the metric link; title "Engagement for D<id>"; first column "POC Email" | Figma: "N members" pill under the metric; title "Engagement for B<buyerId>"; first column "POC Name" with "Primary" chip | Several copy/UX deltas |
| C8 | No error state on the Unverified drill-down (data is inline) | Error state if drill-down data fails to load | New, only if the drill-down starts fetching its data |

## 4. Requirements
| ID | Requirement (one sentence) | Source | Role | Type | Verify via | Exists today |
|---|---|---|---|---|---|---|
| HLE-01 | A buyer lead whose status is express_interest is shown as hot after the next scheduler run. | PRD S1 AC1, FR1 | admin | rule | flow (data setup) | yes |
| HLE-02 | A buyer lead whose status is seller_express_interest is shown as hot after the next scheduler run. | PRD S1 AC1 | admin | rule | manual | yes |
| HLE-03 | A buyer lead whose status is mandate_discovered is shown as hot after the next scheduler run. | PRD S1 AC1 | admin | rule | manual | yes |
| HLE-04 | A buyer lead with only discovery activity and no POC at 1+ min is NOT shown under the Hot Leads toggle after the next run. | PRD S1 AC2, FR2 | admin | rule | flow (data setup) | no |
| HLE-05 | A buyer lead where one POC spent 1+ min on the cue card is shown as hot after the next run. | PRD S1 AC3 | admin, buyer | rule | flow (data setup) | no |
| HLE-06 | A buyer lead where one POC spent 1+ min on the unlocked investment teaser is shown as hot after the next run. | PRD S1 AC3 | admin, buyer | rule | flow (data setup) | no |
| HLE-07 | A lead that qualifies via time spent stays hot for 14 days, then appears under Expired Hot Leads. | PRD S1 AC3, non-goals | admin | rule | manual | partial (14-day window exists) |
| HLE-08 | A buyer lead where a POC expressed interest today is hot for 14 days. | PRD S1 AC4 | admin | rule | flow (data setup) | yes |
| HLE-09 | A seller lead with mandate_discovered or seller_express_interest is hot with no time-spent condition. | PRD S1 AC5, FR3 | admin | rule | flow (data setup) | yes |
| HLE-10 | A lead with several POCs qualifies when only one POC crosses 1 min (not an aggregate). | PRD s.6 | admin | edge-case | flow (data setup) | no |
| HLE-11 | A lead hot via express_interest stays hot even if no POC crosses 1 min. | PRD s.6 | admin | edge-case | flow (data setup) | yes |
| HLE-12 | A lead that was hot only via bare discovery loses hot status at the next run after release. | PRD s.6 | admin | edge-case | manual | no |
| HLE-13 | A POC with several views none of which reaches 1 min does (or does not) qualify, per the per-session vs cumulative decision. | PRD s.6 | admin | edge-case | manual | no |
| HLE-14 | A view event without time-spent data counts as 0 and the row still renders. | PRD s.6 | admin | edge-case | UI | partial ("-" shown) |
| HLE-15 | The Hot Leads and Expired Hot Leads toggles on Investor Leads behave as today (filter, mutual exclusion, reset on tab change). | PRD non-goals | admin | rule | UI | yes |
| HLE-16 | An Unverified Deals row with discovery activity shows the cue-card view count and time spent. | PRD S2 AC1, FR4 | admin | flow | UI | yes (as "CC Views / Time") |
| HLE-17 | An Unverified Deals row with teaser-unlock activity shows the doc view count and time spent. | PRD S2 AC1, FR4 | admin | flow | UI | yes (as "Doc Views / Time") |
| HLE-18 | The time shown is the average time spent per view. | PRD S2 AC1, s.7 | admin | rule | manual | no (code shows max) |
| HLE-19 | The engagement column headers read as agreed in Q3 ("Total Views"/"Avg Time Spent" or "CC/Doc Views / Time"). | PRD s.7, Figma | admin | copy | UI | partial |
| HLE-20 | A row with zero engagement shows a "not yet viewed" state instead of blank or zero. | PRD S2 AC2, s.6 | admin | copy | UI | no ("-" today) |
| HLE-21 | Each row with engagement has a drill-down entry point. | PRD FR5, s.7 | admin | flow | UI | yes (metric link) |
| HLE-22 | A row with no engagement has no clickable drill-down. | code, implied | admin | gating | UI | yes |
| HLE-23 | The drill-down shows one row per POC with POC identifier, CC views, CC avg time, Doc views, Doc avg time. | PRD S2 AC3, Q1, Figma | admin | flow | UI | yes |
| HLE-24 | The primary POC is marked with a "Primary" chip in the drill-down. | Figma | admin | copy | UI | no |
| HLE-25 | The drill-down title reads as agreed in Q5 ("Engagement for B<buyerId>" or "D<dealId>"). | Figma vs code | admin | copy | UI | partial |
| HLE-26 | The drill-down closes with the "Close" button. | Figma | admin | flow | UI | yes |
| HLE-27 | When drill-down data fails to load, an error message is shown with a Close button instead of a blank view. | PRD S2 AC4 | admin | edge-case | UI (needs network mocking) | partial (only on fetch-based DealsLink uses) |
| HLE-28 | Views and time are scoped to discovery and investment-teaser-unlock activity only. | PRD FR4 | admin | rule | manual | unknown |
| HLE-29 | The scheduler runs every 5 min and hot lasts 14 days, unchanged. | PRD non-goals | - | non-functional | manual | yes |
| HLE-30 | Conversion metric (onboarded via time-spent trigger / qualified via time-spent trigger) is tracked. | PRD s.8 | - | non-functional | manual | no |

## 5. Screens
| Screen | Figma node / route | State | Exact visible copy |
|---|---|---|---|
| Investor Leads list | /admin/leads?tabIndex=1 (no Figma) | toggle off / Hot on / Expired on | "Hot Leads", "Expired Hot Leads", "<n> Expiring this week"; row icon tooltips "Hot Lead", "Expired Hot Lead" |
| Unverified Deals table | 43508:119587 / /admin/deals?tabIndex=3 | with engagement | Tabs in Figma "All Deals", "Pending Actions", "Unverified Deals"; filters "Deal ID", "Buyer / Investor Lead", "Seller / Company Lead", "Deal Status", "Reset"; headers "Deal ID", "Buyer / Investor", "Seller / Company", "Lead Owner", "Lead Type", "Deal Status", "CC Views / Time", "Doc Views / Time", "Created At", "Last Activity", "Actions"; cell e.g. "5 / 22min" link with pill "3 members" |
| Unverified Deals table | 43508:119587 | engagement, no drill-down | plain "5 / 22min", no pill (rows 2, 4, 6, 7 in Figma; rule unclear, Q6) |
| Unverified Deals table | none | zero engagement | not designed; code shows "-"; PRD wants "not yet viewed" (Q2) |
| Engagement modal | 43651:131869 | success | Title "Engagement for B1255"; headers "POC Name", "CC Views", "CC Avg Time Spent", "Doc Views", "Doc Avg Time Spent"; values e.g. "BM1125" + "Primary", "5", "8 min"; button "Close" |
| Engagement modal | none | error | not designed; existing DealsLink copy "Unable to load engagement detail. Try again." + "Close"; loading "Loading engagement detail..." |

## 6. Flow and sequencing
- **Order:** buyer POC acts first (opens cue card or teaser and stays 1+ min, or expresses interest) -> scheduler runs (up to 5 min) -> admin checks Investor Leads Hot Leads toggle and Unverified Deals.
- **Time tracking** is per POC, identified by `pocUid` in the cue-card URL (deep link / campaign link). Only tab-visible time counts, and it is sent when the page is left or closed. A test must keep the tab foregrounded 60+ s, then navigate away.
- **Preconditions:** a buyer lead with at least two POCs and cue-card deep links for each; a lead in plain `discovery` with a sub-60 s view; a seller lead in mandate_discovered; a deal in the Unverified Deals default status set.
- **Consumes data:** express interest, teaser unlock, and each qualifying view are one-way. A lead that turns hot stays hot 14 days, so each negative case needs a fresh lead. Budget new leads per run or get a backend reset hook (Q7).
- **Routes:** admin `/admin/leads?tabIndex=1` (Hot Leads switch), `/admin/deals?tabIndex=3&key=Unverified%20Deals`. Buyer POC: cue-card deep link carrying `pocUid`/`listingUid`.
- **What UI tests can see:**
  - UI-testable now, no setup: HLE-15, 16, 17, 19, 21, 22, 23, 24, 25, 26 against existing QA data.
  - UI-testable with seeded data only: HLE-14, 18, 20 (need rows with known counts/times, and zero engagement).
  - Flow with data setup plus a wait of up to 5 min (or a scheduler trigger): HLE-01 to 06, 08 to 11.
  - Needs network mocking: HLE-27.
  - Manual / backend: HLE-07 (14 days), 12 (release-time transition), 13 (pending decision), 28, 29, 30.

## 7. Open questions
1. **blocking** — Time spent shown on the row and in the drill-down: average per view (PRD, Figma "Avg Time Spent") or maximum single view (current code uses `ccMaxTime`/`docMaxTime`)? The oracle for every time value depends on it.
2. **blocking** — What exact copy and style is the "not yet viewed" state (PRD S2 AC2)? Figma has no zero state; today the cell shows "-". Is it one label per cell or per row?
3. **blocking** — Column headers: PRD says "Total Views" and "Avg Time Spent" columns; Figma and the live code say "CC Views / Time" and "Doc Views / Time". Which is final?
4. **blocking** — The 1-min rule: per session or cumulative across a POC's views (PRD s.6 says dev must confirm)? And is "1+ min" inclusive of exactly 60 s?
5. **blocking** — Drill-down title and first column: Figma "Engagement for B<buyerId>" with "POC Name" (BM id + "Primary" chip); code "Engagement for D<dealId>" with "POC Email" (renamed from POC Name in commit a5ab175c8). Which is right?
6. **blocking** — Drill-down entry point: Figma shows an "N members" pill under the metric; code makes the metric itself the link. When is the pill/link shown (Figma rows 2, 4, 6, 7 have counts but no pill)?
7. **blocking** — How can QA create the backend preconditions: is there a way to trigger the hot-lead scheduler or seed time-spent rows on QA, or must tests wait up to 5 min per case? Who owns the reset of a lead that has turned hot?
8. **blocking** — Does "today" in the ACs mean the calendar day (which timezone) or since the last scheduler run? It decides whether a view at 23:59 counts.
9. **deferrable** — Is the engagement work already shipped on QA (commit d8166b264) considered the baseline, with this PRD only changing labels/metric/empty state? Assumed yes.
10. **deferrable** — Error state for the drill-down: the data is inline in the listing today, so it cannot fail separately. Will the drill-down fetch its own data? Assumed the existing DealsLink error copy is reused if so.
11. **deferrable** — Backfill (PRD s.10): will currently hot bare-discovery leads be recomputed at release or expire naturally? Affects HLE-12 only; assumed manual check at release.
12. **deferrable** — Does the Company Leads (seller) Hot Leads toggle need any regression beyond HLE-09? Assumed no.

## Answers
Answered by the user on 2026-09-27. Questions marked *assumption* were not answered: the user said "assume the rest".

1. **Answered:** the backend calculates the time metric, and the frontend displays whatever value it receives. Tests check that the time value is present and correctly formatted. They do not recalculate an average or maximum, so the avg vs max question is out of scope for UI tests.
2. *Assumption:* each empty metric cell (CC or Doc) gets its own "not yet viewed" label instead of "-". Tests match the text "not yet viewed" ignoring case, and don't check styling.
3. **Answered:** use Figma. The headers are "CC Views / Time" and "Doc Views / Time", plus the other Figma headers in section 5.
4. **Answered:** for the frontend, per-session vs cumulative doesn't matter. HLE-13 and the exact-60 s boundary stay backend/manual. UI flow tests use only views well under or well over 1 min.
5. *Assumption (follows the answer to 3, Figma wins):* the drill-down title is "Engagement for B<buyerId>" and the first column is POC Name with a "Primary" chip on the primary POC. The code currently shows D<dealId> and POC Email, so this is a difference to check.
6. *Assumption (Figma):* the "N members" pill on a metric cell opens the drill-down. Tests only check that a row with engagement has a working drill-down entry. They don't check which rows show the pill.
7. *Assumption:* QA has no way to trigger the scheduler or seed data. Hot-lead flow tests use a fresh buyer lead per run, wait up to one scheduler cycle (5 min plus a buffer) by polling the Hot Leads toggle, and are not in smoke. The 14-day expiry and resets stay manual.
8. *Assumption:* "today" is the calendar day in IST and is enforced by the backend. UI tests avoid running near midnight and don't test the day boundary.
9–12. The assumptions stated above stand.

## 8. Gaps and risks
- **Feature partly built already.** Engagement columns and the POC modal exist on the `qa` branch (not `main`). The PRD calls them new; test cases must target the delta, and the impact-analyzer should treat them as existing UI.
- **Metric mismatch.** Code labels the modal columns "Avg Time Spent" but renders max time. Either a bug or the PRD is wrong (Q1).
- **PRD vs Figma vs code copy conflicts:** column headers (Q3), modal title B vs D and POC Name vs Email (Q5), tab names (Figma "Pending Actions" vs code "Active Deals"/"Scheduled Calls"), "Deal Status" vs "Status", "Actions" vs "Action". Figma shows "22min"; code formats "22 min" / "X min Y sec".
- **Hot-lead logic is invisible from the UI** except as a flame icon and a toggle result, delayed up to 5 min, and irreversible for 14 days per lead. Without a scheduler trigger or seeding (Q7), these flows are slow, flaky and eat test data.
- **Time tracking depends on browser behaviour:** only visible-tab time counts and it is sent on unload via beacon. Headless runs must keep the page visible and navigate away cleanly, or the minute will not register.
- **Blocked walk:** no admin session, so no admin screen was seen live. Run `python scripts/save_auth_state.py admin` (biz user) and re-walk both admin routes before test cases are finalised.
