# Data Room Document Request — PRD Analysis

- PRD: `docs/prd/data-room-document-request.md`
- Figma: `RWMCvpU1gf3ydyJxTyQwsA`, section `43762:141750` "Data_Room_Document_Request"
- Purpose: tests (hand-off to test-case-writer)
- Analysed: 2026-09-21, branch `ui-automation-testing`
- **Checkpoint status: `READY`**. The user answered the blocking questions on 2026-09-21 and accepted the deferrable assumptions (see A.6 and A.7).
- **Test marker:** requirements marked **`not_implemented_yet`** are in scope but not built yet. Write them as expected-fail tests (`xfail`, strict), so they start passing, and get flagged, once the feature ships.

---

# Part A — Requirements analysis

## A.1 Summary

When a buyer expresses interest, they can pick documents from the existing document-type list, plus an optional note. This creates one deal note. That note is shown in the seller's express-interest email, in the seller's Accept modal on the deals tab, on the buyer's cue card and deals tab, and in Admin → deal → Data Room. The existing daily AI summary and pending-action reminder read from it. The request is locked once the modal closes. Biz users acting for a buyer skip the step. Fulfilment happens when a document of a requested type is uploaded, whoever uploads it.

**Current state:** mostly built on the frontend for buyer capture, the buyer cue card and the seller Accept modal. **Not built:** the admin Data Room view and the buyer deals-tab status. The email, reminder, AI summary, fulfilment marking and locking are backend-owned, and the frontend can't show whether they work.

## A.2 Sources reviewed

| Source | What it says | Status |
|---|---|---|
| PRD `docs/prd/data-room-document-request.md` | Problem, flows per role, logic rules, 8 doc types in 3 categories, edge cases, metrics | Read in full |
| Figma section "Buyer Profile" `43766:148127` | Cue card before and after the request (`43762:141751`, `43762:142649` with "You flagged for the intro call"). Express Interest modal in 3 states (`43762:147112`, `43762:146883`, `43762:146825`). Confirmation step with doc chips: empty (`43762:147640`, CTA "Close") and 3 selected (`43762:147749`, CTA "Send request (3)") | Read. Copy came from metadata; one screenshot (`43762:147112`) |
| Figma "Seller Email" `43766:148128` | Email frame `43766:148083`: "The buyer would like to discuss: Pitch Deck, MIS, Cap Table" plus per-doc status "Pitch Deck — already uploaded / MIS — needs upload / Cap Table — already uploaded" | Read (metadata copy) |
| Figma "Seller profile aceptance" `43782:149253` | Interest Received table `43767:148744`. Accept modal `44585:103166` with section "Request documents from the investor", rows "Pitch deck *", "Audited financials", "Cap table" | Read (metadata copy) |
| Figma "Meeting notes" `43790:150553` | Admin deal page, Data Room tab, card "Topics for the intro call" with chips "Pitchdeck", "Cap Table and Board Profile", "Registration & Licenses" under "Company" | Read (metadata copy) |
| Code (`src/`) | See A.3 | Grounded |
| Existing suite `automation/` | Tests and page objects already exist for this PRD (`automation/constants.py` mirrors the UI copy) | Skimmed |

**Blocked or partial inputs**
- **Figma MCP rate limit (Starter plan).** It stopped working after the first screenshot. I couldn't take screenshots or run `get_design_context` on the other frames. Copy comes from text-layer names in `get_metadata`. Chip labels inside `_Badge base` instances in the confirmation frames (`43762:147749`) and cue card (`43762:142649`) show as the placeholder "Text", so **Figma's buyer chip labels and their order are unverified**.
- There are no Jira or Google Docs links.

## A.3 Affected modules and files

| Area | File | Role |
|---|---|---|
| Buyer: express interest modal | `src/Component/NewCueCard/SlotSchedulerModal/index.js` | Step 1 (slots and note). Sets `isSuccess` and renders `SuccessView` (`:619-640`) |
| Buyer: doc request step | `src/Component/NewCueCard/SlotSchedulerModal/SuccessView.js` | Options (`:27-36`), toggle (`:70`), submit to `deal/capture/interest/update` (`:83-121`), CTAs (`:221-296`) |
| Buyer: cue card | `src/Component/NewCueCard/CuecardDefaultSection/components/RequestedDocuments.js`, rendered from `CuecardDefaultSection/index.js:372` (mobile) and `:451` (desktop) | "You flagged for the intro call" card |
| Buyer: gating | `src/Component/NewCueCard/CuecardDefaultSection/index.js:99` (`showCTAs` requires `isBuyerUser()`) | Stops biz and admin users reaching Express Interest |
| Seller: deals tab | `src/Container/SellerDealsAndInvestors/` (route `/deals/:companyId?`, `SHOW_SELLER_DASHBOARD_REVAMP=true`, `src/RoutesStructure/index.js:74`) | `SellerDealsAction.js:30,35` Accept CTA |
| Seller: Accept modal | `components/AcceptInterestModal.js`, `components/IntroductionSetupModal.js`, `components/RequestedDocumentRow.js`, `hooks/useIntroductionSetup.js` | Requested rows, upload/attach, accept call |
| Seller: dashboard / data room (not in PRD) | `src/Container/SellerDashboard/data/flaggedTopics.js`, `hooks/useFlaggedTopics.js`, `src/Container/SellerDataRoom/index.js:54` (section commented out) | "Flagged topics", a derived view |
| Admin: deal page | `src/Container/DealNotesContainer/` (route `/admin/deal-notes/:uid`, `src/Routes/AdminRoutes.js:238`), `DealDataRoom/index.js` | Data Room tab. **No request view** |
| Labels | `src/Container/DataRoom/dataRoomModel.js:101-110` (`DATAROOM_KEY_LABEL_MAP`), `src/constants/keyVariableConstants.js` | Doc type keys and labels |
| Endpoints | `src/config/endpoint.js:104-105, 154-162, 209-217` | See B.4 |

## A.4 Before / after / delta

| Aspect | Before (repo evidence / PRD) | After (PRD + Figma) | Delta / current code |
|---|---|---|---|
| Buyer asks for docs | Only possible once the deal reached intro pending (PRD §1) | Picks doc types plus an optional note at express interest (and intro pending) | Built as step 2 of express interest (`SuccessView.js:171-198`). No buyer entry point at intro pending |
| Doc options | n/a | 8 types in 3 categories (PRD §8) | 4 types in a flat list. 4 are commented out (`SuccessView.js:27-36`) |
| Storage | n/a | One deal note with the types and the note | FE sends `requestedDocTypes` plus `interactionNotes` in one call (`SuccessView.js:89-94`). Note creation is backend |
| Lock | n/a | No edits after the modal closes | No re-entry UI on the frontend. Backend enforcement unknown |
| Seller email | Existing EI email | Adds requested types and note (Figma adds per-doc upload status) | Backend. Not testable in the UI (email tests excluded) |
| Seller Accept modal | Deck share plus slot | Shows the request. Seller can upload or attach per type | Built (`IntroductionSetupModal.js:260-293`). Pitch-deck row is always there and mandatory |
| Buyer cue card | n/a | Requested docs plus pending/fulfilled | Built. Status shown by icon only (`RequestedDocuments.js:46`) |
| Buyer deals tab | n/a | Requested docs plus status | **Not built** (no references in `src/Container/BuyersDealsContainer`) |
| Admin Data Room | Shared docs only (`DealDataRoom/index.js`) | "Topics for the intro call" card | **Not built** |
| AI summary / reminder | Existing daily summary and pending-action reminder | Read the note and report fulfilled vs open | Backend. Manual testing only |
| Biz user for buyer | n/a | Modal skipped | Holds by construction: Express Interest CTA is buyer-only (`CuecardDefaultSection/index.js:99`) |

## A.5 Missing points worth flagging

- **Status wording:** PRD says "pending / fulfilled". The cue card only switches icons (document icon vs green check) and has no text or `aria-label`. Screen readers and tests can't tell the states apart without checking the SVG.
- **Empty state (seller):** the requested section always renders because the pitch-deck row is always added (`IntroductionSetupModal.js:94-97`). "Only populated when a request exists" (PRD §6) is not literally true in the Accept modal.
- **Error state (buyer):** a failed `deal/capture/interest/update` shows the backend message or "Something went wrong" and leaves the step open (`SuccessView.js:106-119`). The interest itself was already captured in step 1.
- **Lock enforcement:** the frontend doesn't expose a way to re-request, but nothing in the frontend proves the backend rejects a second `requestedDocTypes`.
- **Analytics:** there's no PostHog event for "document request sent" on the buyer side. The seller side has attach, remove, upload and dismiss events (`IntroductionSetupModal.js:7-13`). PRD §10 metrics need a request-raised signal.
- **Admin visibility:** the admin surface is missing entirely (A.4).

## A.6 Open questions

### Decisions (2026-09-21)

| # | Question | Decision | Effect on tests |
|---|---|---|---|
| 1 | Trigger at introduction_pending | **Both** express interest and introduction_pending are buyer entry points | DR-01…DR-20 cover express interest (built). DR-22 (intro pending) is in scope and `not_implemented_yet`. There's no Figma or code for the intro-pending buyer screen, so DR-22's test asserts the outcome (modal opens and a request is captured), not specific copy |
| 2 | Document options | Test the **4 built** options (Pitchdeck, MIS, Cap Table, Audited Financials). The other 4 PRD types and the category grouping are `not_implemented_yet` | DR-53 (built 4, yes). DR-03 (other 4) and DR-04 (grouping) are `not_implemented_yet` |
| 3 | Admin Data Room view | In scope, `not_implemented_yet` until it ships | DR-46, DR-47 are `not_implemented_yet` |
| 4 | Buyer deals tab | In scope, `not_implemented_yet` until it ships | DR-21 is `not_implemented_yet` |
| 5–11 | Deferrable | **Assumptions accepted** as written below | Treated as decided. Q5 → assert code copy. Q6 → deck row mandatory. Q7 → DR-16 marked unverified. Q8 → manual. Q9 → "Cap Table". Q10 → out of scope. Q11 → icon only |

The original questions are kept below for traceability.

### Blocking (resolved, see Decisions)

1. **Trigger at introduction_pending.** PRD §5/§6 say the buyer can raise the request at introduction_pending. In the code, introduction_pending is set by the *seller* accepting (`useIntroductionSetup.js:143`), and the buyer takes no action at that stage. Is express interest the only buyer entry point, or should a buyer screen at intro pending open the modal?
2. **Document options.** PRD §8 lists 8 types in 3 categories (Company / Financial / Others). The buyer step offers 4 in a flat list (Pitchdeck, MIS, Cap Table, Audited Financials), with Registrations, ITR, GST Filing and Credit rating commented out (`SuccessView.js:27-36`). Which set, and does it need grouping, for this release?
3. **Admin Data Room view.** Figma `43790:150553` shows "Topics for the intro call" on Admin → deal → Data Room, but `src/Container/DealNotesContainer/DealDataRoom/index.js` has no request view. Is it in scope for this release? Should its tests be written as expected-fail, or deferred?
4. **Buyer deals tab.** PRD §5 says the buyer's deals tab shows requested docs and pending/fulfilled status. This isn't built, and only the cue card shows the request. Is it in scope for this release?

### Deferrable (assumptions accepted by the user)

5. Seller modal copy: Figma says "Request documents from the investor", "…revealed to this buyer…", "Pitch deck *", "Audited financials", "Cap table". Code says "The investor would like to discuss", "…revealed to {buyer label | 'this investor'}…", "Pitch Deck", "Audited Financials", "Cap Table". *[Assume code copy is truth; log a design-parity gap.]*
6. The pitch-deck row is always present and mandatory in the Accept modal, even when not requested (`IntroductionSetupModal.js:94-97, 202-209`). *[Assume intended, carried over from the older accept rule.]*
7. Lock: does the backend reject or ignore a second `deal/capture/interest/update` with `requestedDocTypes`? *[Assume yes; API test marks it as unverified.]*
8. Email per-doc upload status line (Figma only, not in PRD). *[Assume nice-to-have; manual check.]*
9. Cap Table label: "Cap Table" (`dataRoomModel.js:103`) vs "Cap Table and Board Profile" (PRD §8, Figma admin, `SellerShareDocsModal/index.js:38`). *[Assume "Cap Table" in buyer and seller UIs.]*
10. Seller dashboard "flagged topics" (`flaggedTopics.js`, `useSellerDashboardHome.js:42`) isn't in the PRD. Should it be tested? *[Assume out of scope.]*
11. Should the cue card show a status text ("Pending" / "Shared") or is the icon enough? *[Assume icon.]*

## A.7 Context checkpoint

- **Status: `READY`** (approved 2026-09-21). All blocking questions are answered and the deferrable assumptions are accepted.
- **Live tests (built behaviour):** buyer capture at express interest (DR-01…DR-20, DR-53), biz gating (DR-23), seller Accept modal (DR-28…DR-42), fulfilment and API checks (DR-10, 11, 13, 16, 24, 43–45, 48).
- **`not_implemented_yet` (expected-fail) tests:** DR-03 (the other 4 PRD doc types), DR-04 (category grouping), DR-21 (buyer deals tab status), DR-22 (buyer request at introduction_pending), DR-46 and DR-47 (admin Data Room "Topics for the intro call" and its gating).
- **Manual:** DR-25…DR-27 (email), DR-49…DR-52 (reminder, AI summary, on_hold, metrics).
- **Still open, not blocking:** DR-22 has no design. When the intro-pending buyer screen is designed, add its copy to B.3 and tighten DR-22's test.

## A.8 Risks

- **Test data is one-shot:** express interest is one-time per buyer/company, and the seller login only exists after it (see B.5). A bad run uses up a company.
- **Backend-only behaviour:** email, reminder, AI summary, fulfilment and lock are all backend. The frontend only reflects `requestedDocuments[].fulfilled`. Most "logic" rows can only be checked through the API or by hand.
- **Payload shape differs by endpoint:** `deal/query` returns `requestedDocuments` as plain strings (seller modal uses `.includes`, `useIntroductionSetup.js:167`, `IntroductionSetupModal.js:95`). The cue card expects `{docType, fulfilled}` objects (`RequestedDocuments.js:21-29`). If the backend switches deal/query to objects, the seller modal breaks silently: every row becomes `[object Object]` and the pitch deck is duplicated. `flaggedTopics.js:36-41` handles both shapes.
- **Design parity:** seller modal copy differs from Figma (Q5). Tests should assert code copy.
- **Accept with multiple docs:** only one `docUid` goes with `deal/seller`. The rest go via a second `document/deal/share` call (`useIntroductionSetup.js:109-156`). If the second call fails, the deal is accepted with some documents unshared.

## A.9 Draft acceptance criteria (checklist)

- [ ] After a successful express interest, the buyer sees the doc-request section with only doc types from the existing list.
- [ ] Selecting N docs changes the CTA to "Send request (N)". Sending shows "Document request sent to founder" and closes the modal.
- [ ] Closing with nothing selected makes no update call and creates no request.
- [ ] After closing, the buyer has no way to add documents.
- [ ] The cue card shows "You flagged for the intro call" with the requested docs, pitch deck first, and a check icon on fulfilled ones.
- [ ] Biz and admin users never see the doc-request step.
- [ ] The seller's Accept modal lists each requested doc with its data-room status and lets them upload or attach. The seller can accept without fulfilling non-deck requests.
- [ ] Uploading a doc of a requested type marks it fulfilled for the buyer (cue card check icon).
- [ ] The 4 built options are offered: Pitchdeck, MIS, Cap Table, Audited Financials.
- [ ] *(`not_implemented_yet`)* The other 4 PRD types (Registration & Licenses, ITR, GST Filing, Credit rating) are offered, grouped under Company / Financial / Others.
- [ ] *(`not_implemented_yet`)* The buyer can raise the request at introduction_pending.
- [ ] *(`not_implemented_yet`)* The admin Data Room shows "Topics for the intro call" only when a request exists.
- [ ] *(`not_implemented_yet`)* The buyer deals tab shows requested docs with status.
- [ ] *(manual)* The email includes requested types and note only when a request exists. The AI summary reports fulfilled vs pending day over day.

---

# Part B — QA hand-off (for test-case-writer)

## B.1 Requirements table

Type: flow · rule · gating · lock · edge-case · copy · non-functional. Testable via: UI · API · UI+API · manual.

| ID | Requirement | Source | Role | Type | Testable via | Implemented? |
|---|---|---|---|---|---|---|
| DR-01 | After express interest succeeds, the buyer sees a doc-request section "What would you like to discuss in your intro call?" in the confirmation step. | PRD §5 Buyer; Figma `43762:147640` | Buyer | flow | UI | yes: `SuccessView.js:171-176`, `SlotSchedulerModal/index.js:268,619` |
| DR-02 | Request options come only from the existing doc-type list. There's no free-text document input. | PRD §6 Document options | Buyer | rule | UI | yes: `SuccessView.js:27-36,179-196` |
| DR-03 | The other 4 PRD §8 types (Registration & Licenses, ITR, GST Filing, Credit rating) are offered. | PRD §8 | Buyer | rule | UI | no, **`not_implemented_yet`**: commented out, `SuccessView.js:32-35` |
| DR-04 | Options are grouped under Company Information / Financial Information / Others. | PRD §8 | Buyer | copy | UI | no, **`not_implemented_yet`**: flat list, `SuccessView.js:178` |
| DR-05 | Clicking a doc chip selects it (check shown). Clicking again deselects it. | Figma `43762:147749` | Buyer | flow | UI | yes: `SuccessView.js:70-74,188-192` |
| DR-06 | With N ≥ 1 selected, the primary CTA reads "Send request (N)". | Figma `43762:147749` | Buyer | copy | UI | yes: `SuccessView.js:292` |
| DR-07 | With nothing selected and no edits, only a "Close" CTA is shown. | Figma `43762:147640` | Buyer | copy | UI | yes: `SuccessView.js:222-242` |
| DR-08 | The buyer can add or edit an optional note (max 400 chars) with the request when the note wasn't mandatory in step 1. | PRD §5, §6 | Buyer | flow | UI | yes: `SuccessView.js:154-168` |
| DR-09 | When the note was mandatory in step 1, it shows read-only under "Note shared with the founder:". | Figma `43762:147749` | Buyer | rule | UI | yes: `SuccessView.js:144-152` |
| DR-10 | "Send request" posts `companyId`, `interactionNotes`, `teamMembers`, `requestedDocTypes[]` to `deal/capture/interest/update`. | PRD §6 Storage | Buyer | flow | UI+API | yes: `SuccessView.js:88-95` |
| DR-11 | `requestedDocTypes` is left out of the payload when nothing is selected. | PRD §9 row 3 | Buyer | edge-case | UI+API | yes: `SuccessView.js:93` |
| DR-12 | On success, the snackbar shows "Document request sent to founder" (unless the backend sends a message) and the modal closes. | — (code) | Buyer | copy | UI | yes: `SuccessView.js:98-105` |
| DR-13 | Closing with nothing selected creates no request: no update call, no cue card section. | PRD §9 row 3 | Buyer | edge-case | UI+API | yes: `SuccessView.js:239` (Close → `handleClose`, no API) |
| DR-14 | "Cancel" clears the selected docs and reverts the note and team edits. | — (code) | Buyer | flow | UI | yes: `SuccessView.js:76-81` |
| DR-15 | After the modal closes, the buyer has no UI to add documents to the request. | PRD §6 One-time capture; §9 row 4 | Buyer | lock | UI | yes (FE): cue card card is read-only, `RequestedDocuments.js:20-55`; the `showExpressInterest` param is removed, `SlotSchedulerModal/index.js:265-267` |
| DR-16 | A second update call with `requestedDocTypes` for the same deal is rejected or ignored by the backend. | PRD §6 One-time capture | Buyer | lock | API | unknown: backend, no FE evidence |
| DR-17 | Once a request exists, the buyer's cue card shows "You flagged for the intro call" / "A reminder of what you asked to cover." with one chip per requested doc. | PRD §5; Figma `43762:142649` | Buyer | flow | UI | yes: `RequestedDocuments.js:32-52`; `CuecardDefaultSection/index.js:372,451` |
| DR-18 | The cue card has no requested-docs card when there's no request. | PRD §6 Visibility gating | Buyer | gating | UI | yes: `RequestedDocuments.js:23-25` |
| DR-19 | The pitch deck chip is listed first on the cue card. Other chips keep request order. | — (code) | Buyer | rule | UI | yes: `RequestedDocuments.js:27-30` |
| DR-20 | A fulfilled requested doc shows a green check icon. A pending one shows a document icon. | PRD §5 status | Buyer | rule | UI+API | partial: icon only, no text, `RequestedDocuments.js:46` |
| DR-21 | The buyer's deals tab shows requested docs and their pending/fulfilled status. | PRD §5 Buyer | Buyer | flow | UI | no, **`not_implemented_yet`**: nothing in `src/Container/BuyersDealsContainer` |
| DR-22 | The buyer can raise the request at introduction_pending (decision Q1: both entry points). | PRD §5, §6 Trigger | Buyer | flow | UI | no, **`not_implemented_yet`**: no buyer action at intro pending; status set by seller accept, `useIntroductionSetup.js:143` |
| DR-23 | A biz or admin user viewing a cue card never gets the Express Interest step, so no doc-request modal appears. | PRD §5 Biz, §7 Story 5, §9 row 2 | Biz | gating | UI | yes: `CuecardDefaultSection/index.js:99` (`isBuyerUser()`) |
| DR-24 | A biz-user-performed EI/intro transition captures no request. | PRD §6 Trigger, §9 row 2 | Biz | gating | API | unknown: backend |
| DR-25 | The seller's EI/intro-pending email lists the requested doc types and the buyer's note when a request exists. | PRD §5 Seller; Figma `43766:148083` | Seller | flow | manual | backend |
| DR-26 | The seller email has no requested-docs section when there's no request. | PRD §6 Visibility gating | Seller | gating | manual | backend |
| DR-27 | The seller email shows per-doc status ("already uploaded" / "needs upload"). | Figma `43766:148083` only | Seller | copy | manual | backend, not in PRD (Q8) |
| DR-28 | On `/deals` → Interest Received, clicking Accept opens "Accept investor interest?" with a requested-docs section "The investor would like to discuss". | PRD §5 Seller, Story 3; Figma `44585:103166` | Seller | flow | UI | yes: `SellerDealsAction.js:30,35,40`; `IntroductionSetupModal.js:236,260-266` |
| DR-29 | The Accept modal has one row per requested doc type, labelled from `DATAROOM_KEY_LABEL_MAP` (deck as "Pitch Deck"). | Figma `44585:103166` | Seller | rule | UI | yes: `IntroductionSetupModal.js:98-107` |
| DR-30 | The Pitch Deck row is always present, first and marked required (*), even when not requested. | Figma "Pitch deck *" | Seller | rule | UI | yes: `IntroductionSetupModal.js:94-97,277`; `RequestedDocumentRow.js:53` |
| DR-31 | With no request, the section shows only the Pitch Deck row. | PRD §6 Visibility gating | Seller | gating | UI | yes (differs from PRD wording): `IntroductionSetupModal.js:94-97` |
| DR-32 | Each row shows status: attached file name, "N file(s) in your data room", or "Not uploaded yet". | Figma `44585:103166` | Seller | copy | UI | yes: `RequestedDocumentRow.js:42-46` |
| DR-33 | A row with no existing files shows "Upload". Uploading sends that row's `docType` and auto-attaches the file. | PRD §5 Seller | Seller | flow | UI+API | yes: `RequestedDocumentRow.js:105-117`; `useIntroductionSetup.js:78-104`; `IntroductionSetupModal.js:164-169` |
| DR-34 | A row with existing files shows "Attach ▾" listing files of that type. Once picked, it shows "Attached" plus a remove (×) button. | Figma `44585:103166` | Seller | flow | UI | yes: `RequestedDocumentRow.js:58-103` |
| DR-35 | The header counter shows attached/total rows (e.g. "1/3"). | Figma | Seller | copy | UI | yes: `IntroductionSetupModal.js:267-269` |
| DR-36 | The latest pitch deck on file is pre-attached once. | — (code) | Seller | rule | UI | yes: `IntroductionSetupModal.js:128-139` |
| DR-37 | Accepting without a deck attached shows "Pitch Deck is mandatory. Please share/upload a Pitch Deck to continue." | — (code) | Seller | edge-case | UI | yes: `IntroductionSetupModal.js:202-209` |
| DR-38 | The seller can accept without attaching non-deck requested docs (the request doesn't block). | PRD §6 Not mandatory, §9 row 1 | Seller | rule | UI+API | yes: only the deck check, `IntroductionSetupModal.js:189-224` |
| DR-39 | When slots exist, accepting without choosing one shows "Please choose a timeslot to continue." | Figma "Choose a timeslot…" | Seller | edge-case | UI | yes: `IntroductionSetupModal.js:211-214,328` |
| DR-40 | Accept posts `deal/seller` {buyerId, companyId, dealStatus: introduction_pending, docUid (deck), slotId}, then `document/deal/share` {dealIds, uids} for the other attached docs. | — (code) | Seller | flow | UI+API | yes: `useIntroductionSetup.js:106-162` |
| DR-41 | The buyer's note shows as "Investor's message:" when present, and is hidden when empty or "--". | PRD §5 Seller | Seller | rule | UI | yes: `IntroductionSetupModal.js:253-258`; `utils.js:40-45` |
| DR-42 | After accepting, the seller can upload and share requested docs through the existing flow. | PRD §5 Seller | Seller | flow | UI | yes: existing manage-docs flow, `hooks/useSharedDocs.js:96,171` |
| DR-43 | Uploading a doc of a requested type marks that item fulfilled, whoever uploads it. | PRD §6 Fulfillment | All | rule | UI+API | partial: backend sets `fulfilled`. FE shows it, `RequestedDocuments.js:46` |
| DR-44 | Uploading a doc of a non-requested type doesn't change the request's status. | PRD §9 row 5 | Seller | edge-case | UI+API | backend |
| DR-45 | The request stays open until all requested types are uploaded (partial = open). | PRD §9 row 6 | All | rule | API | backend |
| DR-46 | Admin → `/admin/deal-notes/:uid` → Data Room shows "Topics for the intro call" with the requested docs. | PRD §5 Buyer owner; Figma `43790:150553` | Admin/Biz | flow | UI | no, **`not_implemented_yet`**: `DealNotesContainer/DealDataRoom/index.js` has none |
| DR-47 | The admin Data Room has no topics card when there's no request. | PRD §6 Visibility gating | Admin/Biz | gating | UI | no, **`not_implemented_yet`**: depends on DR-46 (today it passes trivially because the card never renders, so assert it together with DR-46) |
| DR-48 | One deal note holds the requested types plus the note text. | PRD §6 Storage | Admin/Biz | rule | API | backend |
| DR-49 | The standard pending-action reminder attaches to the request note. | PRD §6 Reminder | System | non-functional | manual | backend |
| DR-50 | The daily AI summary reports newly fulfilled and still-pending items, including partial closure. | PRD §5, §6, §9 row 6 | Admin/Biz | non-functional | manual | backend |
| DR-51 | An on_hold deal pauses and resumes reminders as it does today. | PRD §9 row 7 | System | edge-case | manual | backend |
| DR-52 | Success metrics (§10) can be measured. | PRD §10 | PM | non-functional | manual | partial: no buyer "request sent" event |
| DR-53 | The confirmation step offers exactly the 4 built options, in order: Pitchdeck, MIS, Cap Table, Audited Financials (decision Q2). | PRD §8; Figma `43762:147749` (4 chips) | Buyer | rule | UI | yes: `SuccessView.js:27-31,179-196` |

## B.2 Acceptance criteria (Given / When / Then)

- **DR-01** Given a verified buyer on a company cue card with no deal, when they submit Express Interest with one slot and it succeeds, then the modal switches to "Interest Shared with Founder" and shows "What would you like to discuss in your intro call?" / "Optional. The founder will see this and can prepare."
- **DR-02** Given the confirmation step, then every chip label is in `DATAROOM_KEY_LABEL_MAP` and there's no text input for document names.
- **DR-03** *(`not_implemented_yet`)* Given the confirmation step, then chips "Registration & Licenses", "ITR", "GST Filing" and "Credit rating" are also shown.
- **DR-04** *(`not_implemented_yet`)* Given the confirmation step, then chips are grouped: "Company Information" (Pitchdeck, Cap Table and Board Profile, Registration & Licenses), "Financial Information" (Audited Financials, MIS, ITR, GST Filing), "Others" (Credit rating).
- **DR-05** Given no chips selected, when the buyer clicks "MIS", then its checkbox shows a check. When they click "MIS" again, the check disappears.
- **DR-06** Given 3 chips selected, then the primary CTA text is exactly "Send request (3)", with "Cancel" beside it.
- **DR-07** Given the confirmation step with nothing changed, then only "Close" is shown (no Cancel or Submit).
- **DR-08** Given the note wasn't mandatory, when the buyer types a note in the confirmation step, then the textarea accepts at most 400 characters and the CTA reads "Submit" (0 docs) or "Send request (N)".
- **DR-09** Given the buyer expressed interest outside preferences (mandatory note), then the confirmation step shows the note as read-only text under "Note shared with the founder:".
- **DR-10** Given 2 chips selected, when the buyer clicks "Send request (2)", then one POST to `deal/capture/interest/update` is sent with `requestedDocTypes` = the 2 keys in selection order, plus `companyId`, `interactionNotes` and `teamMembers`.
- **DR-11** Given no chips selected but the note was edited, when the buyer clicks "Submit", then the request body has no `requestedDocTypes` key.
- **DR-12** Given DR-10 returns status success, then a success snackbar appears ("Document request sent to founder" or the backend message) and the modal closes.
- **DR-13** Given nothing selected and nothing edited, when the buyer clicks "Close", then no `deal/capture/interest/update` request is sent, and after reload the cue card has no "You flagged for the intro call" card.
- **DR-14** Given 2 chips selected, when the buyer clicks "Cancel", then all chips are cleared and the CTA returns to "Close".
- **DR-15** Given the buyer sent a request and the modal closed, when they reload the cue card, then the card shows "Expressed Interest" state and no control to add or edit requested docs exists.
- **DR-16** Given a deal with a request, when `deal/capture/interest/update` is called again with other `requestedDocTypes`, then the stored request is unchanged (cue card still shows the original set). *(Mark unverified pending Q7.)*
- **DR-17** Given a buyer who requested Pitchdeck and MIS, when they open the company cue card (desktop), then "You flagged for the intro call" and "A reminder of what you asked to cover." are visible with chips "Pitchdeck" and "MIS".
- **DR-18** Given a buyer who expressed interest without requesting docs, when they open the cue card, then "You flagged for the intro call" isn't present.
- **DR-19** Given a request of [MIS, Pitchdeck], when the cue card renders, then "Pitchdeck" is the first chip.
- **DR-20** Given one requested type has been uploaded by the seller, when the buyer reloads the cue card, then that chip shows the green check icon and the others show the document icon.
- **DR-21** *(`not_implemented_yet`)* Given a buyer with a request, when they open their deals tab, then the deal row or detail shows the requested docs, each marked pending or fulfilled.
- **DR-22** *(`not_implemented_yet`)* Given a buyer with a deal at introduction_pending and no request yet, when they open that deal or cue card, then a doc-request step is offered, and sending it stores `requestedDocuments` on the deal. *(No design yet: assert the outcome, not the copy.)*
- **DR-23** Given an admin or biz user opens a company cue card, then no "Express Interest" CTA or doc-request step is available to them.
- **DR-24** Given a biz user moves a deal to express_interest or introduction_pending for a buyer through admin tools, then `deal/query` for that deal returns no `requestedDocuments`.
- **DR-25** *(manual)* Given a request of Pitchdeck, MIS, Cap Table with a note, when the seller's EI email arrives, then it lists those types and the note.
- **DR-26** *(manual)* Given no request, then the EI email has no requested-docs line.
- **DR-27** *(manual)* Given a request, then each type in the email shows "already uploaded" or "needs upload".
- **DR-28** Given a seller on `/deals` → "Interest Received" with a pending interest, when they click "Accept", then a modal titled "Accept investor interest?" opens with a "The investor would like to discuss" section.
- **DR-29** Given a request of [MIS, Cap Table], then rows labelled "Pitch Deck", "MIS" and "Cap Table" are shown in that order.
- **DR-30** Given a request of [MIS], then the first row is "Pitch Deck" with a red "*". Given a request of [Pitchdeck, MIS], there's exactly one Pitch Deck row.
- **DR-31** Given an interest with no request, then the section shows only the "Pitch Deck *" row and the counter reads "x/1".
- **DR-32** Given a requested type with no files on file, then its row shows "Not uploaded yet". With 2 files it shows "2 files in your data room". Once one is attached, it shows the file name.
- **DR-33** Given a row showing "Not uploaded yet", when the seller uploads a PDF via "Upload", then the button shows "Uploading…", a POST to `document/user/upload` carries `docType` = that row's type, and afterwards the row shows the file name with "Attached".
- **DR-34** Given a row with existing files, when the seller clicks "Attach" and picks a file, then the row shows "Attached" and a "Remove attached {label}" button. Clicking it returns the row to "Attach".
- **DR-35** Given 3 rows with 1 attached, then the counter reads "1/3".
- **DR-36** Given the seller has two pitch decks, when the modal opens, then the most recent one is pre-attached on the Pitch Deck row.
- **DR-37** Given no pitch deck attached, when the seller clicks "Accept", then "Pitch Deck is mandatory. Please share a Pitch Deck to continue." (deck on file) or "…Please upload a Pitch Deck to continue." (none on file) appears and no `deal/seller` call is made.
- **DR-38** Given a deck attached and MIS requested but not attached, when the seller clicks "Accept" (with slot if required), then `deal/seller` is sent and the deal moves to Active Deals.
- **DR-39** Given the buyer proposed slots, when the seller clicks "Accept" without picking one, then "Please choose a timeslot to continue." appears.
- **DR-40** Given deck plus MIS attached and a slot selected, when the seller clicks "Accept", then `deal/seller` is sent with `dealStatus: "introduction_pending"`, `docUid` = the deck uid and `slotId`, followed by `document/deal/share` with `uids` = [MIS uid].
- **DR-41** Given the buyer left note "X", then the modal shows "Investor's message:" followed by "X". Given no note, that block is absent.
- **DR-42** Given an accepted deal, when the seller shares a requested doc via Active Deals' manage-docs flow, then the share succeeds.
- **DR-43** Given MIS requested, when anyone uploads an MIS for that company, then the buyer's cue card MIS chip shows the check icon (`requestedDocuments[].fulfilled = true`).
- **DR-44** Given MIS requested, when the seller uploads a GST Filing, then MIS stays unfulfilled.
- **DR-45** Given [Pitchdeck, MIS] requested and only Pitchdeck uploaded, then the request stays open (MIS `fulfilled: false`).
- **DR-46** *(`not_implemented_yet`)* Given a deal with request [Pitchdeck, Cap Table], when an admin opens `/admin/deal-notes/{dealId}` → "Data Room", then "Topics for the intro call" shows those chips.
- **DR-47** *(`not_implemented_yet`)* Given a deal with no request, then the admin Data Room tab has no "Topics for the intro call", while a deal with a request does (paired with DR-46).
- **DR-48** Given a request with a note, when an admin opens the deal's Notes tab or notes API, then exactly one note holds the types and note text.
- **DR-49…DR-51** *(manual)* Check the reminder, daily AI summary (day-over-day diff, partial closure) and on_hold pause/resume against QA data.
- **DR-52** *(manual)* Confirm with PM or analytics how "request raised" is measured.
- **DR-53** Given the confirmation step, then exactly 4 chips are shown, in order: "Pitchdeck", "MIS", "Cap Table", "Audited Financials".

## B.3 Screen map (Figma)

| Node | Screen | State | Visible copy (CTAs / labels / messages) | Rendered by |
|---|---|---|---|---|
| `43762:141751` | Detailed cue card | Before request | Company sections; no flagged card | `CuecardDefaultSection/index.js` |
| `43762:142649` | Detailed cue card | After request | "Express interest to download Pitchdeck.", "You flagged for the intro call", 3 chips with file icon (labels not readable) | `RequestedDocuments.js` via `CuecardDefaultSection/index.js:451` |
| `43762:147112` | Express Interest modal | Empty, note required, CTA disabled | "Express Interest in this company", "Express your interest by proposing a few time slots…", "Add preferred slots for meet (IST) *", "Add Second Slot", "You are expressing interest in a company outside your preferences; please add a note to continue.", "Add a note to send to the founder *", placeholder "Share your investment focus or key topics to help the founder prepare.", "Cancel", "Request Call" (disabled) | `SlotSchedulerModal/index.js` |
| `43762:146883` | Express Interest modal | Date selected, choosing time | Same as above plus time picker | `SlotSchedulerModal/index.js` |
| `43762:146825` | Express Interest modal | Slot selected "04/03/2026 11:00 AM - 11:30 AM" | Same copy; "Request Call" | `SlotSchedulerModal/index.js` |
| `43762:147640` | Confirmation step | No docs selected | Title (code: "Interest Shared with Founder"), "Your proposed time slots have been shared with the founder.", slots, note, "What would you like to discuss in your intro call?", "Optional. The founder will see this and can prepare.", 4 chips (unchecked), "Add team member (s)", **"Close"** | `SuccessView.js` |
| `43762:147749` | Confirmation step | 3 of 4 selected | Same, plus 3 checked chips, **"Send request (3)"** | `SuccessView.js:292` |
| `43766:148083` | Seller EI email | Request present | "Good news! An investor on Done Deal has shown interest in your company, {CompanyName}…", "Available meeting slot(s):", "The buyer would like to discuss: Pitch Deck, MIS, Cap Table", "Pitch Deck — already uploaded / MIS — needs upload / Cap Table — already uploaded" | Backend email |
| `43767:148744` | Seller deals, Interest Received | List | Tabs "Interest Received", "Active Deals"; columns "Buyer Name", "Description", "Request Recieved" [sic], "Action"; CTAs "Reject", "Accept" | `SellerDealsAndInvestors/SellerDealsTable.js`, `SellerDealsAction.js` |
| `44585:103166` | Seller Accept modal | Request of 3, deck attached | "Accept investor interest?", "Your identity will be revealed to this buyer over email.", "Investor’s message:", "Request documents from the investor", rows "Pitch deck *" → "240304 Company EL.pdf", "Audited financials" → "Not uploaded yet", "Cap table" → "2 files in your data room", "Choose a timeslot for the introductory call *", "Cancel", "Accept" | `IntroductionSetupModal.js`. **Code copy differs**: "The investor would like to discuss", "…revealed to {buyer} over email.", "Investor's message:", "Pitch Deck", "Audited Financials", "Cap Table" |
| `43790:150553` | Admin deal page, Data Room tab | Request present | "Deal 12345", "Deal Transition:", "Deal Members:", "Last Activity:", tabs "Meeting Notes", "Data Room"; card "Topics for the intro call", group "Company", chips "Pitchdeck", "Cap Table and Board Profile", "Registration & Licenses" | Route `/admin/deal-notes/:uid` → `DealNotesContainer/DealDataRoom`. **Card not implemented** |

## B.4 Code facts for testers

**Routes**
- Buyer: `/buyer/browse` → View Listing → cue card (the modal is global via `NewLayoutContainer/index.js:534`). The `?showExpressInterest` param opens EI and is removed on success (`SlotSchedulerModal/index.js:265`).
- Seller: `/deals/:companyId?` → `SellerDealsAndInvestors` (`RoutesStructure/index.js:74`), tab "Interest Received" (`SellerDealsTable.js:13`). Data room: `/dataroom/:uid?`.
- Admin/biz: `/admin/deals` (All Deals, `AdminRoutes.js:165`) → deal link opens `/admin/deal-notes/{id}` **in a new tab** (`<a target="_blank">`, `AdminDealsTableModel.js:890,1126,1359`). Tabs: Notes, Meeting Notes, Data Room, Activity (`dealNotesTabModel.js`). Data Room is hidden for `?noteIdType=unverified_user_deal`.

**Endpoints** (base = QA API)
| Call | Method / URL | Body |
|---|---|---|
| Express interest (step 1) | POST `deal/capture/interest` (`SELLERLISTING.updateInterestApi`) | `meetSlots, companyId, listUid, stage: 'express_interest'\|'connect_with_founder', openToAcquisition, openToFunding, actionSource, unverifiedUserDealFlow, interactionNotes, teamMembers` → `data.dealId > 0` on success |
| Doc request (step 2) | POST `deal/capture/interest/update` | `companyId, interactionNotes, teamMembers, requestedDocTypes?: string[]` |
| Seller/admin deal list | POST `deal/query?page=&size=` | filter model; rows carry `requestedDocuments: string[]`, `investorNote.description`, `buyerId`, `sellerId`, `id` |
| Seller docs | POST `document/query` | `{criteriaMap}` → `data.userDocMap` |
| Admin deal docs | POST `document/query` | `{criteriaMap: {dealId}}` |
| Upload | POST `document/user/upload` (multipart) | `file`, `docData = {userDocArray:[{docType, category:'company'}]}` → `data` = new uid |
| Seller accept | POST `deal/seller` | `buyerId, companyId, dealStatus:'introduction_pending', docUid, slotId` |
| Extra shares | POST `document/deal/share` | `dealIds:[dealId], uids:[...]` |
| Seller slots | POST `ENDPOINT.MEETING.sellerSlot()` | `{dealId}` → `meetingBookingRequired`, `possibleMeetingList` |

Cue card data: `buyerStore.buyerCueCardData.requestedDocuments` = `[{docType, fulfilled}]`.

**Doc keys → labels** (`keyVariableConstants.js`, `dataRoomModel.js:101-110`): `pitch_deck`→"Pitchdeck", `cap_table`→"Cap Table", `registrations_and_licenses`→"Registration & Licenses", `audited_financials`→"Audited Financials", `mis`→"MIS", `itr_filing`→"ITR", `gst_filing`→"GST Filing", `credit_rating`→"Credit rating". Buyer options in order: Pitchdeck, MIS, Cap Table, Audited Financials. In the seller modal the deck row is labelled **"Pitch Deck"**, not "Pitchdeck".

**Element types to know about**
- Buyer doc chips are `<button type="button">` with a nested span checkbox. The selected state is only visible as a `CheckIcon` (MUI SVG). There's no `aria-pressed`.
- "Add Team Member (s)" is a clickable `<div>` (`SuccessView.js:201`).
- The seller "Accept" / "Reject" CTAs in the deals table are **`<div>`s with onClick** (`SellerDealsAction.js:30,35`), not buttons.
- Accept modal slots are `<button role="radio" aria-checked>`. The close icon is `aria-label="Close"`. The remove attachment button is `aria-label="Remove attached {label}"`.
- The row "Upload" button triggers a hidden `<input type="file" class="hidden" accept=…>`, so use `set_input_files` on it.
- The Attach menu is an MUI `Menu` (portal, `role="menu"` / `menuitem`).
- The cue card fulfilled/pending state is only the SVG (green circle `#12B76A` vs purple file stroke `#7F56D9`).
- The cue card requested card shows on desktop only when `showDesktopCTAs`, and on mobile under separate conditions (`CuecardDefaultSection/index.js:138-144`).

## B.5 Role and sequencing notes

1. **The buyer acts first:** express interest (step 1) → doc request (step 2) in the same modal session. It's one-shot per buyer × company, so each run uses up a company from `/buyer/browse`.
2. **The seller login only exists after the buyer's express interest** (seller credentials are created by that action). Keep the existing `phase1` (buyer) → save seller session → `phase2` (seller) split (`automation/tests/e2e/`).
3. **The Accept action is one-time:** it moves the deal to introduction_pending and uses up the "Interest Received" row. Run all read-only Accept-modal checks (DR-28…DR-37, DR-39, DR-41) **before** a single accepting test (DR-38/40).
4. **Uploads are persistent:** uploading in the modal adds a real file to the seller's data room. This changes later "Not uploaded yet" states and fulfils the request (DR-43). Order tests so "Not uploaded yet" is asserted before any upload.
5. **Admin checks** (DR-46/47) need the deal id from phase 1 (`run_state/phase1.json`). The admin deal page opens in a new tab from the list, so go directly to `/admin/deal-notes/{id}`.
6. **Biz gating** (DR-23) needs an admin or biz session only and uses no data.
7. **Negative "no request" cases** (DR-13, DR-18, DR-26, DR-31, DR-47) need a **second** company where the buyer expressed interest and clicked Close.
8. **Emails and the AI summary** are manual, per the user's preference (no mailbox tests).

## B.6 Gaps (PRD vs Figma vs code)

| # | Gap | PRD | Figma | Code (evidence) |
|---|---|---|---|---|
| G1 | Doc options set | 8 types, 3 categories (§8) | 4 chips in confirmation (`43762:147749`) | 4 types, flat; 4 commented out (`SuccessView.js:27-36`). **Decision:** test the 4 built (DR-53); DR-03 and DR-04 are `not_implemented_yet` |
| G2 | Admin Data Room request view | Required (§5 Buyer owner) | "Topics for the intro call" (`43790:150553`) | Missing (`DealNotesContainer/DealDataRoom/index.js:11-95`). **Decision:** in scope, DR-46 and DR-47 are `not_implemented_yet` |
| G3 | Buyer deals-tab status | Required (§5 Buyer) | Not drawn | Missing (no refs in `src/Container/BuyersDealsContainer`). **Decision:** in scope, DR-21 is `not_implemented_yet` |
| G4 | Intro-pending buyer trigger | Buyer can request at intro pending (§5, §6) | Only the EI flow is drawn | Intro pending is set by the seller accepting (`useIntroductionSetup.js:143`); no buyer entry point. **Decision:** both entry points; DR-22 is `not_implemented_yet`, no design yet |
| G5 | Seller modal section title and copy | — | "Request documents from the investor", "this buyer", "Investor’s message:", "Pitch deck *", "Audited financials", "Cap table" | "The investor would like to discuss" (`IntroductionSetupModal.js:265`), "{buyer label \| this investor}" (`:251`), "Investor's message:" (`:255`), "Pitch Deck" (`:102`), map labels (`dataRoomModel.js:103,105`) |
| G6 | Visibility gating in the Accept modal | "Only populated when a request exists" (§6) | — | Section always renders with the Pitch Deck row (`IntroductionSetupModal.js:94-97,260`) |
| G7 | Status display | "pending / fulfilled" (§5) | File icons only | Icon swap, no text (`RequestedDocuments.js:46`) |
| G8 | Cap Table label | "Cap Table and Board Profile" (§8) | Admin: "Cap Table and Board Profile"; seller: "Cap table" | "Cap Table" (`dataRoomModel.js:103`) |
| G9 | `requestedDocuments` shape | — | — | Strings in `deal/query` (`IntroductionSetupModal.js:95`) vs objects in the cue card (`RequestedDocuments.js:21-29`); only `flaggedTopics.js:36-41` handles both |
| G10 | Email per-doc upload status | Not in PRD | Present (`43766:148083`) | Backend |
| G11 | Seller "flagged topics" | Not in PRD | Not drawn | Built but hidden: `SellerDataRoom/index.js:54` commented out; used in `useSellerDashboardHome.js:42` |
| G12 | Buyer analytics for request sent | Needed for §10 metrics | — | No event in `SuccessView.js:83-121` (seller-side events exist, `IntroductionSetupModal.js:7-13`) |
| G13 | Lock enforcement | One-time (§6) | — | FE-only (no re-entry UI). Backend guard unverified |
