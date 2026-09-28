# Star Seller Marking — Fundraising Sellers — test cases
Status: APPROVED
Slug: star-seller-fundraising | Analysis: automation/specs/prd/star-seller-fundraising.analysis.md | Impact: automation/specs/features/star-seller-fundraising/impact.md
Requirements covered: 36 of 36  (2 manual: SSF-31, SSF-36)

Checked live on 2026-09-28 with `scripts/explore.py admin` (captures in `automation/reports/explore/sss-*` and
this run's `ssf-dataroom*`, `ssf-meeting*`). The admin session (auth/admin.json, userType 2) works. The cue card
of S5133 "test company" (/admin/notes/784d70cb-750a-4966-addf-f78656158ec5) is a usable funding-primary seller
today: "Primary: Funding | Secondary: Acquisition", "Star: No", 3 of 3 highlights, a pitch deck and an MIS in
"Important Documents", no investment teaser. The Data Room tab has "Upload Document" ("PDF, XLS, XLSX, size limit:
20 MB") with a "Company Pitchdeck" and a "Financials" (MIS) section. "Schedule Meeting" opens a "Select Meeting
Preferences" modal ("Meeting Type: 1 on 1 Call", slots, note); how a call becomes completed or cancelled was not
visible. The feature itself is not deployed yet, so the new message and the objective-change upload option were
not seen.

Common path used below:
- **Additional Details modal** = /admin/notes/<companyId> → "Additional details for this seller" block → "Edit" →
  modal "Additional Details for this Seller".
- **Objective modal** = /admin/notes/<companyId> → "Company's Objective" block → "Edit" → modal
  "Edit Company's Objective" ("Primary Objective*" dropdown, Cancel, Confirm).
- **The message** = the one block message the modal shows when star requirements are missing. It lists each
  missing item as "<item> is missing". Cases check that each named item appears with "missing", ignoring case,
  punctuation and order (Answer 2).

## 1. Scenario overview
| ID | Scenario | Role | Test cases | Priorities |
|---|---|---|---|---|
| S1 | Admin stars a ready funding-primary seller (highlights + pitch deck) | admin | 7 | P0 ×3, P1 ×2, P2 ×2 |
| S2 | Admin tries to star a funding-primary seller with highlights but no pitch deck | admin | 4 | P0, P1, P2 ×2 |
| S3 | Admin tries to star a funding-primary seller missing highlights and pitch deck | admin | 3 | P1, P2 ×2 |
| S4 | Admin stars a funding-primary seller whose other settings must not block the star | admin | 3 | P1, P2 ×2 |
| S5 | Admin marks acquisition-primary sellers (rules unchanged, combined message) | admin | 4 | P1 ×2, P2 ×2 |
| S6 | Biz user stars a ready funding-primary seller with an MIS | biz_user | 3 | P0 ×2, P1 |
| S7 | Biz user stars a funding-primary seller with a completed seller call and no MIS | biz_user | 1 | P1 |
| S8 | Biz user tries to star a funding-primary seller with no MIS and no counting seller call | biz_user | 4 | P1 ×2, P2 ×2 |
| S9 | Biz user tries to star a funding-primary seller with no pitch deck | biz_user | 2 | P1, P2 |
| S10 | Biz user marks acquisition-primary sellers (rules unchanged) | biz_user | 2 | P1, P2 |
| S11 | Documents change around the star: re-check at Confirm, deletion after star | admin | 2 | P2 ×2 |
| S12 | Admin changes a star funding seller to Acquisition with no teaser, uploads it and saves | admin | 5 | P0 ×2, P1 ×3 |
| S13 | Admin hits a failing or wrong upload in the objective-change upload option | admin | 3 | P2 ×3 |
| S14 | Admin changes a star acquisition seller to Funding with no pitch deck, uploads, then cancels | admin | 5 | P1 ×5 |
| S15 | Admin changes the objective of a non-star seller | admin | 1 | P1 |
| S16 | Biz user changes a star seller's objective | biz_user | 2 | P1 ×2 |
| S17 | Another tab uploads the missing document while the objective change is blocked | admin (two tabs) | 1 | P2 |
| S18 | Seller starred before this release: kept, edited, unstarred and re-marked | admin, biz_user | 5 | P1 ×5 |
| S19 | Rules with no browser check | manual | 2 | P2 ×2 |

## 2. The happy flow
S1-01 → S1-03 → S1-04 → S2-01 → S12-01 → S12-05 → S6-01 → S6-02

These eight are the `smoke` set. The admin part (first six) runs on one admin session in about 3–4 minutes:
it opens the Additional Details modal for a ready funding seller, stars it, checks the pitch-deck block on a second
funding seller, then changes the seller starred in S1-04 to Acquisition, uploads the teaser and saves. The biz_user
part (last two, about 1 minute) needs `auth/biz_user.json`, which is not saved yet, so S6-01 and S6-02 skip until it
is. The flow is destructive: it stars one seller, changes its objective and uploads a teaser (see section 6 for
reset).

## 3. Scenarios and their test cases

### S1 — Admin stars a ready funding-primary seller (highlights + pitch deck)
**Role:** admin · **Precondition:** admin session; a funding-primary, non-star seller with all 3 highlights (each 50+ characters) and a pitch deck, no investment teaser (seller "F-ready", e.g. S5133 today) · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S1-01 | Requirements panel lists the pitch deck for a funding seller | 1. Open /admin/notes/<F-ready> → 2. Open the Additional Details modal → 3. Read the "Star seller requirements" panel | Panel has a row naming "Pitch deck" under "All 3 company highlights" | P0 | happy | SSF-13 | auto |
| S1-02 | Admin panel has no call/MIS row | 1. Open the Additional Details modal for F-ready → 2. Read the "Star seller requirements" panel | Panel does not contain "A completed call with Seller or MIS document upload" | P1 | gating | SSF-14 | auto |
| S1-03 | Clicking Yes selects Star with no message | 1. Open the Additional Details modal for F-ready → 2. Click "Yes" under "Star" | "Yes" is selected and no "is missing" message appears | P0 | happy | SSF-01 | auto |
| S1-04 | Confirm saves the star (replaces today's highlights-only rule) | 1. Open the Additional Details modal for F-ready → 2. Click "Yes" under "Star" → 3. Click "Confirm" → 4. Reload the cue card | "Additional details for this seller" block reads "Star: Yes" | P0 | happy | SSF-01 | auto |
| S1-05 | Starred seller appears in the Star Sellers tab | Given S1-04 has run: 1. Open /admin/seller → 2. Click the "Star Sellers" tab → 3. Search for F-ready | F-ready's row shows the star mark after its S-id | P1 | state | SSF-01 | auto |
| S1-06 | Pitch deck row is labelled "A verified document" | 1. Open the Additional Details modal for a funding-primary non-star seller → 2. Read the pitch deck row | Row title reads "A verified document" with "Pitch deck" beneath it | P2 | copy | SSF-13 | auto |
| S1-07 | Cue card edit modal shows the same pitch deck requirement | 1. Open /admin/notes/<F-ready> → 2. Click "Edit Cue Card" → 3. Read the "Star seller requirements" panel at the top of "Cue card edit" | Panel has a row naming "Pitch deck" | P2 | copy | SSF-13 | auto |

### S2 — Admin tries to star a funding-primary seller with highlights but no pitch deck
**Role:** admin · **Precondition:** admin session; a funding-primary, non-star seller with all 3 highlights and no pitch deck ("F-nodeck") · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S2-01 | Clicking Yes shows the pitch deck is missing | 1. Open the Additional Details modal for F-nodeck → 2. Click "Yes" under "Star" | A message appears containing "pitch deck" and "missing" | P0 | gating | SSF-02 | auto |
| S2-02 | Seller stays non-star after the block | 1. Open the Additional Details modal for F-nodeck → 2. Click "Yes" under "Star" → 3. Click "Confirm" → 4. Reload the cue card | "Additional details for this seller" block reads "Star: No" | P1 | gating | SSF-02, SSF-15 | auto |
| S2-03 | Message names only the missing item | 1. Open the Additional Details modal for F-nodeck → 2. Click "Yes" under "Star" → 3. Read the message | Message does not name highlights | P2 | copy | SSF-09 | auto |
| S2-04 | "Back to cue card" closes the modal | 1. Open the Additional Details modal for F-nodeck → 2. Click "Back to cue card" | Modal closes and the cue card is visible | P2 | state | new — needs an id | auto |

### S3 — Admin tries to star a funding-primary seller missing highlights and pitch deck
**Role:** admin · **Precondition:** admin session; a funding-primary, non-star seller with fewer than 3 highlights and no pitch deck ("F-empty") · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S3-01 | One message names both highlights and pitch deck (replaces the first-item-only toast) | 1. Open the Additional Details modal for F-empty → 2. Click "Yes" under "Star" | One message names both "highlight" and "pitch deck", each with "missing" | P1 | copy | SSF-09 | auto |
| S3-02 | Highlights row shows the count added | 1. Open the Additional Details modal for F-empty → 2. Read the highlights row | Row reads "<N> of 3 added on the cue card" with N below 3 | P2 | state | SSF-13 | auto |
| S3-03 | A highlight under 50 characters does not count | Given a funding seller with a pitch deck and 3 highlights, one of them under 50 characters: 1. Open its Additional Details modal → 2. Click "Yes" under "Star" | Message names "highlight" as missing | P2 | edge | SSF-01 | auto |

### S4 — Admin stars a funding-primary seller whose other settings must not block the star
**Role:** admin · **Precondition:** admin session; funding-primary non-star sellers with highlights and a pitch deck, set up per case · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S4-01 | Funding seller open to acquisition needs no teaser | Given a seller showing "Primary: Funding \| Secondary: Acquisition", highlights, pitch deck, no teaser: 1. Open its Additional Details modal → 2. Click "Yes" → 3. Click "Confirm" → 4. Reload | Block reads "Star: Yes" | P1 | happy | SSF-10 | auto |
| S4-02 | Panel shows no teaser row for that seller | Given the same seller as S4-01, before starring: 1. Open its Additional Details modal → 2. Read the "Star seller requirements" panel | Panel does not contain "Investment teaser" | P2 | gating | SSF-10 | auto |
| S4-03 | Pitch deck consent off does not block | Given a seller with highlights and a pitch deck whose pitch deck consent setting is off (BLOCKED: where the consent setting is changed is unknown): 1. Open its Additional Details modal → 2. Click "Yes" → 3. Click "Confirm" → 4. Reload | Block reads "Star: Yes" | P2 | edge | SSF-11 | auto |

### S5 — Admin marks acquisition-primary sellers (rules unchanged, combined message)
**Role:** admin · **Precondition:** admin session; acquisition-primary non-star sellers set up per case · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S5-01 | Acquisition seller with highlights and teaser is starred | Given an acquisition seller "A-ready" with highlights and a teaser, no pitch deck: 1. Open its Additional Details modal → 2. Click "Yes" → 3. Click "Confirm" → 4. Reload | Block reads "Star: Yes" | P1 | happy | SSF-12 | auto |
| S5-02 | Missing teaser is named in the new format (replaces "Please add an investment teaser in order to mark this seller as a Star Seller.") | Given an acquisition seller with highlights and no teaser: 1. Open its Additional Details modal → 2. Click "Yes" | Message contains "investment teaser" and "missing" | P1 | gating | SSF-12 | auto |
| S5-03 | Acquisition panel still asks for the teaser | Given an acquisition non-star seller: 1. Open its Additional Details modal → 2. Read the panel | Panel shows "A qualifying document" with "Investment teaser" beneath it | P2 | copy | SSF-12 | auto |
| S5-04 | Acquisition seller missing both gets one combined message | Given an acquisition seller with fewer than 3 highlights and no teaser: 1. Open its Additional Details modal → 2. Click "Yes" | One message names both "highlight" and "investment teaser", each with "missing" | P2 | copy | SSF-09, SSF-12 | auto |

### S6 — Biz user stars a ready funding-primary seller with an MIS
**Role:** biz_user · **Precondition:** biz_user session (BLOCKED: auth/biz_user.json not saved yet); a funding-primary non-star seller with 3 highlights, a pitch deck and an MIS ("F-mis"; S5133 has all three today) · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S6-01 | Clicking Yes selects Star with no message | 1. Open the Additional Details modal for F-mis → 2. Click "Yes" under "Star" | "Yes" is selected and no "is missing" message appears | P0 | happy | SSF-03 | auto |
| S6-02 | Confirm saves the star | 1. Open the Additional Details modal for F-mis → 2. Click "Yes" → 3. Click "Confirm" → 4. Reload | Block reads "Star: Yes" | P0 | happy | SSF-03 | auto |
| S6-03 | Biz user panel shows the call/MIS row for a funding seller | 1. Open the Additional Details modal for a funding non-star seller → 2. Read the panel | Panel contains "A completed call with Seller or MIS document upload" | P1 | copy | SSF-13 | auto |

### S7 — Biz user stars a funding-primary seller with a completed seller call and no MIS
**Role:** biz_user · **Precondition:** biz_user session (BLOCKED: not saved); a funding-primary non-star seller with highlights, a pitch deck, no MIS, and one completed 1-on-1 seller call ("F-call"; BLOCKED: how a call is marked completed on QA was not seen) · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S7-01 | Completed seller call stands in for the MIS | 1. Open the Additional Details modal for F-call → 2. Click "Yes" → 3. Click "Confirm" → 4. Reload | Block reads "Star: Yes" | P1 | happy | SSF-04 | auto |

### S8 — Biz user tries to star a funding-primary seller with no MIS and no counting seller call
**Role:** biz_user · **Precondition:** biz_user session (BLOCKED: not saved); funding-primary non-star sellers with highlights and a pitch deck, no MIS, and the call state given per case (BLOCKED for S8-02..04: setting a call to completed, cancelled or deal-call on QA was not seen) · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S8-01 | No MIS and no call: MIS/seller call is named | Given no calls at all: 1. Open its Additional Details modal → 2. Click "Yes" | Message contains "MIS" and "missing" | P1 | gating | SSF-05 | auto |
| S8-02 | A deal call with a buyer does not count | Given only a deal call with a buyer: 1. Open its Additional Details modal → 2. Click "Yes" | Message contains "MIS" and "missing" | P1 | edge | SSF-06 | auto |
| S8-03 | A cancelled seller call does not count | Given only a cancelled 1-on-1 seller call: 1. Open its Additional Details modal → 2. Click "Yes" | Message contains "MIS" and "missing" | P2 | edge | SSF-07 | auto |
| S8-04 | A scheduled but not completed seller call does not count | Given only a scheduled, not yet completed 1-on-1 seller call: 1. Open its Additional Details modal → 2. Click "Yes" | Message contains "MIS" and "missing" | P2 | edge | SSF-05, SSF-04 | auto |

### S9 — Biz user tries to star a funding-primary seller with no pitch deck
**Role:** biz_user · **Precondition:** biz_user session (BLOCKED: not saved); funding-primary non-star sellers set up per case · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S9-01 | Pitch deck is named when only it is missing | Given highlights and an MIS, no pitch deck: 1. Open its Additional Details modal → 2. Click "Yes" | Message contains "pitch deck" and "missing" | P1 | gating | SSF-08 | auto |
| S9-02 | Everything missing is named in one message | Given fewer than 3 highlights, no pitch deck, no MIS, no call: 1. Open its Additional Details modal → 2. Click "Yes" | One message names "highlight", "pitch deck" and "MIS", each with "missing" | P2 | copy | SSF-09 | auto |

### S10 — Biz user marks acquisition-primary sellers (rules unchanged)
**Role:** biz_user · **Precondition:** biz_user session (BLOCKED: not saved); acquisition-primary non-star sellers with highlights and a teaser · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S10-01 | Acquisition seller without MIS or call is blocked | Given no MIS and no call: 1. Open its Additional Details modal → 2. Click "Yes" | Message contains "MIS" and "missing" | P1 | gating | SSF-12 | auto |
| S10-02 | Acquisition seller with an MIS is starred | Given an MIS: 1. Open its Additional Details modal → 2. Click "Yes" → 3. Click "Confirm" → 4. Reload | Block reads "Star: Yes" | P2 | happy | SSF-12 | auto |

### S11 — Documents change around the star: re-check at Confirm, deletion after star
**Role:** admin · **Precondition:** admin session; a ready funding seller (as F-ready); deleting a file from the Data Room (BLOCKED: no delete control seen in the Data Room capture) · **Path:** Additional Details modal in tab 1, Data Room in tab 2

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S11-01 | Pitch deck deleted before Confirm blocks the save | 1. Tab 1: open the Additional Details modal for the seller → 2. Click "Yes" → 3. Tab 2: open the same cue card → "Data Room" → delete every pitch deck → 4. Tab 1: click "Confirm" | Message contains "pitch deck" and "missing"; the block does not change to "Star: Yes" | P2 | edge | SSF-16, SSF-15 | auto |
| S11-02 | Deleting the pitch deck after starring keeps the star | Given the seller is already star: 1. Open "Data Room" → delete every pitch deck → 2. Reload the cue card | Block still reads "Star: Yes" | P2 | edge | SSF-17 | auto |

### S12 — Admin changes a star funding seller to Acquisition with no teaser, uploads it and saves
**Role:** admin · **Precondition:** admin session; a star, funding-primary seller with a pitch deck and no investment teaser ("F-star"; none exists on QA today, S1-04 creates one) · **Path:** /admin/notes/<companyId> → Objective modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S12-01 | Switching to Acquisition shows the star-seller message | 1. Open the Objective modal for F-star → 2. Select "Acquisition" in "Primary Objective*" → 3. Click "Confirm" | A message below the dropdown contains "star" and "investment teaser" | P0 | gating | SSF-18, SSF-19 | auto |
| S12-02 | Teaser upload option appears right below the message | 1. Repeat S12-01 → 2. Look directly below the message | An investment teaser upload option is shown | P1 | state | SSF-20 | auto |
| S12-03 | The objective is not saved while blocked | 1. Repeat S12-01 → 2. Reload the cue card | "Company's Objective" still reads "Primary: Funding" | P1 | gating | SSF-18 | auto |
| S12-04 | Uploading the teaser clears the message | 1. Repeat S12-01 → 2. Upload a PDF in the upload option | The star-seller message is gone | P1 | happy | SSF-22 | auto |
| S12-05 | Change saves in the same step after upload | 1. Open the Objective modal for F-star → 2. Select "Acquisition" → 3. Click "Confirm" → 4. Upload a PDF in the upload option → 5. Click "Confirm" → 6. Reload | "Company's Objective" reads "Primary: Acquisition" | P0 | happy | SSF-22 | auto |

### S13 — Admin hits a failing or wrong upload in the objective-change upload option
**Role:** admin · **Precondition:** admin session; F-star in the blocked state of S12-01 (run before S12-04/S12-05); for S13-01/02 the upload request is forced to fail with network mocking · **Path:** Objective modal → upload option

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S13-01 | Failed upload shows an error | 1. Reach the blocked state (S12-01) → 2. Make the upload request fail → 3. Upload a PDF | An upload error is shown and the star-seller message stays | P2 | edge | SSF-23 | auto |
| S13-02 | User can retry after a failed upload | 1. Do S13-01 → 2. Let requests succeed again → 3. Upload a PDF again in the same option | The star-seller message is gone | P2 | edge | SSF-23 | auto |
| S13-03 | Wrong file type is rejected with the needed type | 1. Reach the blocked state → 2. Choose a .docx file in the upload option | A message naming "PDF" appears and the star-seller message stays | P2 | edge | SSF-24 | auto |

### S14 — Admin changes a star acquisition seller to Funding with no pitch deck, uploads, then cancels
**Role:** admin · **Precondition:** admin session; a star, acquisition-primary seller with a teaser and no pitch deck ("A-star"; S5-01 creates one from A-ready) · **Path:** /admin/notes/<companyId> → Objective modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S14-01 | Switching to Funding names the pitch deck | 1. Open the Objective modal for A-star → 2. Select "Funding" → 3. Click "Confirm" | A message below the dropdown contains "star" and "pitch deck" | P1 | gating | SSF-21 | auto |
| S14-02 | Pitch deck upload option appears below the message | 1. Repeat S14-01 → 2. Look directly below the message | A pitch deck upload option is shown | P1 | state | SSF-21 | auto |
| S14-03 | Cancel keeps the previous objective | 1. Repeat S14-01 → 2. Upload a PDF in the upload option → 3. Click "Cancel" → 4. Reload | "Company's Objective" still reads "Primary: Acquisition" | P1 | happy | SSF-25 | auto |
| S14-04 | Pitch deck uploaded before Cancel stays on the profile | Given S14-03 has run: 1. Reload the cue card → 2. Read "Important Documents" | A pitch deck file is listed under "Pitch Deck" | P1 | state | SSF-26 | auto |
| S14-05 | With the document present the change saves with no message | Given S14-04 has run: 1. Open the Objective modal → 2. Select "Funding" → 3. Click "Confirm" → 4. Reload | No star-seller message appeared and the block reads "Primary: Funding" | P1 | happy | SSF-27 | auto |

### S15 — Admin changes the objective of a non-star seller
**Role:** admin · **Precondition:** admin session; a non-star funding-primary seller with no investment teaser · **Path:** /admin/notes/<companyId> → Objective modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S15-01 | Non-star seller changes objective with no check | 1. Open the Objective modal → 2. Select "Acquisition" → 3. Click "Confirm" → 4. Reload → 5. Change it back to "Funding" (cleanup) | After step 4 the block reads "Primary: Acquisition" and no star-seller message appeared | P1 | happy | SSF-28 | auto |

### S16 — Biz user changes a star seller's objective
**Role:** biz_user · **Precondition:** biz_user session (BLOCKED: not saved); star sellers set up per case · **Path:** /admin/notes/<companyId> → Objective modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S16-01 | Biz user gets the same block on a missing teaser | Given a star funding seller with no teaser (e.g. F-mis after S6-02): 1. Open the Objective modal → 2. Select "Acquisition" → 3. Click "Confirm" → 4. Click "Cancel" (cleanup) | After step 3 a message below the dropdown contains "star" and "investment teaser" | P1 | gating | SSF-18, SSF-19 | auto |
| S16-02 | Objective change ignores MIS and seller call | Given a star seller with a teaser and a pitch deck but no MIS and no call (e.g. A-star after S14-05, now funding): 1. Open the Objective modal → 2. Select "Acquisition" → 3. Click "Confirm" → 4. Reload | No message appeared and the block reads "Primary: Acquisition" | P1 | happy | SSF-29 | auto |

### S17 — Another tab uploads the missing document while the objective change is blocked
**Role:** admin (two tabs of one session) · **Precondition:** admin session; a star funding seller with no teaser (as F-star); uploading a teaser from a second tab (BLOCKED: the Data Room upload categories list no "Investment teaser" section, and the rail teaser block shows only for acquisition-primary sellers) · **Path:** tab 1 Objective modal, tab 2 cue card

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S17-01 | Teaser uploaded elsewhere is picked up on save | 1. Tab 1: reach the blocked state (S12-01) → 2. Tab 2: upload an investment teaser for the same seller → 3. Tab 1: click "Confirm" without using the upload option → 4. Reload | Block reads "Primary: Acquisition" with no second upload asked | P2 | edge | SSF-30 | auto |

### S18 — Seller starred before this release: kept, edited, unstarred and re-marked
**Role:** admin, biz_user · **Precondition:** admin session; a funding-primary seller with highlights, no pitch deck, no MIS, no call, marked star **before the release reaches QA** under today's rules ("L-star"; none exists today, see section 6); S18-04 needs biz_user (BLOCKED: not saved). Run in the order below: S18-03 consumes the legacy star. · **Path:** /admin/notes/<companyId> → Additional Details modal

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S18-01 | Legacy star without a pitch deck stays star | 1. Open /admin/notes/<L-star> | Block reads "Star: Yes" | P1 | state | SSF-32 | auto |
| S18-02 | Legacy star can still save other details | 1. Open the Additional Details modal for L-star → 2. Change "Growth" to another value → 3. Click "Confirm" → 4. Reload | Block shows the new Growth value and still "Star: Yes" | P1 | state | SSF-32 | auto |
| S18-03 | Unstarred legacy seller is blocked on the pitch deck | 1. Open the Additional Details modal for L-star → 2. Click "No" → 3. Click "Confirm" → 4. Reopen the modal → 5. Click "Yes" | Message contains "pitch deck" and "missing" | P1 | gating | SSF-33 | auto |
| S18-04 | Biz user re-marking is blocked on MIS/seller call | Given S18-03 ran and a pitch deck was then uploaded to L-star's Data Room: 1. As biz_user open its Additional Details modal → 2. Click "Yes" | Message contains "MIS" and "missing" | P1 | gating | SSF-34 | auto |
| S18-05 | Admin re-marks once the new rules are met | Given S18-04 ran: 1. As admin open its Additional Details modal → 2. Click "Yes" → 3. Click "Confirm" → 4. Reload | Block reads "Star: Yes" | P1 | happy | SSF-35 | auto |

### S19 — Rules with no browser check
**Role:** manual · **Precondition:** see each case · **Path:** none

| TC | Title | Steps | Expected result | Pri | Type | Req | Run as |
|---|---|---|---|---|---|---|---|
| S19-01 | Changing only the open-to-all setting runs no check | Manual: the secondary objective checkbox is disabled in the Objective modal ("Secondary Objective can't be edited"); confirm with dev whether any other surface changes it, and if so change only that on a star seller without the documents | No star-seller message; setting saved | P2 | edge | SSF-31 | manual |
| S19-02 | Star conversion rate is reported by primary objective | Manual: check the analytics report | Report shows sellers marked star ÷ star-ready sellers, split by primary objective | P2 | state | SSF-36 | manual |

## 4. Detail blocks
None. No case needs more than six steps.

## 5. Requirement coverage
| Req ID | Requirement | Test cases | Covered |
|---|---|---|---|
| SSF-01 | Admin can star a funding seller with highlights + pitch deck | S1-03, S1-04, S1-05, S3-03 | yes |
| SSF-02 | Admin blocked without pitch deck; pitch deck named | S2-01, S2-02 | yes |
| SSF-03 | Biz user stars funding seller with highlights + pitch deck + MIS | S6-01, S6-02 | yes |
| SSF-04 | Biz user stars with a seller call instead of MIS | S7-01, S8-04 | yes |
| SSF-05 | Biz user blocked with neither MIS nor seller call | S8-01, S8-04 | yes |
| SSF-06 | Deal call with a buyer does not count | S8-02 | yes |
| SSF-07 | Cancelled seller call does not count | S8-03 | yes |
| SSF-08 | Biz user blocked without pitch deck | S9-01 | yes |
| SSF-09 | One message names every missing item | S2-03, S3-01, S5-04, S9-02 | yes |
| SSF-10 | Funding seller open to acquisition needs no teaser | S4-01, S4-02 | yes |
| SSF-11 | Pitch deck consent off does not block | S4-03 | yes |
| SSF-12 | Acquisition rules unchanged | S5-01, S5-02, S5-03, S5-04, S10-01, S10-02 | yes |
| SSF-13 | Funding panel lists pitch deck (and call/MIS for biz user) | S1-01, S1-06, S1-07, S3-02, S6-03 | yes |
| SSF-14 | Admin panel never shows the call/MIS row | S1-02 | yes |
| SSF-15 | Check runs again at Confirm | S2-02, S11-01 | yes |
| SSF-16 | Document deleted before Confirm blocks submit | S11-01 | yes |
| SSF-17 | Document deleted after star keeps the star | S11-02 | yes |
| SSF-18 | Star seller to acquisition with no teaser: not saved | S12-01, S12-03, S16-01 | yes |
| SSF-19 | Message says star seller and names the teaser | S12-01, S16-01 | yes |
| SSF-20 | Teaser upload option below the message | S12-02 | yes |
| SSF-21 | Star seller to funding with no pitch deck: blocked, message, upload option | S14-01, S14-02 | yes |
| SSF-22 | After upload the message clears and the change saves in the same step | S12-04, S12-05 | yes |
| SSF-23 | Failed upload: error, not saved, retry | S13-01, S13-02 | yes |
| SSF-24 | Wrong file type rejected, type named | S13-03 | yes |
| SSF-25 | Cancel keeps the previous objective | S14-03 | yes |
| SSF-26 | Document uploaded before Cancel stays | S14-04 | yes |
| SSF-27 | Star seller with the document changes objective normally | S14-05, S16-02 | yes |
| SSF-28 | Non-star seller changes objective with no check | S15-01 | yes |
| SSF-29 | Objective-change check ignores MIS and seller call | S16-02 | yes |
| SSF-30 | Document uploaded by another user is picked up on save | S17-01 | yes |
| SSF-31 | Only the open-to-all setting changes: no check | S19-01 | manual |
| SSF-32 | Pre-release star never unstarred stays star, no check | S18-01, S18-02 | yes |
| SSF-33 | Unstarred legacy seller without pitch deck blocked on re-marking | S18-03 | yes |
| SSF-34 | Unstarred legacy seller without MIS/call blocked for biz user | S18-04 | yes |
| SSF-35 | Unstarred seller meeting new rules can be re-marked | S18-05 | yes |
| SSF-36 | Star conversion rate by primary objective reported | S19-02 | manual |

## 6. Test data and run order
**Sellers each run needs** (all on qa.done.deals; "highlights" = all 3 company highlights, each 50+ characters, added via "Edit Cue Card"; pitch deck and MIS via Data Room → "Upload Document" into "Company Pitchdeck" / "Financials"):

| Name | Primary | Star | Highlights | Pitch deck | Teaser | MIS | Calls | Used by |
|---|---|---|---|---|---|---|---|---|
| F-ready | Funding | No | 3 | yes | no | any | any | S1, then becomes F-star for S12/S13/S17 |
| F-nodeck | Funding | No | 3 | no | no | no | none | S2 |
| F-empty | Funding | No | < 3 | no | no | no | none | S3, S9-02 |
| F-short | Funding | No | 3, one under 50 chars | yes | no | – | – | S3-03 |
| F-open | Funding, open to acquisition | No | 3 | yes | no | – | – | S4-01, S4-02 |
| F-noconsent | Funding | No | 3 | yes, consent off | no | – | – | S4-03 |
| A-ready | Acquisition | No | 3 | no | yes | no | none | S5-01, S5-03, then becomes A-star for S14, S16-02 |
| A-noteaser / A-empty | Acquisition | No | 3 / < 3 | – | no | – | – | S5-02 / S5-04 |
| F-mis | Funding | No | 3 | yes | no | yes | none | S6 (S5133 fits today), then S16-01 |
| F-call | Funding | No | 3 | yes | no | no | 1 completed seller call | S7 |
| F-nomis, F-dealcall, F-cancelled, F-scheduled | Funding | No | 3 | yes | no | no | none / buyer deal call / cancelled / scheduled | S8-01..04 |
| F-mis-nodeck | Funding | No | 3 | no | no | yes | – | S9-01 |
| A-biz-nomis / A-biz-mis | Acquisition | No | 3 | – | yes | no / yes | none | S10 |
| Non-star funding | Funding | No | any | – | no | – | – | S15 |
| L-star | Funding | **Yes, set before release** | 3 | no | no | no | none | S18 |

- **Destructive and consumable.** Every case that clicks Confirm on Star = Yes, changes an objective or uploads
  consumes a seller state. Reset after each run: set Star to No, set the objective back, remove uploaded files
  (Data Room delete was not seen, so a fresh seller from "Create a Seller" on /admin/seller may be the cheaper
  reset). Read-only cases (S1-01, S1-02, S1-06, S1-07, S3-02, S4-02, S5-03, S6-03) and the block cases that only
  click Yes consume nothing.
- **Chains inside a run:** S1-04 → S12 (S13 runs between S12-03 and S12-04, S17 before S12-04 too) ;
  S5-01 → S14-01..05 → S16-02 ; S6-02 → S16-01 ; S18-01 → S18-02 → S18-03 → (upload pitch deck) → S18-04 → S18-05.
- **Legacy star (S18) must be prepared before the feature deploys to QA:** take a funding seller with 3
  highlights and no pitch deck and mark it star under today's rules (today only highlights are needed). Once the
  release is on QA, a legacy star cannot be recreated, and S18-03 unstars it for good. Keep at least one spare, or
  S18-01/02 can run on a legacy star that is never unstarred.
- **Biz user session:** save `auth/biz_user.json` with a userType 4 QA login (`python scripts/save_auth_state.py
  biz_user`, after impact rows 1-3). Until then S6-S10, S16 and S18-04 skip. Env: `DD_BIZ_USER_STATE` if the
  file lives elsewhere.
- **Calls:** S7 and S8-02..04 need a seller call in a given status. "Schedule Meeting" only creates a request
  ("1 on 1 Call" plus slots); how QA moves it to completed or cancelled, and how to get a buyer deal call, is not
  known. Needs a data recipe from dev.
- **Files:** a small valid PDF (teaser/pitch deck), a .docx (S13-03), and network mocking of the upload request
  (S13-01/02).
- No cross-role phase ordering beyond S6-02 → S16-01 and S18-03 → S18-04 → S18-05.

## 7. Assumptions
1. Only a completed 1-on-1 seller call counts; scheduled, cancelled and buyer deal calls do not (Answer 1).
2. The block message is one message listing each missing item as "<item> is missing", for both acquisition and
   funding sellers. Cases match the item keyword plus "missing", ignoring case, punctuation and order. Item
   keywords assumed: "highlight", "pitch deck", "investment teaser", and "MIS" for the MIS-or-seller-call item
   (Answer 2 example "MIS is missing").
3. Yes stays clickable and clicking it with requirements missing shows the message; the check re-runs at
   Confirm. The Figma disabled chips / "Pending requirements" / disabled Confirm state is not tested (Answer 3).
4. A legacy star who fails the new rules can still save other additional details (e.g. Growth) while Star stays
   Yes; only switching No → Yes runs the check (Answer 4, assumed, not confirmed by the user).
5. The objective-change check lives in the "Edit Company's Objective" modal on the admin cue card, below
   "Primary Objective*"; the message mentions "star" and names the document; the upload option sits right below
   it (Answer 5, assumed). Cases select the new objective and then click Confirm; if the message already appears
   on selection, the case still passes.
6. "Highlight present" means all 3 company highlights, each 50+ characters (analysis Q6).
7. "Back to cue card" (Figma) is in scope as a UI element; S2-04 is `new — needs an id` and should be dropped if
   it does not ship (Q7).
8. The funding pitch deck row reads "A verified document" / "Pitch deck"; the acquisition row keeps "A qualifying
   document" / "Investment teaser" (Q8). Only S1-06 and S5-03 depend on this.
9. The objective-change upload option accepts PDF only, up to 20 MB, like today's teaser upload (Q9); S13-03
   expects "PDF" to be named.
10. The objective-change check applies to admin and biz user, on the admin cue card only (Q10).
11. The open-to-all setting is not editable in the UI, so SSF-31 is manual (Q11).
12. Judgement call: S2-01 (the pitch deck block) is P0 although it is a gating case. Without it the smoke run
    would pass even if the new funding rule never shipped, since starring a ready seller also works today.
13. Judgement call: rules that apply to both roles (SSF-09 to SSF-11, SSF-15 to SSF-17, SSF-19 to SSF-28, SSF-30,
    SSF-33, SSF-35) are run as admin only, with a biz_user case only where the biz rule differs (SSF-29 and
    SSF-34) plus S16-01 to show the objective block reaches the biz user too. This keeps the table short.
14. Judgement call: S1-04 still passes on today's build (a highlights-only funding seller can be starred today),
    so it proves the save path, not the new rule; S2-01 proves the rule.

## 8. Review
Approved by the user on 2026-09-28 ("approve").
- Approved: all 59 cases (S1-01 .. S19-02), including S2-04 ("Back to cue card") as written.
- Changed: none.
- Dropped: none.
