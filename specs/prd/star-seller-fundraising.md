# Star Seller Marking — Fundraising Sellers

Design: Figma — https://www.figma.com/design/RWMCvpU1gf3ydyJxTyQwsA/Sprint-Work?node-id=44664-45365&t=uWlnHgvT70eKSQpx-1

## 1. Problem

A star seller tells buyers this seller is deal-ready. For acquisition sellers, the star is earned: a biz user can mark star only once the highlight, investment teaser, and MIS or a seller call are in place.

Fundraising sellers need only a highlight. So a fundraising seller can be starred and shown to investors with no pitch deck and no diligence done. The star means less than it should.

The same gap opens when a star seller's objective changes. The seller keeps the star, but may not have the document the new buyer type expects.

## 2. What we are solving

Hold fundraising sellers to the same readiness standard as acquisition sellers, and keep a star seller's documents in line with their objective when it changes.

### Inputs the check uses

| Input | What counts |
|---|---|
| Primary objective | Acquisition or fundraising. Open to all does not change the rule — the primary objective decides. |
| Role | Admin (userType 2) or biz user (userType 4) |
| Highlight | Highlight present on the seller profile |
| Pitch deck | Pitch deck uploaded. Consent setting is ignored. |
| Investment teaser | Investment teaser uploaded |
| MIS | MIS document uploaded |
| Individual seller call | A call set up with the seller. Deal calls with buyers and cancelled calls do not count. |

## 3. Rules

| Primary objective | Admin | Biz user |
|---|---|---|
| Acquisition (live — no change) | Highlight + investment teaser | Highlight + investment teaser + (MIS or seller call) |
| Fundraising (new) | Highlight + pitch deck | Highlight + pitch deck + (MIS or seller call) |

- If anything is missing, one message lists every missing item.
- The check runs again at submit.

## 4. Objective change on a star seller

When a star seller's primary objective is changed and the document for the new objective is missing (investment teaser for acquisition, pitch deck for fundraising):

- The change is not saved.
- A message below the field says the seller is a star seller and names the document needed.
- An upload option for that document is shown right below the message.
- Once uploaded, the user saves the change in the same step.
- If the user cancels, the objective stays as it was. Any uploaded document stays on the profile.
- Only the document is checked here — not MIS or the seller call.

## 5. Acceptance criteria

### 5.1 Marking a fundraising seller star

| Given | When | Then |
|---|---|---|
| Highlight + pitch deck | Admin submits | Marked star |
| Highlight + pitch deck + MIS or seller call | Biz user submits | Marked star |
| Highlight + pitch deck, only a deal call (no MIS) | Biz user submits | Blocked — MIS or seller call named as missing |
| Highlight, no pitch deck | Admin or biz user submits | Blocked — pitch deck named as missing |
| No highlight, no pitch deck | Admin or biz user submits | Blocked — both named |
| Fundraising primary, open to all, no teaser, all else met | Admin or biz user submits | Marked star — teaser not needed |
| All requirements met, pitch deck consent off | Admin or biz user submits | Marked star |

### 5.2 Changing the objective of a star seller

| Given | When | Then |
|---|---|---|
| Star seller, no investment teaser | Objective changed to acquisition | Not saved; message and teaser upload option shown below the field |
| Star seller, no pitch deck | Objective changed to fundraising | Not saved; message and pitch deck upload option shown below the field |
| Upload option shown | Required document uploaded | Message clears; change saves in the same step |
| Upload option shown | Upload fails | Error shown; change not saved; user can retry |
| Upload option shown | User cancels | Previous objective kept |
| Star seller, document for new objective already uploaded | Objective changed | Saves normally; nothing shown |
| Seller is not star | Objective changed | Saves normally; no check |

### 5.3 Re-marking an existing star seller after unstar

| Given | When | Then |
|---|---|---|
| Seller starred before this release, now unstarred, no pitch deck | Admin or biz user marks star again | New rules checked; blocked — pitch deck named as missing |
| Seller starred before this release, now unstarred, no MIS or seller call | Biz user marks star again | Blocked — MIS or seller call named as missing |
| Seller unstarred, now meets all new requirements | Admin or biz user marks star again | Marked star |
| Seller starred before this release, never unstarred | No action taken | Stays star; no check |

## 6. Edge cases

| Scenario | Expected behavior |
|---|---|
| Document deleted between opening the form and submit | Blocked at submit |
| Document deleted after the seller is marked star | Star stays |
| Existing star fundraising seller without a pitch deck | Stays star until unstarred; new rules apply on any re-marking |
| Wrong file type in the upload option | Rejected; message names the type needed |
| Another user uploads the document while the change is blocked | Picked up on save; no second upload asked |
| Only the open-to-all setting changes | No check |

## 7. Success metric

Star conversion rate = sellers marked star ÷ star-ready sellers, by primary objective. A star-ready seller meets every biz user requirement for their primary objective.

## 8. Out of scope

- Changes to acquisition rules
- Re-checking sellers already marked star
- Removing star status automatically
