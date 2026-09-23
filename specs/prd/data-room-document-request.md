# Data Room Document Request Management

Design: https://www.figma.com/design/RWMCvpU1gf3ydyJxTyQwsA/Sprint-Work?node-id=43762-141750

## 1. The Problem
Buyers have no way to tell a seller which documents they need at the moment they express interest. Today that ask only becomes known once the deal reaches introduction pending — after the buyer has already committed to a conversation.

This means sellers get no advance notice of what to prepare, buyer owners have no way to check whether documents were shared before the intro call, and intro calls can happen without the documents the buyer actually asked for.

## 2. What We Are Solving
Let buyers request specific documents (from the existing document list, not free text) at express interest or introduction pending. Make that request visible to the seller immediately, track it using the systems already in place (deal notes, reminders, AI summary), and give the buyer, seller, and buyer owner the same source of truth — without building new tracking mechanisms.

## 3. Users
- **Buyer** — expresses interest and requests the documents they need.
- **Seller** — sees the request and decides whether to upload the documents (not mandatory).
- **Buyer owner (biz user)** — needs visibility that the request gets fulfilled before the intro call.
- **Biz user acting on the buyer's behalf** — moves the deal forward without going through document selection.

## 4. The Core Idea
One request. One note. Three existing surfaces.

At express interest / introduction pending, the buyer picks from the existing document type list and can add an optional note.

This creates a single deal note, which rides the existing pending-action reminder mechanism already used for express-interest and intro-pending deals.

That same note is what appears on the deals tab, what the seller sees when accepting, and what the AI summary reads from.

No new tables, no new reminder logic, no new summary logic — everything reuses what already exists.

## 5. What Each User Sees / Flow

### Buyer
- At express interest / introduction pending, a modal opens: select the documents needed from the existing list, optionally add a note.
- Once the modal is closed, the request is locked — no further documents can be added to it.
- Post-request, the buyer's deals tab and the detailed cue card show the requested documents and their status (pending / fulfilled).

### Seller
- The express-interest or introduction-pending email includes the requested document types and the buyer's note — only when the buyer raised the request.
- On the seller's deals tab, while accepting the request, the seller sees what was asked for.
- After accepting, the seller can upload and share the requested documents through the existing upload flow.

### Buyer owner (Admin / Biz)
- Admin > Deals tab > Data Room shows the document request for that deal.
- The AI summary (daily) narrates what's been fulfilled and what's still open, regardless of who uploaded it.

### Biz user acting for the buyer
- The document-request modal does not appear. This step is skipped entirely for biz-user-initiated actions.

## 6. Logics
- **Trigger:** only on a buyer-initiated express_interest or introduction_pending action — not when a biz user performs it on the buyer's behalf.
- **Document options:** existing document type list only. No free-text document names.
- **One-time capture:** the request is locked once the modal closes. No edits or additions afterward.
- **Storage:** a single deal note holds the requested document types plus the buyer's optional note text.
- **Reminder:** the standard pending-action reminder mechanism attaches to this note, same as existing express-interest / intro-pending reminders.
- **Fulfillment:** uploading a document that matches a requested type marks that item fulfilled — regardless of whether the seller, a biz user, or the buyer's side performs the upload.
- **Not mandatory:** the seller can skip fulfilling the request; the deal is not blocked by an open request.
- **Visibility gating:** seller email inclusion, seller deals-tab view, and the admin Data Room view are only populated when a request exists.
- **AI summary:** diffs the previous day's state against the latest, and reports newly closed items and anything still pending, on the existing daily cadence.

## 7. User Stories
- **Story 1 — Buyer requests documents:** As a buyer, I want to request specific documents when I express interest, so that the seller knows what to prepare before our intro call.
- **Story 2 — Seller sees the request via email:** As a seller, I want to see requested documents in my express-interest / intro-pending email, so I can prepare or upload them in advance.
- **Story 3 — Seller sees the request while accepting:** As a seller, I want to see the document request again when I accept, so I can share the documents right after accepting.
- **Story 4 — Buyer owner tracks fulfillment:** As a buyer owner, I want to see pending document requests on the deals tab and in the AI summary, so I know whether documents are shared before the intro call.
- **Story 5 — Biz user is not blocked by this step:** As a biz user acting on behalf of a buyer, I want the document-request step skipped, so I'm not forced through a step that isn't mine to fill.

## 8. Document categorisation in buyer tab
- **Company Information:** Pitchdeck; Cap Table and Board Profile; Registration & Licenses
- **Financial Information:** Audited Financials; MIS; ITR; GST Filing
- **Others:** Credit rating

## 9. Edge Cases

| Scenario | Expected behavior |
|---|---|
| Buyer requests documents but seller never uploads them. | Reminder stays open; AI summary keeps flagging it as pending; seller is not blocked from other deal actions. |
| Biz user performs express interest / intro pending on the buyer's behalf. | No document-request modal is shown; no request is captured for that transition. |
| Buyer closes the modal without selecting anything. | Treated as no request; no note is created. |
| Buyer wants to add more documents after submitting. | Not allowed — the request is locked once the modal closes. |
| Seller uploads a document that wasn't requested. | Uploads normally through the existing flow; does not affect the open request's status. |
| Multiple document types requested, only some uploaded. | Request stays open until all are uploaded; AI summary reports partial closure day over day. |
| Deal goes on_hold after the request is raised. | Follows existing on_hold reminder handling (pauses and resumes with the deal); no new behavior needed. |

## 10. Success Metrics
- % of buyer-initiated express-interest / introduction-pending deals where a document request is raised.
- Time from request raised to first matching document uploaded.
- % of requests fulfilled before the scheduled intro-call date.
- Seller response rate to document requests (uploaded vs. skipped).
