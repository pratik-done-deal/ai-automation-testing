# Hot Lead Refinement & Engagement Visibility on Unverified Deals

Design: https://www.figma.com/design/RWMCvpU1gf3ydyJxTyQwsA/Sprint-Work?node-id=43508-121328&t=neNkqm6DJUVLT9Cr-1

## 1. Problem statement
Biz users rely on the "hot lead" flag to prioritize their buyer lead pipeline, but today a buyer lead qualifies as hot from a single cue-card open (discovery) with no minimum engagement. Production data confirms the gap: only 1.89% (1 of 53) of ever-hot buyer leads have converted to onboarding. Biz users also have no visibility into engagement depth (views, time spent) on the Unverified Deals page, so they can't distinguish genuinely engaged leads from shallow opens when deciding who to call.

## 2. Goals
- Goal 1: Improve buyer-lead onboarding conversion among hot-flagged leads, by requiring genuine engagement (1+ min time spent) rather than a bare discovery event.
- Goal 2: Give biz users visibility into engagement depth (total views, avg time spent) on Unverified Deals to inform reachout prioritization.

### Non-goals
- Not changing seller lead hot-lead criteria (mandate_discovered, seller_express_interest remain engagement-gate-free).
- Not building conversion/reachout funnel tracking (hot lead → onboarding rate, reachout counts) — separate future scope.
- Not changing the 14-day hot window, re-qualification behavior, or the 5-min scheduler cadence.
- Not adding a new page — Investor Lead Listing keeps its existing hotLead filter; only the underlying logic changes.

## 3. Users and context
- Primary user: Biz user (M&A Associate) and Admin managing the buyer lead pipeline.
- Entry point: Investor Lead Listing (hotLead filter, logic changes under the hood) and Unverified Deals page (new engagement columns + drill-down).

## 4. User stories + acceptance criteria

### Story 1
As a biz user, I want buyer leads to only be marked hot when there's genuine engagement, so the hot-lead filter surfaces leads worth calling instead of shallow opens.
- [ ] Given a buyer lead's status today is express_interest, seller_express_interest, or mandate_discovered, when the hot-lead scheduler runs, then the lead is marked hot (unchanged).
- [ ] Given a buyer lead's only activity today is discovery (cue card opened) with no POC crossing 1 min time spent, when the scheduler runs, then the lead is NOT marked hot.
- [ ] Given at least one POC has spent 1+ min on the cue card (discovery) or on the unlocked investment teaser today, when the scheduler runs, then the lead is marked hot for 14 days.
- [ ] Given at least one POC has done express interest today, when the scheduler runs, then the lead is marked hot for 14 days.
- [ ] Given a seller lead has mandate_discovered or seller_express_interest activity today, when the scheduler runs, then it is marked hot exactly as today — no time-spent condition applied.

### Story 2
As a biz user, I want to see engagement data on the Unverified Deals page, so I can tell which leads are worth a reachout call.
- [ ] Given a lead-seller pairing has recorded discovery or investment-teaser-unlock activity, when the page loads, then total views and avg time spent for that activity are shown on the row.
- [ ] Given a row has zero recorded engagement, when the page loads, then it shows a clear "not yet viewed" state instead of a blank/zero without context.
- [ ] Given a biz user clicks the drill-down CTA on a row, when the detail view opens, then it shows a per-POC breakdown (POC name, views, avg time spent) — pending confirmation on exact fields.
- [ ] Given the drill-down data fails to load, when the CTA is clicked, then an error state is shown rather than a blank/broken view.

## 5. Functional requirements
- The system SHALL evaluate buyer lead hot-status using: (express_interest OR seller_express_interest OR mandate_discovered) OR (any POC time-spent ≥ 1 min on discovery or investment teaser unlock).
- The system SHALL NOT mark a buyer lead hot on bare discovery status alone.
- The system SHALL leave seller lead hot-status logic unchanged.
- The system SHALL display aggregate views and avg time spent — scoped to discovery and investment teaser unlock activity — per lead-seller pairing row on Unverified Deals.
- The system SHALL provide a drill-down entry point per row for deeper engagement detail.

## 6. Edge cases and error states
| Scenario | Expected behavior |
|---|---|
| Time-spent data not yet available for a given view event | Treat as 0 for that event; don't block the row from rendering |
| Buyer lead already hot via express_interest but no POC crosses 1 min | Remains hot — conditions are independent, not combined |
| Lead was hot only via bare discovery before this ships | Loses hot status at next scheduler run if no other condition is met — expected, not a bug |
| Multiple POCs on same lead, only one crosses 1 min | Lead qualifies hot — trigger is "any POC," not an aggregate across POCs |
| Same POC views multiple times, no single session hits 1 min | Does not qualify unless time-spent is cumulative — needs dev confirmation (per-session vs. cumulative) |
| Unverified Deals row with no discovery/teaser-unlock activity yet | Show "not yet viewed" rather than erroring |

## 7. UI/UX notes
- Unverified Deals: add Total Views and Avg Time Spent columns (scoped to discovery + investment teaser unlock), plus a drill-down CTA per row.
- No new page — drill-down can be a modal/expandable panel; exact UX pending design input, not blocking for dev scoping.

## 8. Analytics and success metrics
North star metric: Buyer lead → onboarding conversion rate among leads qualified hot via the time-spent trigger. Formula: onboarded_leads_via_timespent_trigger / total_leads_qualified_via_timespent_trigger. Target: TBD.

## 9. Open questions
| # | Question | Owner | Answer |
|---|---|---|---|
| 1 | Drill-down CTA content — confirm per-POC breakdown fields shown | Ashutosh | Yes it will show per POC data |

## 10. Out of scope / future considerations
- Conversion/reachout funnel tracking (hot lead → onboarding rate visibility, reachout counts).
- Seller lead engagement-gated hot logic (explicitly not requested).
- Backfill/re-evaluation of currently-hot leads under the new logic — decide separately whether to let them expire naturally or force-recompute.
