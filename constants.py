"""Document keys, labels and UI copy, mirrored from the web app so tests fail loudly on drift.

Sources:
  src/constants/keyVariableConstants.js          (doc type keys)
  src/Container/DataRoom/dataRoomModel.js        (DATAROOM_KEY_LABEL_MAP)
  src/Component/NewCueCard/SlotSchedulerModal/*  (buyer modal copy)
  src/Container/SellerDealsAndInvestors/*        (seller accept modal copy)
"""

PITCHDECK = "pitch_deck"
CAP_TABLE = "cap_table"
REGISTRATIONS = "registrations_and_licenses"
AUDITED = "audited_financials"
MIS = "mis"
ITR = "itr_filing"
GST = "gst_filing"
CREDIT_RATING = "credit_rating"

DOC_LABELS = {
    PITCHDECK: "Pitchdeck",
    CAP_TABLE: "Cap Table",
    REGISTRATIONS: "Registration & Licenses",
    AUDITED: "Audited Financials",
    MIS: "MIS",
    ITR: "ITR",
    GST: "GST Filing",
    CREDIT_RATING: "Credit rating",
}

# PRD section 7: the only document types a buyer may request (no free text).
PRD_ALLOWED_DOC_TYPES = set(DOC_LABELS)

# What the buyer modal currently offers (SuccessView.DOCUMENT_REQUEST_OPTIONS), in display order.
BUYER_MODAL_OPTIONS = [PITCHDECK, MIS, CAP_TABLE, AUDITED]

EXPRESS_STATUS = "express_interest"
INTRO_PENDING_STATUS = "introduction_pending"


class Copy:
    # Buyer: cue card
    EXPRESS_INTEREST_CTA = "Express Interest"
    EXPRESSED_INTEREST = "Expressed Interest"
    FLAGGED_TITLE = "You flagged for the intro call"
    FLAGGED_SUBTITLE = "A reminder of what you asked to cover."

    # Buyer: slot scheduler
    SLOT_LABEL = "Add preferred slots for meet"  # matches "meet (IST)" and "meeting (IST)"
    ADD_SECOND_SLOT = "Add Second Slot"
    OUTSIDE_PREF_WARNING = "You are expressing interest in a company outside your preferences"
    NOTE_LABEL = "Add a note to send to the founder"
    REQUEST_CALL = "Request Call"

    # Buyer: success view / document request
    SUCCESS_TITLE = "Interest Shared with Founder"
    SUCCESS_SUBTITLE = "Your proposed time slots have been shared with the founder."
    PROPOSED_SLOTS = "Proposed Time Slots:"
    NOTE_SHARED = "Note shared with the founder:"
    DOC_REQUEST_TITLE = "What would you like to discuss in your intro call?"
    DOC_REQUEST_HINT = "Optional. The founder will see this and can prepare."
    ADD_TEAM_MEMBER = "Add Team Member (s)"
    CLOSE = "Close"
    SUBMIT = "Submit"
    CANCEL = "Cancel"
    DOC_REQUEST_SNACKBAR = "Document request sent to founder"

    # Seller: deals + accept modal
    INTEREST_RECEIVED_TAB = "Interest Received"
    ACCEPT = "Accept"
    REJECT = "Reject"
    INVESTOR_MESSAGE = "Investor's message:"
    INVESTOR_WANTS_TO_DISCUSS = "The investor would like to discuss"
    SELLER_PITCH_DECK_LABEL = "Pitch Deck"
    NOT_UPLOADED_YET = "Not uploaded yet"
    UPLOAD = "Upload"
    PITCH_DECK_MANDATORY = "Pitch Deck is mandatory"
    CHOOSE_TIMESLOT = "Choose a timeslot for the introductory call"
    TIMESLOT_REQUIRED = "Please choose a timeslot to continue."

    # Admin: deal page
    ADMIN_DATA_ROOM_TAB = "Data Room"
    ADMIN_TOPICS_TITLE = "Topics for the intro call"


def send_request_label(count):
    return f"Send request ({count})"
