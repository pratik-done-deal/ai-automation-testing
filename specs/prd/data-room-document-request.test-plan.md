# Data Room Document Request — Test Plan & Traceability

- Source: `docs/prd/data-room-document-request.analysis.md` (checkpoint READY, 2026-09-21)
- Suite: `automation/` (pytest + Playwright), 76 tests
- Generated from the test sources: every `DR-xx` below is referenced inside the listed test function.

## Summary

| | Count |
|---|---|
| Requirements | 53 |
| Automated (live) | 40 |
| `not_implemented_yet` (strict xfail) | 6 (DR-03, DR-04, DR-21, DR-22, DR-46+DR-47 as one paired test) |
| Manual | 7 (DR-25–27 email; DR-49–52 reminder, AI summary, on_hold, metrics) |
| Not covered | 0 |

Tests by run group: **phase1** 2 · **phase2** 31 · **standalone** 43 (buyer, api, admin-gating; need `DD_FRESH_COMPANY_UIDS` etc., skip when data is missing). Buyer UI tests run as ordered journeys on one cue card each (`buyer/test_buyer_journey.py`), with no reloads between steps. The slot-modal steps come before DR-01 and have no DR id.

## Run order

1. `pytest -m phase1 --headed`: the buyer expresses interest from `/buyer/browse`. One company gets a request and one gets closed without a request. Both are saved to `run_state/phase1.json`.
2. `python scripts/save_auth_state.py seller`: log in as the seller created by step 1.
3. `pytest -m phase2`: the seller Accept modal (read-only checks first, then one accept), uploads and fulfilment, the no-request deal, and the admin xfail pair.
4. Optional: `pytest -m "not phase1 and not phase2"` for the buyer, API and biz-gating checks. `pytest -m "not not_implemented_yet"` hides the expected-fail tests.

## Traceability

| ID | Requirement | Type | Status | Test(s) |
|---|---|---|---|---|
| DR-01 | After express interest succeeds, the buyer sees a doc-request section "What would you like to discuss in your intro call?" in the confirmation step. | flow | automated | `buyer/test_buyer_journey.py::test_success_view_shows_document_request_section` _standalone_<br>`e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` _standalone_ |
| DR-02 | Request options come only from the existing doc-type list. There's no free-text document input. | rule | automated | `api/test_document_request_api.py::test_unknown_or_free_text_types_are_not_stored` _standalone_<br>`buyer/test_buyer_journey.py::test_options_come_only_from_existing_document_list` _standalone_ |
| DR-03 | The other 4 PRD §8 types (Registration & Licenses, ITR, GST Filing, Credit rating) are offered. | rule | `not_implemented_yet` (xfail strict) | `buyer/test_buyer_journey.py::test_other_prd_document_types_are_offered` [xfail] _standalone_ |
| DR-04 | Options are grouped under Company Information / Financial Information / Others. | copy | `not_implemented_yet` (xfail strict) | `buyer/test_buyer_journey.py::test_options_are_grouped_by_category` [xfail] _standalone_ |
| DR-05 | Clicking a doc chip selects it (check shown). Clicking again deselects it. | flow | automated | `buyer/test_buyer_journey.py::test_chip_toggles_selection` _standalone_ |
| DR-06 | With N ≥ 1 selected, the primary CTA reads "Send request (N)". | copy | automated | `buyer/test_buyer_journey.py::test_cta_counts_selected_documents` _standalone_ |
| DR-07 | With nothing selected and no edits, only a "Close" CTA is shown. | copy | automated | `buyer/test_buyer_journey.py::test_only_close_when_nothing_changed` _standalone_ |
| DR-08 | The buyer can add or edit an optional note (max 400 chars) with the request when the note wasn't mandatory in step 1. | flow | automated | `buyer/test_buyer_journey.py::test_note_on_confirmation_step` _standalone_ |
| DR-09 | When the note was mandatory in step 1, it shows read-only under "Note shared with the founder:". | rule | automated | `buyer/test_buyer_journey.py::test_note_on_confirmation_step` _standalone_ |
| DR-10 | "Send request" posts `companyId`, `interactionNotes`, `teamMembers`, `requestedDocTypes[]` to `deal/capture/interest/update`. | flow | automated | `buyer/test_buyer_journey.py::test_send_request_posts_selected_types_and_closes` _standalone_<br>`e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` _standalone_ |
| DR-11 | `requestedDocTypes` is left out of the payload when nothing is selected. | edge-case | automated | `api/test_document_request_api.py::test_empty_list_creates_no_request` _standalone_<br>`buyer/test_buyer_journey.py::test_note_only_submit_omits_requested_types` _standalone_ |
| DR-12 | On success, the snackbar shows "Document request sent to founder" (unless the backend sends a message) and the modal closes. | copy | automated | `buyer/test_buyer_journey.py::test_send_request_posts_selected_types_and_closes` _standalone_<br>`buyer/test_buyer_journey.py::test_request_error_keeps_step_open` _standalone_<br>`e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` _standalone_ |
| DR-13 | Closing with nothing selected creates no request: no update call, no cue card section. | edge-case | automated | `api/test_document_request_api.py::test_empty_list_creates_no_request` _standalone_<br>`e2e/test_phase1_buyer_requests.py::test_express_interest_and_close_without_request` _standalone_ |
| DR-14 | "Cancel" clears the selected docs and reverts the note and team edits. | flow | automated | `buyer/test_buyer_journey.py::test_cancel_clears_selection_and_edits` _standalone_ |
| DR-15 | After the modal closes, the buyer has no UI to add documents to the request. | lock | automated | `api/test_document_request_api.py::test_request_locked_after_modal_closed_empty` _standalone_<br>`buyer/test_buyer_journey.py::test_no_ui_to_change_the_request_after_close` _standalone_<br>`e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` _standalone_ |
| DR-16 | A second update call with `requestedDocTypes` for the same deal is rejected or ignored by the backend. | lock | automated | `api/test_document_request_api.py::test_second_submission_cannot_extend_request` _standalone_<br>`api/test_document_request_api.py::test_request_locked_after_modal_closed_empty` _standalone_<br>`buyer/test_buyer_journey.py::test_backend_rejects_adding_documents_after_lock` _standalone_ |
| DR-17 | Once a request exists, the buyer's cue card shows "You flagged for the intro call" / "A reminder of what you asked to cover." with one chip per requested doc. | flow | automated | `buyer/test_buyer_journey.py::test_flagged_card_appears_without_reload` _standalone_<br>`buyer/test_buyer_journey.py::test_request_persists_after_reload` _standalone_<br>`e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` _standalone_ |
| DR-18 | The cue card has no requested-docs card when there's no request. | gating | automated | `e2e/test_phase1_buyer_requests.py::test_express_interest_and_close_without_request` _standalone_ |
| DR-19 | The pitch deck chip is listed first on the cue card. Other chips keep request order. | rule | automated | `buyer/test_buyer_journey.py::test_pitch_deck_leads_and_others_keep_request_order` _standalone_ |
| DR-20 | A fulfilled requested doc shows a green check icon. A pending one shows a document icon. | rule | automated | `buyer/test_buyer_journey.py::test_chip_icon_matches_fulfilment_state` _standalone_<br>`e2e/test_phase2_seller_fulfils.py::test_04_partial_upload_keeps_request_open` _standalone_ |
| DR-21 | The buyer's deals tab shows requested docs and their pending/fulfilled status. | flow | `not_implemented_yet` (xfail strict) | `buyer/test_buyer_journey.py::test_buyer_deals_tab_shows_requested_docs_and_status` [xfail] _standalone_ |
| DR-22 | The buyer can raise the request at introduction_pending (decision Q1: both entry points). | flow | `not_implemented_yet` (xfail strict) | `e2e/test_phase2_no_request_deal.py::test_02_seller_accepts` _standalone_<br>`e2e/test_phase2_no_request_deal.py::test_03_buyer_can_raise_request_at_introduction_pending` [xfail] _standalone_ |
| DR-23 | A biz or admin user viewing a cue card never gets the Express Interest step, so no doc-request modal appears. | gating | automated | `admin/test_admin_document_request.py::test_biz_user_cue_card_has_no_express_interest_or_request_step` _standalone_<br>`admin/test_admin_document_request.py::test_biz_edit_deal_state_has_no_document_request_step` _standalone_ |
| DR-24 | A biz-user-performed EI/intro transition captures no request. | gating | automated | `admin/test_admin_document_request.py::test_biz_edit_deal_state_has_no_document_request_step` _standalone_ |
| DR-25 | The seller's EI/intro-pending email lists the requested doc types and the buyer's note when a request exists. | flow | manual | — (manual: seller email; no mailbox tests) |
| DR-26 | The seller email has no requested-docs section when there's no request. | gating | manual | — (manual: seller email; no mailbox tests) |
| DR-27 | The seller email shows per-doc status ("already uploaded" / "needs upload"). | copy | manual | — (manual: seller email; no mailbox tests) |
| DR-28 | On `/deals` → Interest Received, clicking Accept opens "Accept investor interest?" with a requested-docs section "The investor would like to discuss". | flow | automated | `e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting` _standalone_<br>`seller/test_accept_interest_modal.py::test_accept_opens_modal_with_request_section` _standalone_<br>`seller/test_accept_interest_modal.py::test_dismiss_closes_without_accepting` _standalone_ |
| DR-29 | The Accept modal has one row per requested doc type, labelled from `DATAROOM_KEY_LABEL_MAP` (deck as "Pitch Deck"). | rule | automated | `e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting` _standalone_<br>`seller/test_accept_interest_modal.py::test_one_row_per_requested_type_in_request_order` _standalone_ |
| DR-30 | The Pitch Deck row is always present, first and marked required (*), even when not requested. | rule | automated | `seller/test_accept_interest_modal.py::test_pitch_deck_row_is_pinned_first_required_and_single` _standalone_ |
| DR-31 | With no request, the section shows only the Pitch Deck row. | gating | automated | `e2e/test_phase2_no_request_deal.py::test_01_accept_modal_shows_only_the_deck_row` _standalone_<br>`seller/test_accept_interest_modal.py::test_only_pitch_deck_row_without_request` _standalone_ |
| DR-32 | Each row shows status: attached file name, "N file(s) in your data room", or "Not uploaded yet". | copy | automated | `e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting` _standalone_<br>`seller/test_accept_interest_modal.py::test_row_status_reflects_the_data_room` _standalone_ |
| DR-33 | A row with no existing files shows "Upload". Uploading sends that row's `docType` and auto-attaches the file. | flow | automated | `e2e/test_phase2_seller_fulfils.py::test_02_seller_uploads_one_requested_doc_and_accepts` _standalone_<br>`seller/test_accept_interest_modal.py::test_upload_sends_the_row_type_and_auto_attaches` _standalone_ |
| DR-34 | A row with existing files shows "Attach ▾" listing files of that type. Once picked, it shows "Attached" plus a remove (×) button. | flow | automated | `seller/test_accept_interest_modal.py::test_attach_existing_file_then_remove` _standalone_ |
| DR-35 | The header counter shows attached/total rows (e.g. "1/3"). | copy | automated | `seller/test_accept_interest_modal.py::test_counter_counts_attached_rows` _standalone_ |
| DR-36 | The latest pitch deck on file is pre-attached once. | rule | automated | `seller/test_accept_interest_modal.py::test_deck_is_pre_attached_once` _standalone_ |
| DR-37 | Accepting without a deck attached shows "Pitch Deck is mandatory. Please share/upload a Pitch Deck to continue." | edge-case | automated | `seller/test_accept_interest_modal.py::test_accept_without_a_deck_is_blocked` _standalone_ |
| DR-38 | The seller can accept without attaching non-deck requested docs (the request doesn't block). | rule | automated | `e2e/test_phase2_seller_fulfils.py::test_02_seller_uploads_one_requested_doc_and_accepts` _standalone_<br>`seller/test_accept_interest_modal.py::test_open_requests_do_not_block_accept` _standalone_ |
| DR-39 | When slots exist, accepting without choosing one shows "Please choose a timeslot to continue." | edge-case | automated | `seller/test_accept_interest_modal.py::test_timeslot_is_required_when_slots_exist` _standalone_ |
| DR-40 | Accept posts `deal/seller` {buyerId, companyId, dealStatus: introduction_pending, docUid (deck), slotId}, then `document/deal/share` {dealIds, uids} for the other attached docs. | flow | automated | `e2e/test_phase2_seller_fulfils.py::test_02_seller_uploads_one_requested_doc_and_accepts` _standalone_<br>`seller/test_accept_interest_modal.py::test_accept_payload_and_extra_share` _standalone_ |
| DR-41 | The buyer's note shows as "Investor's message:" when present, and is hidden when empty or "--". | rule | automated | `e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting` _standalone_<br>`seller/test_accept_interest_modal.py::test_investor_message_only_when_buyer_left_a_note` _standalone_ |
| DR-42 | After accepting, the seller can upload and share requested docs through the existing flow. | flow | automated | `e2e/test_phase2_seller_fulfils.py::test_06_seller_shares_a_requested_doc_from_active_deals` _standalone_ |
| DR-43 | Uploading a doc of a requested type marks that item fulfilled, whoever uploads it. | rule | automated | `e2e/test_phase2_seller_fulfils.py::test_04_partial_upload_keeps_request_open` _standalone_<br>`e2e/test_phase2_seller_fulfils.py::test_05_remaining_uploads_fulfil_everything` _standalone_ |
| DR-44 | Uploading a doc of a non-requested type doesn't change the request's status. | edge-case | automated | `e2e/test_phase2_seller_fulfils.py::test_03_non_requested_upload_does_not_touch_request` _standalone_ |
| DR-45 | The request stays open until all requested types are uploaded (partial = open). | rule | automated | `e2e/test_phase2_seller_fulfils.py::test_04_partial_upload_keeps_request_open` _standalone_<br>`e2e/test_phase2_seller_fulfils.py::test_05_remaining_uploads_fulfil_everything` _standalone_ |
| DR-46 | Admin → `/admin/deal-notes/:uid` → Data Room shows "Topics for the intro call" with the requested docs. | flow | `not_implemented_yet` (xfail strict) | `admin/test_admin_document_request.py::test_data_room_topics_card_only_when_request_exists` [xfail] _standalone_ |
| DR-47 | The admin Data Room has no topics card when there's no request. | gating | `not_implemented_yet` (xfail strict) | `admin/test_admin_document_request.py::test_data_room_topics_card_only_when_request_exists` [xfail] _standalone_ |
| DR-48 | One deal note holds the requested types plus the note text. | rule | automated | `e2e/test_phase2_seller_fulfils.py::test_07_request_stored_as_single_deal_note` _standalone_ |
| DR-49 | The standard pending-action reminder attaches to the request note. | non-functional | manual | — (manual: backend scheduler / daily job / analytics) |
| DR-50 | The daily AI summary reports newly fulfilled and still-pending items, including partial closure. | non-functional | manual | — (manual: backend scheduler / daily job / analytics) |
| DR-51 | An on_hold deal pauses and resumes reminders as it does today. | edge-case | manual | — (manual: backend scheduler / daily job / analytics) |
| DR-52 | Success metrics (§10) can be measured. | non-functional | manual | — (manual: backend scheduler / daily job / analytics) |
| DR-53 | The confirmation step offers exactly the 4 built options, in order: Pitchdeck, MIS, Cap Table, Audited Financials (decision Q2). | rule | automated | `buyer/test_buyer_journey.py::test_offers_exactly_the_four_built_options_in_order` _standalone_ |