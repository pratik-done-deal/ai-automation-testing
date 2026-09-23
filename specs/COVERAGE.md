# Coverage

## Data Room Document Request (`data-room-document-request`, feature, shipped)

53 requirements: 41 live, 5 xfail, 7 manual

| ID | Requirement | State | Tests |
|---|---|---|---|
| DR-01 | After express interest succeeds, the buyer sees a doc-request section "What woul | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_success_view_shows_document_request_section`<br>`test_cases/e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` |
| DR-02 | Request options come only from the existing doc-type list. There's no free-text  | live | `test_cases/api/test_document_request_api.py::test_unknown_or_free_text_types_are_not_stored`<br>`test_cases/buyer_test_cases/test_buyer_journey.py::test_options_come_only_from_existing_document_list` |
| DR-03 | The other 4 PRD §8 types (Registration & Licenses, ITR, GST Filing, Credit ratin | xfail | `test_cases/buyer_test_cases/test_buyer_journey.py::test_other_prd_document_types_are_offered` |
| DR-04 | Options are grouped under Company Information / Financial Information / Others. | xfail | `test_cases/buyer_test_cases/test_buyer_journey.py::test_options_are_grouped_by_category` |
| DR-05 | Clicking a doc chip selects it (check shown). Clicking again deselects it. | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_chip_toggles_selection` |
| DR-06 | With N ≥ 1 selected, the primary CTA reads "Send request (N)". | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_cta_counts_selected_documents` |
| DR-07 | With nothing selected and no edits, only a "Close" CTA is shown. | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_only_close_when_nothing_changed` |
| DR-08 | The buyer can add or edit an optional note (max 400 chars) with the request when | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_note_on_confirmation_step` |
| DR-09 | When the note was mandatory in step 1, it shows read-only under "Note shared wit | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_note_on_confirmation_step` |
| DR-10 | "Send request" posts `companyId`, `interactionNotes`, `teamMembers`, `requestedD | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_send_request_posts_selected_types_and_closes`<br>`test_cases/e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` |
| DR-11 | `requestedDocTypes` is left out of the payload when nothing is selected. | live | `test_cases/api/test_document_request_api.py::test_empty_list_creates_no_request`<br>`test_cases/buyer_test_cases/test_buyer_journey.py::test_note_only_submit_omits_requested_types` |
| DR-12 | On success, the snackbar shows "Document request sent to founder" (unless the ba | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_request_error_keeps_step_open`<br>`test_cases/buyer_test_cases/test_buyer_journey.py::test_send_request_posts_selected_types_and_closes`<br>`test_cases/e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` |
| DR-13 | Closing with nothing selected creates no request: no update call, no cue card se | live | `test_cases/api/test_document_request_api.py::test_empty_list_creates_no_request`<br>`test_cases/e2e/test_phase1_buyer_requests.py::test_express_interest_and_close_without_request` |
| DR-14 | "Cancel" clears the selected docs and reverts the note and team edits. | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_cancel_clears_selection_and_edits` |
| DR-15 | After the modal closes, the buyer has no UI to add documents to the request. | live | `test_cases/api/test_document_request_api.py::test_request_locked_after_modal_closed_empty`<br>`test_cases/buyer_test_cases/test_buyer_journey.py::test_express_interest_is_now_disabled`<br>`test_cases/buyer_test_cases/test_buyer_journey.py::test_no_ui_to_change_the_request_after_close`<br>`test_cases/e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` |
| DR-16 | A second update call with `requestedDocTypes` for the same deal is rejected or i | live | `test_cases/api/test_document_request_api.py::test_second_submission_cannot_extend_request`<br>`test_cases/api/test_document_request_api.py::test_request_locked_after_modal_closed_empty`<br>`test_cases/buyer_test_cases/test_buyer_journey.py::test_backend_rejects_adding_documents_after_lock` |
| DR-17 | Once a request exists, the buyer's cue card shows "You flagged for the intro cal | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_flagged_card_appears_without_reload`<br>`test_cases/buyer_test_cases/test_buyer_journey.py::test_request_persists_after_reload`<br>`test_cases/e2e/test_phase1_buyer_requests.py::test_express_interest_and_request_docs_from_browse` |
| DR-18 | The cue card has no requested-docs card when there's no request. | live | `test_cases/e2e/test_phase1_buyer_requests.py::test_express_interest_and_close_without_request` |
| DR-19 | The pitch deck chip is listed first on the cue card. Other chips keep request or | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_pitch_deck_leads_and_others_keep_request_order` |
| DR-20 | A fulfilled requested doc shows a green check icon. A pending one shows a docume | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_chip_icon_matches_fulfilment_state`<br>`test_cases/e2e/test_phase2_seller_fulfils.py::test_04_partial_upload_keeps_request_open` |
| DR-21 | The buyer's deals tab shows requested docs and their pending/fulfilled status. | xfail | `test_cases/buyer_test_cases/test_buyer_journey.py::test_buyer_deals_tab_shows_requested_docs_and_status` |
| DR-22 | The buyer can raise the request at introduction_pending (decision Q1: both entry | live | `test_cases/e2e/test_phase2_no_request_deal.py::test_02_seller_accepts`<br>`test_cases/e2e/test_phase2_no_request_deal.py::test_03_buyer_can_raise_request_at_introduction_pending` |
| DR-23 | A biz or admin user viewing a cue card never gets the Express Interest step, so  | live | `test_cases/admin_test_cases/test_admin_document_request.py::test_biz_user_cue_card_has_no_express_interest_or_request_step`<br>`test_cases/admin_test_cases/test_admin_document_request.py::test_biz_edit_deal_state_has_no_document_request_step` |
| DR-24 | A biz-user-performed EI/intro transition captures no request. | live | `test_cases/admin_test_cases/test_admin_document_request.py::test_biz_edit_deal_state_has_no_document_request_step` |
| DR-25 | The seller's EI/intro-pending email lists the requested doc types and the buyer' | manual | — |
| DR-26 | The seller email has no requested-docs section when there's no request. | manual | — |
| DR-27 | The seller email shows per-doc status ("already uploaded" / "needs upload"). | manual | — |
| DR-28 | On `/deals` → Interest Received, clicking Accept opens "Accept investor interest | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_accept_opens_modal_with_request_section`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_dismiss_closes_without_accepting` |
| DR-29 | The Accept modal has one row per requested doc type, labelled from `DATAROOM_KEY | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_one_row_per_requested_type_in_request_order` |
| DR-30 | The Pitch Deck row is always present, first and marked required (*), even when n | live | `test_cases/seller_test_cases/test_accept_interest_modal.py::test_pitch_deck_row_is_pinned_first_required_and_single` |
| DR-31 | With no request, the section shows only the Pitch Deck row. | live | `test_cases/e2e/test_phase2_no_request_deal.py::test_01_accept_modal_shows_only_the_deck_row`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_only_pitch_deck_row_without_request` |
| DR-32 | Each row shows status: attached file name, "N file(s) in your data room", or "No | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_row_status_reflects_the_data_room` |
| DR-33 | A row with no existing files shows "Upload". Uploading sends that row's `docType | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_02_seller_uploads_one_requested_doc_and_accepts`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_upload_sends_the_row_type_and_auto_attaches` |
| DR-34 | A row with existing files shows "Attach ▾" listing files of that type. Once pick | live | `test_cases/seller_test_cases/test_accept_interest_modal.py::test_attach_existing_file_then_remove` |
| DR-35 | The header counter shows attached/total rows (e.g. "1/3"). | live | `test_cases/seller_test_cases/test_accept_interest_modal.py::test_counter_counts_attached_rows` |
| DR-36 | The latest pitch deck on file is pre-attached once. | live | `test_cases/seller_test_cases/test_accept_interest_modal.py::test_deck_is_pre_attached_once` |
| DR-37 | Accepting without a deck attached shows "Pitch Deck is mandatory. Please share/u | live | `test_cases/seller_test_cases/test_accept_interest_modal.py::test_accept_without_a_deck_is_blocked` |
| DR-38 | The seller can accept without attaching non-deck requested docs (the request doe | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_02_seller_uploads_one_requested_doc_and_accepts`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_open_requests_do_not_block_accept` |
| DR-39 | When slots exist, accepting without choosing one shows "Please choose a timeslot | live | `test_cases/seller_test_cases/test_accept_interest_modal.py::test_timeslot_is_required_when_slots_exist` |
| DR-40 | Accept posts `deal/seller` {buyerId, companyId, dealStatus: introduction_pending | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_02_seller_uploads_one_requested_doc_and_accepts`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_accept_payload_and_extra_share` |
| DR-41 | The buyer's note shows as "Investor's message:" when present, and is hidden when | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_01_seller_sees_request_when_accepting`<br>`test_cases/seller_test_cases/test_accept_interest_modal.py::test_investor_message_only_when_buyer_left_a_note` |
| DR-42 | After accepting, the seller can upload and share requested docs through the exis | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_06_seller_shares_a_requested_doc_from_active_deals` |
| DR-43 | Uploading a doc of a requested type marks that item fulfilled, whoever uploads i | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_04_partial_upload_keeps_request_open`<br>`test_cases/e2e/test_phase2_seller_fulfils.py::test_05_remaining_uploads_fulfil_everything` |
| DR-44 | Uploading a doc of a non-requested type doesn't change the request's status. | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_03_non_requested_upload_does_not_touch_request` |
| DR-45 | The request stays open until all requested types are uploaded (partial = open). | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_04_partial_upload_keeps_request_open`<br>`test_cases/e2e/test_phase2_seller_fulfils.py::test_05_remaining_uploads_fulfil_everything` |
| DR-46 | Admin → `/admin/deal-notes/:uid` → Data Room shows "Topics for the intro call" w | xfail | `test_cases/admin_test_cases/test_admin_document_request.py::test_data_room_topics_card_only_when_request_exists` |
| DR-47 | The admin Data Room has no topics card when there's no request. | xfail | `test_cases/admin_test_cases/test_admin_document_request.py::test_data_room_topics_card_only_when_request_exists` |
| DR-48 | One deal note holds the requested types plus the note text. | live | `test_cases/e2e/test_phase2_seller_fulfils.py::test_07_request_stored_as_single_deal_note` |
| DR-49 | The standard pending-action reminder attaches to the request note. | manual | — |
| DR-50 | The daily AI summary reports newly fulfilled and still-pending items, including  | manual | — |
| DR-51 | An on_hold deal pauses and resumes reminders as it does today. | manual | — |
| DR-52 | Success metrics (§10) can be measured. | manual | — |
| DR-53 | The confirmation step offers exactly the 4 built options, in order: Pitchdeck, M | live | `test_cases/buyer_test_cases/test_buyer_journey.py::test_offers_exactly_the_four_built_options_in_order` |

## Totals

41 live, 5 xfail, 7 manual

Tests naming no requirement id: 10
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_express_interest_opens_slot_modal`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_request_call_blocked_until_slot_selected`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_past_dates_are_disabled`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_picking_a_date_shows_time_slots_with_back`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_confirm_selection_disabled_until_time_chosen`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_back_returns_to_calendar`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_confirmed_slot_shows_date_and_30_minute_range`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_add_second_slot`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_cancel_asks_for_confirmation_and_back_keeps_slots`
- `test_cases/buyer_test_cases/test_buyer_journey.py::test_request_call_creates_the_interest`
