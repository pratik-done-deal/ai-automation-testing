# Hot Lead Refinement & Engagement Visibility — test cases
Status: APPROVED
Slug: hot-lead-engagement-visibility | Analysis: automation/specs/prd/hot-lead-engagement-visibility.analysis.md | Impact: automation/specs/features/hot-lead-engagement-visibility/impact.md
Requirements covered: 30 of 30  (9 manual-only: HLE-02, 03, 07, 12, 13, 18, 28, 29, 30)

Admin preconditions were NOT confirmed live: `automation/auth/admin.json` does not exist, so no admin
screen could be walked with `scripts/explore.py`. Every admin case below carries that blocker until
`python scripts/save_auth_state.py admin` is run. Copy and structure come from Figma (which wins, per
Answers 3 and 5) and from the `qa` branch code.

## 1. Scenario overview
| ID | Scenario | Role | Test cases | Priorities |
|---|---|---|---|---|
| S1 | Admin opens Unverified Deals and reads the engagement columns | admin | 4 | P0 ×2, P1, P2 |
| S2 | Admin sees an Unverified Deals row with no engagement yet | admin | 5 | P0, P1 ×3, P2 |
| S3 | Admin opens the engagement drill-down for a row with engagement | admin | 7 | P0 ×3, P1 ×3, P2 |
| S4 | Admin opens the drill-down and its data fails to load | admin | 2 | P2 ×2 |
| S5 | Admin filters Investor Leads with the Hot Leads toggles (behaviour unchanged) | admin | 7 | P0, P1 ×4, P2 ×2 |
| S6 | A fresh buyer lead expresses interest and turns hot | buyer POC (dedicated), admin | 2 | P1, P2 |
| S7 | A fresh buyer lead's POC spends 1+ min on the cue card or teaser and turns hot | buyer POC (dedicated), admin | 5 | P1 ×3, P2 ×2 |
| S8 | A fresh buyer lead with only short views stays not hot | buyer POC (dedicated), admin | 3 | P1 ×2, P2 |
| S9 | Seller lead hot logic is unchanged | admin | 2 | P1, P2 |
| S10 | Backend-only and long-window rules | manual | 9 | P1 ×3, P2 ×6 |

## 2. The happy flow
S1-01 → S1-02 → S2-01 → S3-01 → S3-02 → S3-05 → S5-01

One admin session, no buyer action, no scheduler wait, no data consumed. It reads existing QA data on
Unverified Deals (needs at least one row with engagement and one without) and on Investor Leads (needs at
least one hot lead). Roughly 1–2 minutes. These seven are the `smoke` set. Hot-lead flows (S6–S8) are not
in smoke: they wait up to one scheduler cycle each.

## 3. Scenarios and their test cases

### S1 — Admin opens Unverified Deals and reads the engagement columns
**Role:** admin · **Precondition:** admin session (BLOCKED: `auth/admin.json` missing); at least one Unverified Deals row with cue-card views · **Path:** /admin/deals?tabIndex=3&key=Unverified%20Deals

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S1-01 | Engagement column headers are shown | 1. Open /admin/deals?tabIndex=3&key=Unverified%20Deals → 2. Wait for the table to load | Header row contains "CC Views / Time" and "Doc Views / Time" | P0 | happy | HLE-19, HLE-16, HLE-17 | auto |
| S1-02 | Row with cue-card views shows count and time | 1. Open Unverified Deals → 2. Find the first row whose "CC Views / Time" cell is not "not yet viewed" → 3. Read that cell | Cell reads `<whole number ≥ 1> / <time>`, time in minute/second format (e.g. "22 min", "3 min 10 sec", "45 sec"); value is not recalculated | P0 | happy | HLE-16 | auto |
| S1-03 | Row with teaser views shows doc count and time | Given a row where the teaser was unlocked and viewed: 1. Open Unverified Deals → 2. Find that row → 3. Read its "Doc Views / Time" cell | Cell reads `<whole number ≥ 1> / <time>` in the same format as S1-02 | P1 | happy | HLE-17 | auto |
| S1-04 | Full header set matches Figma | 1. Open Unverified Deals → 2. Read the header row left to right | Headers read, in order, "Deal ID", "Buyer / Investor", "Seller / Company", "Lead Owner", "Lead Type", "Deal Status", "CC Views / Time", "Doc Views / Time", "Created At", "Last Activity", "Actions" (code today shows "Status" and "Action") | P2 | copy | HLE-19 | auto |

### S2 — Admin sees an Unverified Deals row with no engagement yet
**Role:** admin · **Precondition:** admin session (BLOCKED: `auth/admin.json` missing); at least one Unverified Deals row with zero cue-card views (e.g. a deal older than the tracking release) · **Path:** /admin/deals?tabIndex=3&key=Unverified%20Deals

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S2-01 | Empty CC cell shows "not yet viewed" (replaces "-") | 1. Open Unverified Deals → 2. Find a row with no cue-card views → 3. Read its "CC Views / Time" cell | Cell text matches "not yet viewed" (case ignored) | P0 | state | HLE-20 | auto |
| S2-02 | Empty Doc cell shows its own "not yet viewed" | 1. Open Unverified Deals → 2. Find a row with cue-card views but no doc views → 3. Read its "Doc Views / Time" cell | Cell text matches "not yet viewed" (case ignored) while the CC cell on the same row shows a count | P1 | state | HLE-20 | auto |
| S2-03 | No engagement cell shows "-" any more (replaces today's "-") | 1. Open Unverified Deals → 2. Read every "CC Views / Time" and "Doc Views / Time" cell on the first page | No engagement cell is "-", blank or "0" on its own | P1 | state | HLE-20, HLE-14 | auto |
| S2-04 | Empty cell has no drill-down entry | 1. Open Unverified Deals → 2. Find a "not yet viewed" cell → 3. Click it | No drill-down modal opens; the cell has no link or "N members" pill | P1 | gating | HLE-22 | auto |
| S2-05 | View with no time data still renders | Given a dedicated POC opened a cue card and the browser context was killed before leaving (no time sent): 1. Open Unverified Deals → 2. Find that lead's row → 3. Read its "CC Views / Time" cell | Cell shows a count and a time value; no "NaN", "undefined" or empty text | P2 | edge | HLE-14 | auto |

### S3 — Admin opens the engagement drill-down for a row with engagement
**Role:** admin · **Precondition:** admin session (BLOCKED: `auth/admin.json` missing); at least one Unverified Deals row with a drill-down entry (the "N members" pill or the metric link) · **Path:** Unverified Deals → engagement cell → drill-down modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S3-01 | Drill-down entry opens the modal | 1. Open Unverified Deals → 2. Find the first row with a drill-down entry in "CC Views / Time" → 3. Click the entry | Engagement modal opens | P0 | happy | HLE-21 | auto |
| S3-02 | Modal lists at least one POC row | 1. Open the drill-down as in S3-01 → 2. Read the modal table | Modal table has at least one POC row with a value in each of the five columns | P0 | happy | HLE-23 | auto |
| S3-03 | Modal headers match Figma (replaces "POC Email") | 1. Open the drill-down → 2. Read the header row | Headers read, in order, "POC Name", "CC Views", "CC Avg Time Spent", "Doc Views", "Doc Avg Time Spent" | P1 | copy | HLE-23 | auto |
| S3-04 | Modal title names the buyer lead (replaces "Engagement for D<dealId>") | 1. Open the drill-down → 2. Read the modal title | Title matches "Engagement for B<digits>" | P1 | copy | HLE-25 | auto |
| S3-05 | Close button closes the modal | 1. Open the drill-down → 2. Click "Close" | Modal is gone and the Unverified Deals table is visible again | P0 | happy | HLE-26 | auto |
| S3-06 | Modal time values are present and formatted | 1. Open the drill-down → 2. Read "CC Avg Time Spent" for each POC row with CC Views > 0 | Each value is in minute/second format (e.g. "8 min"); not recalculated | P1 | state | HLE-23 | auto |
| S3-07 | Primary POC carries a "Primary" chip | Given a lead whose primary POC has viewed: 1. Open that row's drill-down → 2. Read the "POC Name" column | Exactly one POC row shows a "Primary" chip | P2 | copy | HLE-24 | auto |

### S4 — Admin opens the drill-down and its data fails to load
**Role:** admin · **Precondition:** admin session (BLOCKED: `auth/admin.json` missing); the drill-down fetches its own data (BLOCKED: today the data is inline in the listing row, Q10), and that request is forced to fail with network mocking · **Path:** Unverified Deals → engagement cell → drill-down modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S4-01 | Failed load shows an error message | Given the engagement detail request returns a server error: 1. Open Unverified Deals → 2. Click a row's drill-down entry | Modal shows "Unable to load engagement detail. Try again." instead of a blank table | P2 | negative | HLE-27 | auto |
| S4-02 | Error state can be closed | Given the error state from S4-01: 1. Click "Close" | Modal is gone and the Unverified Deals table is visible again | P2 | negative | HLE-27 | auto |

### S5 — Admin filters Investor Leads with the Hot Leads toggles (behaviour unchanged)
**Role:** admin · **Precondition:** admin session (BLOCKED: `auth/admin.json` missing); at least one hot and one expired-hot buyer lead in QA · **Path:** /admin/leads?tabIndex=1

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S5-01 | Hot Leads toggle shows only hot leads | 1. Open /admin/leads?tabIndex=1 → 2. Turn on "Hot Leads" → 3. Wait for the list to reload | Every row shows the flame icon; no row is without it | P0 | happy | HLE-15 | auto |
| S5-02 | Turning on Hot Leads reveals "Expired Hot Leads" | 1. Open Investor Leads → 2. Turn on "Hot Leads" | An "Expired Hot Leads" switch appears next to it | P1 | state | HLE-15 | auto |
| S5-03 | The two toggles are mutually exclusive | 1. Open Investor Leads → 2. Turn on "Hot Leads" → 3. Turn on "Expired Hot Leads" | "Hot Leads" switches off | P1 | gating | HLE-15 | auto |
| S5-04 | Expired Hot Leads shows only expired leads | 1. Open Investor Leads → 2. Turn on "Hot Leads" → 3. Turn on "Expired Hot Leads" → 4. Hover the icon on each row | Every row's icon tooltip reads "Expired Hot Lead" | P1 | state | HLE-15 | auto |
| S5-05 | Changing tab resets both toggles | 1. Open Investor Leads → 2. Turn on "Hot Leads" → 3. Open the Company Leads tab → 4. Return to Investor Leads | "Hot Leads" is off and "Expired Hot Leads" is hidden | P1 | state | HLE-15 | auto |
| S5-06 | Flame icon tooltip reads "Hot Lead" | 1. Open Investor Leads → 2. Turn on "Hot Leads" → 3. Hover the flame icon on the first row | Tooltip reads "Hot Lead" | P2 | copy | HLE-15 | auto |
| S5-07 | Expiring-this-week pill copy | Given at least one hot lead expires within 7 days: 1. Open Investor Leads | Pill next to "Hot Leads" reads "<n> Expiring this week" with n ≥ 1 | P2 | copy | HLE-15 | auto |

### S6 — A fresh buyer lead expresses interest and turns hot
**Role:** buyer POC on the dedicated HLE buyer lead (not `buyer.json`), then admin · **Precondition:** a buyer lead that has never been hot, logged in as one of its POCs; one company cue card this lead has not expressed interest in (consumed); admin session (BLOCKED) · **Path:** /buyer/cue-card/:uid → Express Interest; then /admin/leads?tabIndex=1

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S6-01 | Express interest with a short view makes the lead hot | 1. As the POC, open the cue card → 2. Express interest within 30 s → 3. Leave the page → 4. As admin, open Investor Leads → 5. Turn on "Hot Leads" and re-check every 30 s for up to 7 min | The lead appears in the Hot Leads list | P1 | happy | HLE-01, HLE-08, HLE-11 | auto |
| S6-02 | Lead row shows the "Hot Lead" icon | Given S6-01 passed: 1. Open Investor Leads with toggles off → 2. Find the lead → 3. Hover its icon | Tooltip reads "Hot Lead" | P2 | state | HLE-01 | auto |

### S7 — A fresh buyer lead's POC spends 1+ min on the cue card or teaser and turns hot
**Role:** buyer POC on a dedicated HLE buyer lead, then admin · **Precondition:** one never-hot buyer lead per case, with POC cue-card deep links carrying `pocUid` (BLOCKED: deep-link format and a POC list not yet confirmed on QA); no interest expressed; admin session (BLOCKED) · **Path:** POC deep link → cue card (tab kept visible) → navigate away; then /admin/leads?tabIndex=1

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S7-01 | 90 s on the cue card makes the lead hot | 1. Open POC A's cue-card deep link → 2. Keep the tab visible for 90 s, no clicks on Express Interest → 3. Navigate to another page → 4. As admin, open Investor Leads → 5. Turn on "Hot Leads" and re-check every 30 s for up to 7 min | The lead appears in the Hot Leads list | P1 | happy | HLE-05 | auto |
| S7-02 | 90 s on the unlocked teaser makes the lead hot | Given a never-hot lead whose teaser for this company is already unlocked (BLOCKED: no known way to unlock without seller action): 1. Open the unlocked teaser as POC A → 2. Keep it visible for 90 s → 3. Navigate away → 4. As admin, poll "Hot Leads" for up to 7 min | The lead appears in the Hot Leads list | P1 | happy | HLE-06 | auto |
| S7-03 | One POC over 1 min is enough when another stays short | See detail block S7-03 | The lead appears in the Hot Leads list | P1 | edge | HLE-10 | auto |
| S7-04 | The view shows on the Unverified Deals row | Given S7-01 passed: 1. Open Unverified Deals → 2. Find the row for that lead and company → 3. Read "CC Views / Time" | Cell reads `<whole number ≥ 1> / <time>` in minute/second format | P2 | state | HLE-16 | auto |
| S7-05 | The drill-down lists the POC who viewed | Given S7-04 passed: 1. Click that row's drill-down entry → 2. Read the POC rows | POC A appears with "CC Views" ≥ 1 | P2 | state | HLE-23 | auto |

### S8 — A fresh buyer lead with only short views stays not hot
**Role:** buyer POC on a dedicated HLE buyer lead, then admin · **Precondition:** one never-hot buyer lead per case, POC deep links with `pocUid` (BLOCKED as in S7); no interest expressed; admin session (BLOCKED) · **Path:** POC deep link → cue card → navigate away; wait a full cycle; /admin/leads?tabIndex=1

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S8-01 | 20 s on the cue card does not make the lead hot (replaces "hot on bare discovery") | 1. Open POC A's cue-card deep link → 2. Keep it visible for 20 s → 3. Navigate away → 4. Wait 7 min (one full cycle plus buffer) → 5. As admin, open Investor Leads → 6. Turn on "Hot Leads" | The lead is not in the Hot Leads list | P1 | negative | HLE-04 | auto |
| S8-02 | Shallow-view lead has no "Hot Lead" icon | Given S8-01 passed: 1. Open Investor Leads with toggles off → 2. Find the lead | The lead's row has no flame icon | P2 | negative | HLE-04 | auto |
| S8-03 | Two POCs at 40 s each do not add up to hot | See detail block S8-03 | The lead is not in the Hot Leads list | P1 | edge | HLE-10 | auto |

### S9 — Seller lead hot logic is unchanged
**Role:** admin · **Precondition:** admin session (BLOCKED: `auth/admin.json` missing); at least one hot seller lead in QA · **Path:** /admin/leads → Company Leads tab

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S9-01 | Company Leads Hot Leads toggle still lists hot seller leads | 1. Open /admin/leads → 2. Open the Company Leads tab → 3. Turn on "Hot Leads" | At least one row is listed and every row shows the flame icon | P2 | state | HLE-09 | auto |
| S9-02 | Seller lead with mandate_discovered today is hot with no time spent | Manual: pick a seller lead that got mandate_discovered or seller_express_interest today with no POC view over 1 min → wait one scheduler run → check Company Leads with "Hot Leads" on | The seller lead is listed as hot | P1 | happy | HLE-09 | manual |

### S10 — Backend-only and long-window rules
**Role:** manual (QA with backend access) · **Precondition:** access to lead records or backend logs; release-day access for S10-04 · **Path:** n/a

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S10-01 | seller_express_interest makes a buyer lead hot | Manual: have a seller express interest in a never-hot buyer lead → wait one scheduler run → check Investor Leads "Hot Leads" | The buyer lead is listed as hot | P1 | happy | HLE-02 | manual |
| S10-02 | mandate_discovered makes a buyer lead hot | Manual: get a never-hot buyer lead into mandate_discovered → wait one scheduler run → check Investor Leads "Hot Leads" | The buyer lead is listed as hot | P1 | happy | HLE-03 | manual |
| S10-03 | Time-spent hot lead expires after 14 days | Manual: note a lead that turned hot through time spent (S7-01) → check again on day 15 with "Expired Hot Leads" on | The lead is listed under Expired Hot Leads, not Hot Leads | P2 | state | HLE-07, HLE-08 | manual |
| S10-04 | Bare-discovery hot leads lose hot status after release | Manual: before release, list leads hot only via discovery → after the first scheduler run post-release, check "Hot Leads" | None of those leads is still listed as hot | P1 | edge | HLE-12 | manual |
| S10-05 | Several sub-minute views and the exact-60 s boundary | Manual, backend: one POC views three times at 30 s each; another POC views exactly 60 s → check the hot flag after one run | Hot status matches the dev decision on per-session vs cumulative and on 60 s inclusive | P2 | edge | HLE-13 | manual |
| S10-06 | Displayed time equals the backend's avg value | Manual, backend: for one row, compare "CC Views / Time" and the drill-down times to the stored avg time per view | UI values equal the backend values | P2 | edge | HLE-18 | manual |
| S10-07 | Only discovery and teaser-unlock activity is counted | Manual, backend: record other activity types (e.g. document request) for a POC → compare counts before and after | View counts and times do not change | P2 | edge | HLE-28 | manual |
| S10-08 | Scheduler cadence and 14-day window unchanged | Manual, backend: check scheduler logs over 30 min and the hot-lead expiry field of a new hot lead | Runs every 5 min; expiry is 14 days after qualifying | P2 | state | HLE-29 | manual |
| S10-09 | Conversion metric is recorded | Manual, analytics: find the time-spent-trigger conversion metric after a lead qualifies via time spent | The metric exists and counts that lead | P2 | state | HLE-30 | manual |

## 4. Detail blocks

**S7-03 — One POC over 1 min is enough when another stays short**
Precondition: a never-hot buyer lead with at least two POCs (A and B) and a deep link for each.
1. Open POC B's cue-card deep link, keep it visible 20 s, navigate away. Expected: page leaves cleanly.
2. Open POC A's cue-card deep link for the same company, keep it visible 90 s, navigate away. Expected: page leaves cleanly.
3. As admin, open /admin/leads?tabIndex=1. Expected: Investor Leads list loads.
4. Turn on "Hot Leads" and re-check every 30 s for up to 7 min. Expected: the lead appears in the Hot Leads list.

**S8-03 — Two POCs at 40 s each do not add up to hot**
Precondition: a never-hot buyer lead with at least two POCs (A and B) and a deep link for each.
1. Open POC A's cue-card deep link, keep it visible 40 s, navigate away. Expected: page leaves cleanly.
2. Open POC B's cue-card deep link for the same company, keep it visible 40 s, navigate away. Expected: page leaves cleanly.
3. Wait 7 min (one full scheduler cycle plus buffer).
4. As admin, open /admin/leads?tabIndex=1 and turn on "Hot Leads". Expected: the lead is not in the Hot Leads list (80 s combined across POCs must not qualify).

## 5. Requirement coverage
| Req ID | Requirement | Test cases | Covered |
|---|---|---|---|
| HLE-01 | express_interest buyer lead hot after next run | S6-01, S6-02 | yes |
| HLE-02 | seller_express_interest buyer lead hot after next run | S10-01 | manual (no confirmed seller UI path to create it on a dedicated lead) |
| HLE-03 | mandate_discovered buyer lead hot after next run | S10-02 | manual (no known UI way to put a fresh lead into mandate_discovered) |
| HLE-04 | discovery only, no POC at 1+ min, not hot | S8-01, S8-02 | yes |
| HLE-05 | one POC 1+ min on cue card makes lead hot | S7-01 | yes |
| HLE-06 | one POC 1+ min on unlocked teaser makes lead hot | S7-02 | yes (precondition blocked: teaser unlock) |
| HLE-07 | time-spent hot lasts 14 days then Expired | S10-03 | manual (14-day window) |
| HLE-08 | POC expressed interest today, hot for 14 days | S6-01, S10-03 | yes (14-day part manual) |
| HLE-09 | seller lead hot with no time-spent condition | S9-01, S9-02 | yes |
| HLE-10 | any single POC over 1 min qualifies, not an aggregate | S7-03, S8-03 | yes |
| HLE-11 | express_interest lead hot without any 1-min view | S6-01 | yes |
| HLE-12 | bare-discovery hot leads lose hot after release | S10-04 | manual (release-time transition) |
| HLE-13 | several sub-minute views per session vs cumulative | S10-05 | manual (backend decision, per Answer 4) |
| HLE-14 | view without time data counts as 0 and row renders | S2-03, S2-05 | yes |
| HLE-15 | Hot Leads / Expired Hot Leads toggles unchanged | S5-01 – S5-07 | yes |
| HLE-16 | row shows cue-card view count and time | S1-01, S1-02, S7-04 | yes |
| HLE-17 | row shows doc view count and time | S1-01, S1-03 | yes |
| HLE-18 | time shown is avg per view | S10-06 | manual (UI shows the backend value as-is, per Answer 1) |
| HLE-19 | engagement headers per Figma | S1-01, S1-04 | yes |
| HLE-20 | zero engagement shows "not yet viewed" | S2-01, S2-02, S2-03 | yes |
| HLE-21 | each row with engagement has a drill-down entry | S3-01 | yes |
| HLE-22 | row with no engagement has no drill-down | S2-04 | yes |
| HLE-23 | drill-down shows one row per POC with the five columns | S3-02, S3-03, S3-06, S7-05 | yes |
| HLE-24 | primary POC has a "Primary" chip | S3-07 | yes |
| HLE-25 | drill-down title "Engagement for B<buyerId>" | S3-04 | yes |
| HLE-26 | drill-down closes with "Close" | S3-05 | yes |
| HLE-27 | drill-down load failure shows error with Close | S4-01, S4-02 | yes (precondition blocked until the drill-down fetches its own data) |
| HLE-28 | views scoped to discovery and teaser unlock only | S10-07 | manual (backend scope) |
| HLE-29 | scheduler every 5 min, hot 14 days, unchanged | S10-08 | manual (non-functional) |
| HLE-30 | time-spent conversion metric tracked | S10-09 | manual (analytics, no UI) |

## 6. Test data and run order
- **S1–S5, S9-01 (read-only admin):** an admin session in `auth/admin.json` (`python scripts/save_auth_state.py admin`, biz user). They read existing QA data and consume nothing. Unverified Deals must hold at least one row with cue-card views, one with a teaser/doc view, one with zero engagement, and one where the primary POC viewed; Investor Leads must hold at least one hot and one expired-hot lead. Rows are found at run time by cell content, never by fixed deal id.
- **S4:** network mocking of the drill-down detail request. Runs only once the drill-down fetches its own data (Q10); until then the script should skip with that reason.
- **S6–S8 (hot-lead flows, destructive):** a dedicated HLE buyer lead per case, never used by `buyer.json`, the buyer journey or phase 1. Each case consumes one lead for 14 days (a lead that turns hot cannot be reused; a lead used by a negative case must not be reused either, because later views would change its outcome). Per full run: S6-01, S7-01, S7-02, S7-03, S8-01, S8-03 = 6 fresh buyer leads, S7-03 and S8-03 each with at least two POCs. S6-01 also consumes one company cue card (express interest).
- **Order inside a flow:** buyer POC acts first, then admin polls. Positive cases poll "Hot Leads" every 30 s for up to 7 min and pass as soon as the lead appears; negative cases must wait the full 7 min before checking. Run all six flows' buyer steps first, then one shared admin wait, so the whole block costs about one cycle, not six.
- **Time tracking:** the cue-card tab must stay visible (headless runs keep it in the foreground) and the test must navigate away cleanly so the time is sent. S2-05 is the one case that deliberately kills the context instead.
- **Two-phase:** none. No seller login is needed for any automated case.
- **Avoid running near midnight IST** (the backend's "today"), per Answer 8.
- **`.env` additions (proposed names):** `DD_ADMIN_STATE` (exists), `DD_HLE_BUYER_STATE` (dedicated buyer session, if the deep link needs a logged-in POC), `DD_HLE_POC_LINKS` (comma-separated fresh POC deep links, grouped per lead, e.g. `leadA:link1|link2,leadB:link1`), `DD_HLE_LEAD_NAMES` (how each lead appears on Investor Leads, to find it), `DD_HLE_FRESH_COMPANY_UIDS` (for S6-01), `DD_HLE_TEASER_UNLOCKED_LINK` (for S7-02), `DD_HLE_HOT_POLL_SECONDS=420`.

## 7. Assumptions
1. (Answer 1) Time values are checked for presence and minute/second format only. Accepted formats: "N min", "N min N sec", "N sec", and Figma's "Nmin". Avg vs max is never recalculated in UI tests; HLE-18 is manual.
2. (Answer 2, assumption) Each empty metric cell (CC or Doc) shows its own "not yet viewed", matched ignoring case; styling not checked. This replaces today's "-".
3. (Answer 3) Figma headers win: "CC Views / Time", "Doc Views / Time", and the full Figma set in S1-04 ("Deal Status", "Actions"). The current QA code shows "Status" and "Action", so S1-04 fails until that changes.
4. (Answer 4) Per-session vs cumulative and the exact-60 s boundary are backend/manual. UI flows use 20 s and 40 s (under) and 90 s (over).
5. (Answer 5, assumption) Drill-down title is "Engagement for B<buyerId>" and the first column is "POC Name" with a "Primary" chip. Current QA code shows "Engagement for D<dealId>" and "POC Email", so S3-03, S3-04 and S3-07 fail on today's code.
6. (Answer 6, assumption) A row with engagement has a working drill-down entry, either the "N members" pill or the metric link; the tests accept either and do not check which rows show the pill.
7. (Answer 7, assumption) No scheduler trigger or data seeding on QA. Hot-lead flows use fresh dedicated leads, poll up to one cycle (5 min + 2 min buffer), and are not in smoke. The 14-day expiry and resets are manual.
8. (Answer 8, assumption) "Today" is the IST calendar day; tests avoid running near midnight and do not test the boundary.
9. (Q9) The engagement UI already on `qa` (commit d8166b264) is the baseline; the cases target the Figma/PRD end state.
10. (Q10) The drill-down error copy reuses "Unable to load engagement detail. Try again." with a "Close" button, and S4 applies only once the drill-down fetches its own data.
11. (Q11) Backfill is checked by hand at release (S10-04).
12. (Q12) The Company Leads toggle needs no regression beyond S9.
13. (Judgement) The drill-down entry is tested on the "CC Views / Time" cell; the Doc cell entry is not tested separately.
14. (Judgement) S2-05 assumes killing the browser context before leaving the cue card produces a view with no time data. If the backend drops such a view entirely, S2-05 has no precondition and becomes manual.
15. (Judgement) A POC cue-card deep link carrying `pocUid` can be produced for a dedicated lead on QA; its format was not confirmed because no admin/POC walk was possible.

## 8. Review
(filled by the caller: approved, changed and rejected rows, plus the date)

## Review
2026-09-27: approved by the user with no changes. All 46 cases (10 scenarios) stand as written.
