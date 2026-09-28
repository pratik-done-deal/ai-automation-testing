# Star Seller Marking — Fundraising Sellers — requirements analysis
Status: READY
Slug: star-seller-fundraising | Roles: admin (userType 2), biz user (userType 4) | PRD: automation/specs/prd/star-seller-fundraising.md | Figma: https://www.figma.com/design/RWMCvpU1gf3ydyJxTyQwsA/Sprint-Work?node-id=44664-45365 (section "Edit Star Seller - Fundraising"; only frame 44664:47911 could be viewed, see section 8)
Explored: admin:/admin/seller (list + Star Sellers tab), admin:/admin/notes/:companyId cue card for 6 sellers (star acquisition, non-star acquisition, non-star funding), admin: "Additional Details for this Seller" modal, admin: "Edit Company's Objective" modal (+ dropdown), admin: "Cue card edit" modal. All read-only; every modal closed with Cancel.

## 1. Summary
Star marking is gated by a readiness check. Today only acquisition-primary sellers need a document (investment teaser; biz users also need MIS or a completed seller call). Funding-primary sellers only need the 3 highlights.
The feature adds the same standard for funding-primary sellers: highlight + pitch deck (admin), plus MIS or seller call (biz user). It also adds a check when a **star** seller's primary objective is changed: if the document for the new objective is missing (teaser for acquisition, pitch deck for funding) the change is not saved, a message and an upload option appear below the field, and uploading lets the change save in the same step.
Existing star sellers are not re-checked; the new rules apply on the next (re-)marking.

## 2. How it works today
| Screen | Route | Role | Current behaviour | Capture |
|---|---|---|---|---|
| Sellers list | /admin/seller | admin | Tabs incl. "Star Sellers"; star sellers show ⭐️ after the S-id. Filters incl. "Primary Purpose", "Star Seller". Clicking a name opens the seller dashboard in a new tab (/admin-user/dashboard/:id). Row "Actions" can also open the Additional Details modal (code: AdminSeller/ActionModals, not walked). | sss-admin-seller |
| Admin cue card | /admin/notes/:companyId | admin | Right rail: "Investment Teaser" block (Upload, "PDF, size limit: 20 MB") shown **only for acquisition-primary**; "Company's Objective" ("Primary: Acquisition \| Secondary: Funding", Edit); "Additional details for this seller" ("Star: Yes/No", Edit); "Important Documents" lists Pitch Deck / MIS / Cap Table with "View Data Room". Funding-primary card shows "View Pitch Deck", no teaser block. | sss-admin-cuecard-1-view-cue-card, sss-artinci-*, sss-funding-nonstar-* |
| Additional Details modal | cue card > Additional details > Edit | admin | "Star" Yes/No chips; "Pending requirements" pill when the check fails. "Star seller requirements" panel: "All 3 company highlights" ("N of 3 added on the cue card"); for acquisition only "A qualifying document / Investment teaser"; for biz user only "A completed call with Seller or MIS document upload / One of them must be completed". Funding-primary shows only the highlights row. Clicking Yes when unmet shows an error toast and does not select; the check re-runs on Confirm. | sss-artinci-additional-modal, sss-artinci-star-yes-click, sss-funding-nonstar-additional-modal |
| Current block message (acquisition) | toast at top of modal | admin | One message, first missing item only: "Please add an investment teaser in order to mark this seller as a Star Seller." Other live copies (code): "Please add all 3 company highlights in order to mark this seller as a Star Seller." / "Please mark a call with the seller as completed or add an MIS document in order to mark this seller as a Star Seller." | sss-artinci-star-yes-click |
| Edit Company's Objective modal | cue card > Company's Objective > Edit | admin | "Primary Objective*" dropdown: Acquisition, Funding. Checkbox "Open for funding as well" / "Open for acquisition as well" is **disabled** (tooltip "Secondary Objective can't be edited"). Cancel / Confirm. No star check today. | sss-artinci-objective-modal, sss-funding-nonstar-objective-dropdown |
| Cue card edit modal | cue card > Edit Cue Card | admin | Title "Cue card edit"; shows the same "Star seller requirements" panel at top; highlights 1-3, fields, "Discard Changes" / "Save & Close". | sss-artinci-editcuecard-modal |
| Seller calls | cue card > "Schedule Meeting" | admin / biz | Calls with the seller; live rule counts only calls with status completed and referenceType seller. Not walked. | — |
| Pitch deck / MIS upload | Data Room ("View Data Room") | admin / biz | Documents are listed on the cue card; upload lives in the data room. Not walked. | — |

Captures are in `automation/reports/explore/` (prefix `sss-`). Live rule notes from code (cross-check only): a highlight counts only if it has >= 50 characters, and all 3 are required.

## 3. What changes
| # | Before (today) | After (PRD) | Delta |
|---|---|---|---|
| 1 | Funding-primary: admin and biz user need only 3 highlights | Admin: highlight + pitch deck | new doc gate |
| 2 | Funding-primary biz user: no MIS/call requirement | Biz user: highlight + pitch deck + (MIS or seller call) | new gate |
| 3 | Requirements panel for funding shows highlights row only | Panel shows pitch deck row (Figma: "A verified document / Pitch deck") and, for biz user, the call/MIS row | new rows, new label |
| 4 | Block message names only the first missing item | "One message lists every missing item" | copy/logic change (scope for acquisition unclear, Q2) |
| 5 | Yes chip clickable; toast on click when unmet | Figma: Yes/No chips shown disabled while requirements pending | interaction change (Q3) |
| 6 | Objective change never checks star status | Star seller: change blocked if new objective's document missing; message + upload option below field; saves in same step after upload | new flow |
| 7 | Figma shows "Back to cue card" button in Additional Details modal | not mentioned in PRD | Figma-only (Q7) |

## 4. Requirements
| ID | Requirement (one sentence) | Source | Role | Type | Verify via | Exists today |
|---|---|---|---|---|---|---|
| SSF-01 | Admin can mark a funding-primary seller star when highlights and a pitch deck are present. | PRD 3, 5.1 | admin | rule | flow | partial (no pitch deck needed today) |
| SSF-02 | Admin cannot mark a funding-primary seller star without a pitch deck; the message names the pitch deck. | PRD 5.1 | admin | gating | flow | no |
| SSF-03 | Biz user can mark a funding-primary seller star with highlights + pitch deck + MIS. | PRD 3, 5.1 | biz | rule | flow | no |
| SSF-04 | Biz user can mark a funding-primary seller star with highlights + pitch deck + an individual seller call (no MIS). | PRD 3, 5.1 | biz | rule | flow | no |
| SSF-05 | Biz user cannot mark a funding-primary seller star with highlights + pitch deck but neither MIS nor seller call; message names MIS or seller call. | PRD 5.1 | biz | gating | flow | no |
| SSF-06 | A deal call with a buyer does not satisfy the seller-call requirement. | PRD 2, 5.1 | biz | edge-case | flow | yes (acquisition) |
| SSF-07 | A cancelled seller call does not satisfy the seller-call requirement. | PRD 2 | biz | edge-case | flow | yes (acquisition; only completed counts) |
| SSF-08 | Biz user cannot mark a funding-primary seller star without a pitch deck; message names the pitch deck. | PRD 5.1 | biz | gating | flow | no |
| SSF-09 | With neither highlight nor pitch deck, one message names both (admin and biz user). | PRD 3, 5.1 | admin, biz | copy | UI | no (first item only today) |
| SSF-10 | A funding-primary seller open to acquisition, with no investment teaser but all else met, can be marked star (teaser not required). | PRD 5.1 | admin, biz | rule | flow | yes |
| SSF-11 | Pitch deck consent setting off does not block marking star. | PRD 2, 5.1 | admin, biz | edge-case | flow | n/a |
| SSF-12 | Acquisition rules are unchanged: admin needs highlights + teaser; biz user also needs MIS or completed seller call. | PRD 3, 8 | admin, biz | rule | flow | yes |
| SSF-13 | The requirements panel for a funding-primary seller lists the pitch deck requirement (and call/MIS row for biz user only). | Figma 44664:47911, PRD 3 | admin, biz | copy | UI | no |
| SSF-14 | The requirements panel for an admin never shows the call/MIS row. | live, Figma | admin | rule | UI | yes (acquisition) |
| SSF-15 | The check runs again at submit (Confirm), not only when Yes is clicked. | PRD 3 | admin, biz | gating | flow | yes |
| SSF-16 | A document deleted between opening the modal and Confirm blocks the submit. | PRD 6 | admin, biz | edge-case | flow | partial (depends on refetch) |
| SSF-17 | Deleting a document after the seller is star leaves the star in place. | PRD 6 | admin, biz | edge-case | flow | yes |
| SSF-18 | A star seller changed to acquisition with no investment teaser: change not saved. | PRD 4, 5.2 | admin, biz | lock | flow | no |
| SSF-19 | In that case a message below the field says the seller is a star seller and names the investment teaser. | PRD 4, 5.2 | admin, biz | copy | UI | no |
| SSF-20 | In that case an investment teaser upload option is shown right below the message. | PRD 4, 5.2 | admin, biz | flow | UI | no |
| SSF-21 | A star seller changed to funding with no pitch deck: change not saved, message names the pitch deck, pitch deck upload option shown. | PRD 4, 5.2 | admin, biz | lock | flow | no |
| SSF-22 | After the required document is uploaded the message clears and the objective change saves in the same step. | PRD 4, 5.2 | admin, biz | flow | flow | no |
| SSF-23 | If the upload fails, an error is shown, the change is not saved, and the user can retry. | PRD 5.2 | admin, biz | edge-case | flow | no |
| SSF-24 | A wrong file type in the upload option is rejected with a message naming the required type. | PRD 6 | admin, biz | edge-case | UI | partial (teaser upload is PDF-only today) |
| SSF-25 | Cancel keeps the previous objective. | PRD 4, 5.2 | admin, biz | flow | flow | yes (no check today) |
| SSF-26 | A document uploaded before Cancel stays on the profile. | PRD 4 | admin, biz | edge-case | flow | no |
| SSF-27 | A star seller whose new objective's document already exists changes objective normally with nothing shown. | PRD 5.2 | admin, biz | rule | flow | yes |
| SSF-28 | A non-star seller changes objective normally with no check. | PRD 5.2 | admin, biz | rule | flow | yes |
| SSF-29 | The objective-change check looks only at the document, not MIS or seller call. | PRD 4 | biz | rule | flow | no |
| SSF-30 | A document uploaded by another user while the change is blocked is picked up on save, with no second upload asked. | PRD 6 | admin, biz | edge-case | flow | no |
| SSF-31 | Changing only the open-to-all setting runs no check. | PRD 6 | admin, biz | edge-case | manual | n/a (setting not editable in UI today) |
| SSF-32 | A seller starred before release and never unstarred stays star with no check. | PRD 5.3, 8 | admin, biz | rule | UI | yes |
| SSF-33 | A pre-release star seller, unstarred, with no pitch deck, is blocked on re-marking (pitch deck named). | PRD 5.3 | admin, biz | gating | flow | no |
| SSF-34 | A pre-release star seller, unstarred, with no MIS or seller call, is blocked on biz-user re-marking. | PRD 5.3 | biz | gating | flow | no |
| SSF-35 | An unstarred seller meeting all new requirements can be re-marked star. | PRD 5.3 | admin, biz | flow | flow | partial |
| SSF-36 | Star conversion rate by primary objective is reported. | PRD 7 | — | non-functional | manual | no |

## 5. Screens
| Screen | Figma node / route | State | Exact visible copy |
|---|---|---|---|
| Additional Details modal (admin, funding, pending) | 44664:47911 | pending | "Additional Details for this Seller", "Star", "Pending requirements", "Yes" "No" (disabled), "Star seller requirements", "All 3 company highlights" / "0 of 3 added on the cue card", "A verified document" / "Pitch deck", "Back to cue card", "Cancel", "Confirm" (disabled) |
| Additional Details modal (live, acquisition) | /admin/notes/:id | pending / met | "Pending requirements", "A qualifying document" / "Investment teaser", "A completed call with Seller or MIS document upload" / "One of them must be completed" (biz only) |
| Additional Details modal (biz user, funding) | 44664:47290 | pending | not viewed (Figma rate limit) |
| Cue card edit modal with requirements panel | 44671:50034, 44671:50563, 44664:47384, 44664:47990 | to be filled | not viewed; live: "Cue card edit", "Star seller requirements", "Discard Changes", "Save & Close" |
| Edit Company's Objective modal (star seller, doc missing) | section 44671:52438 (frames 44671:50984, 44671:51465, 44671:51950) | blocked / upload shown | not viewed; message copy unknown. Live: "Edit Company's Objective", "Primary Objective*", options "Acquisition" / "Funding", "Open for funding as well", "Cancel", "Confirm" |
| Block message (live) | toast | error | "Please add an investment teaser in order to mark this seller as a Star Seller." |

## 6. Flow and sequencing
- Single-role flows; no cross-role dependency and no login created by another role. Admin (userType 2) and biz user (userType 4) act independently. Only an admin session exists (nadeem@done.deals, confirmed userType 2: no call/MIS row in the panel).
- Route: /admin/seller → seller → "View cue card" → /admin/notes/:companyId. Star marking: "Additional details for this seller" > Edit (also reachable from the seller list Actions). Objective: "Company's Objective" > Edit. Documents: Investment Teaser block (acquisition only) and Data Room. Calls: "Schedule Meeting".
- Preconditions (test data needed, none found on QA): funding-primary non-star sellers in each combination (highlights ± pitch deck ± MIS ± completed seller call ± deal call ± cancelled call ± consent off); funding-primary seller open to acquisition without teaser; star acquisition seller without teaser (Artinci S6261 qualifies today), star funding seller without pitch deck (none found among 17 star sellers sampled, all acquisition-primary); a seller starred before release.
- Destructive / data-consuming: marking star, unstarring, changing objective, uploading documents, completing/cancelling calls, deleting documents. Every positive test changes the seller; each run needs a reset (unstar, revert objective, delete uploaded doc) or fresh sellers. Pre-release stars cannot be recreated after release: once unstarred in a test they are consumed.

## 7. Open questions
1. **blocking** — Individual seller call: the PRD says "a call set up with the seller"; the live rule and panel copy count only a **completed** call ("A completed call with Seller or MIS document upload"). For funding sellers, does a scheduled-but-not-completed seller call count?
2. **blocking** — "One message lists every missing item": does this also change the acquisition message (today it names only the first missing item), given acquisition rules are marked "no change"? And what is the exact combined copy?
3. **blocking** — Figma shows Yes/No disabled with "Pending requirements" and Confirm disabled; the PRD and the live app show a clickable Yes that raises a message. Which interaction ships: disabled chips, or a message on click/submit?
4. **blocking** — The live Confirm re-checks whenever Star = Yes, so today a pre-release star seller who fails the rules cannot save any other additional detail (e.g. Growth). After release, should editing other fields of a legacy star funding seller without a pitch deck save, or be blocked? (PRD says "stays star; no check".)
5. **blocking** — Where does the objective-change check appear: inside the "Edit Company's Objective" modal (below the Primary Objective dropdown, before Confirm)? What is the exact message copy? The Figma frames for this (section 44671:52438) could not be read.
6. **deferrable** — "Highlight present" is assumed to mean the live rule (all 3 highlights, each >= 50 characters).
7. **deferrable** — "Back to cue card" button in the Figma modal: assumed in scope as a UI element; confirm.
8. **deferrable** — Label change: Figma "A verified document" vs live "A qualifying document". Assumed Figma copy applies to funding; acquisition label unchanged.
9. **deferrable** — Upload option file rules: assumed PDF only, 20 MB, as the live teaser upload.
10. **deferrable** — The objective-change check is assumed to apply to both admin and biz user, and only on the admin cue card (not the seller's own onboarding/profile objective).
11. **deferrable** — "Only the open-to-all setting changes": the secondary objective is not editable in the UI today; assumed untestable (manual/not applicable).

## Answers
Answered by the user on 2026-09-28. Questions 4 and 5 were not answered; the user said to assume them.

1. **Answered:** only a **completed** individual seller call counts, the same as the live rule. A scheduled call that hasn't happened yet, a deal call with buyers, or a cancelled call does not meet the requirement.
2. **Answered:** when requirements are missing, one message lists each missing item as "<item> is missing", for example "MIS is missing, Investment teaser is missing". (The user wrote "Acquisition is missing"; read here as the acquisition document, the investment teaser.) *Interpretation:* the same combined format applies to acquisition and fundraising sellers. Tests check that each missing item is named in the one message ("<item> is missing", ignoring case) and don't check the exact punctuation or order.
3. **Answered:** Yes stays clickable. Clicking **Yes** when requirements are missing shows the message. The chips are not disabled, so the Figma "Pending requirements" and disabled-Confirm state is not what ships. The check also runs again at submit (PRD section 3).
4. *Assumption (follows the PRD, "stays star; no check"):* a seller starred before this release who fails the new rules can still save other additional details, such as Growth, while Star stays Yes. Only switching Star from No to Yes runs the check. Tests expect that save to go through.
5. *Assumption:* the objective-change check sits inside the "Edit Company's Objective" modal on the admin cue card, below the Primary Objective dropdown and above Confirm. The message says the seller is a star seller and names the needed document (pitch deck or investment teaser), with the upload option right below it. Tests check that the message mentions "star" and names the document (ignoring case), not the exact wording.
6–11. The assumptions stated above stand.

## 8. Gaps and risks
- **Figma mostly unread.** The Figma MCP hit its Starter-plan call limit after one screenshot (44664:47911, admin funding modal). Biz-user frames, cue card edit frames and the objective-change frames were not seen. Re-run a Figma read or share exports before test cases are finalised.
- **Figma vs PRD vs live:** disabled chips (Figma) vs block-on-click (live/PRD) (Q3); "A verified document" vs "A qualifying document" (Q8); Figma shows a green tick next to "0 of 3 added on the cue card", which looks like a design error; "Back to cue card" not in PRD.
- **Seller call definition** (Q1) conflicts with live copy and code (completed only).
- **Legacy-star save lock** (Q4): the live save-time check would block any edit of a legacy star seller who fails the new rules, contradicting "no re-check".
- **No biz user session.** STATE_BY_ROLE has buyer/seller/admin only; every biz-user requirement (SSF-03..08, 29, 34) needs a userType 4 login saved.
- **Test data scarcity and consumption:** no star funding sellers on QA; pre-release star sellers are a finite, unrecreatable resource; many cases need specific document/call combinations and cleanup.
- **Multi-session edge cases** (SSF-16, SSF-30) need two concurrent sessions and precise timing; likely flaky, consider manual.
- Pitch deck upload today is in the Data Room, not on the cue card rail; the objective-change upload option is a new upload surface for the pitch deck.
