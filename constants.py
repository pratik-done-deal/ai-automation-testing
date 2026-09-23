"""Document keys, labels and UI copy, mirrored from the web app so tests fail loudly on drift.

Where Figma and the app disagree, the app's copy is the source of truth (analysis gap G5).

Sources:
  src/constants/keyVariableConstants.js                                 (doc type keys)
  src/Container/DataRoom/dataRoomModel.js:101-110                       (DATAROOM_KEY_LABEL_MAP)
  src/Component/NewCueCard/SlotSchedulerModal/SuccessView.js            (buyer doc request step)
  src/Component/NewCueCard/CuecardDefaultSection/components/RequestedDocuments.js (buyer cue card)
  src/Container/SellerDealsAndInvestors/components/IntroductionSetupModal.js, RequestedDocumentRow.js
  src/Container/SellerDealsAndInvestors/components/ManageSharedDocsModal.js, hooks/useSharedDocs.js
  src/Component/LoginFormField/index.js, src/Component/NewAuthOtpFlow/index.js               (buyer login)
  src/Container/BuyersContainer/BuyerLogin/index.js, src/Container/NewLoginContainer/index.js (buyer login)
"""

PITCHDECK = "pitch_deck"
CAP_TABLE = "cap_table"
REGISTRATIONS = "registrations_and_licenses"
AUDITED = "audited_financials"
MIS = "mis"
ITR = "itr_filing"
GST = "gst_filing"
CREDIT_RATING = "credit_rating"

# DATAROOM_KEY_LABEL_MAP, in the map's own order.
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

# PRD section 8: the only document types a buyer may request (no free text).
PRD_ALLOWED_DOC_TYPES = set(DOC_LABELS)

# DR-53: what the buyer step offers today (SuccessView.DOCUMENT_REQUEST_OPTIONS, :27-31), in order.
BUYER_MODAL_OPTIONS = [PITCHDECK, MIS, CAP_TABLE, AUDITED]

# DR-03: PRD types that are commented out of the buyer step (SuccessView.js:32-35).
NOT_BUILT_REQUEST_OPTIONS = [REGISTRATIONS, ITR, GST, CREDIT_RATING]

# DR-04: PRD section 8 grouping (not built; the buyer step is a flat list).
PRD_CATEGORIES = {
    "Company Information": [PITCHDECK, CAP_TABLE, REGISTRATIONS],
    "Financial Information": [AUDITED, MIS, ITR, GST],
    "Others": [CREDIT_RATING],
}

# PRD section 8 / Figma admin frame spell the cap table differently from the app (gap G8).
PRD_CAP_TABLE_LABEL = "Cap Table and Board Profile"

EXPRESS_STATUS = "express_interest"
INTRO_PENDING_STATUS = "introduction_pending"

# useIntroductionSetup / utils.isEngagementLetterDocument: never listed in the Accept modal.
ENGAGEMENT_LETTER_DOC_TYPE = "engagement_letter"


class Copy:
    # Buyer: cue card (BuyerActionsCard, RequestedDocuments)
    EXPRESS_INTEREST_CTA = "Express Interest"
    EXPRESSED_INTEREST = "Expressed Interest"
    FLAGGED_TITLE = "You flagged for the intro call"
    FLAGGED_SUBTITLE = "A reminder of what you asked to cover."

    # Buyer: slot scheduler (SlotSchedulerModal)
    SLOT_LABEL = "Add preferred slots for meet"  # matches "meet (IST)" and "meeting (IST)"
    ADD_SECOND_SLOT = "Add more"  # Figma says "Add Second Slot" (SlotSchedulerModal/index.js:411)
    NOTE_LABEL = "Add a note to send to the founder"
    REQUEST_CALL = "Request Call"
    EI_SUCCESS_SNACKBAR = "Successfully sent interest to company"

    # Buyer: success view / document request (SuccessView)
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
    NOTE_ONLY_SNACKBAR = "Successfully updated details"
    GENERIC_ERROR = "Something went wrong"

    # Seller: deals table. Tabs render SellerDealsTab.js `displayLabel` (Figma: "Interest Received").
    INTEREST_RECEIVED_TAB = "Interest received"
    ACTIVE_DEALS_TAB = "Active deals"
    ACCEPT = "Accept"
    REJECT = "Reject"

    # Seller: accept modal (IntroductionSetupModal, RequestedDocumentRow). Figma copy differs (G5).
    ACCEPT_MODAL_TITLE = "Accept investor interest?"
    IDENTITY_REVEALED = "Your identity will be revealed to"
    INVESTOR_MESSAGE = "Investor's message:"
    INVESTOR_WANTS_TO_DISCUSS = "The investor would like to discuss"
    SELLER_PITCH_DECK_LABEL = "Pitch Deck"
    NOT_UPLOADED_YET = "Not uploaded yet"
    UPLOAD = "Upload"
    UPLOADING = "Uploading…"
    ATTACH = "Attach"
    ATTACHED = "Attached"
    PITCH_DECK_MANDATORY = "Pitch Deck is mandatory"
    PITCH_DECK_MANDATORY_SHARE = "Pitch Deck is mandatory. Please share a Pitch Deck to continue."
    PITCH_DECK_MANDATORY_UPLOAD = "Pitch Deck is mandatory. Please upload a Pitch Deck to continue."
    CHOOSE_TIMESLOT = "Choose a timeslot for the introductory call"
    TIMESLOT_REQUIRED = "Please choose a timeslot to continue."

    # Seller: Active Deals manage-docs modal (ManageSharedDocsModal, useSharedDocs)
    SAVE_EDITS = "Save edits"
    DOCUMENT_ACCESS_UPDATED = "Document access updated"

    # Admin: deal page (dealNotesTabModel, DealDataRoom). The topics card is Figma-only (DR-46).
    ADMIN_DATA_ROOM_TAB = "Data Room"
    ADMIN_NO_DOCS = "No Documents Shared"
    ADMIN_TOPICS_TITLE = "Topics for the intro call"
    ADMIN_EDIT_DEAL_TITLE = "Edit deal state for D"


# ---------------------------------------------------------------- buyer login (module buyer-login)

# localStorage keys a login writes or clears. src/constants/index.js:5,6,147,307,308.
TOKEN_KEY = "authToken"
SESSION_ID_KEY = "sessionid"          # written pre-login from a response header (apiService.js:105-109)
BUYER_ID_KEY = "buyerId"
SELLER_UID_KEY = "seller_uid"
SAVED_PROFILE_KEY = "saved_buyer_profile"
SAVE_LOGIN_MODAL_SHOWN_KEY = "saveLoginModalShown"
# The whole persisted Redux state (authorizationStore, commonStore, buyerVerificationStore).
# src/utils/persistState.js:3,16 - it is what the store boots from, so seeding it seeds a session.
PERSISTED_STATE_KEY = "state"

# Where a buyer lands after login. Services/index.js:18-35, NewLoginContainer/index.js:313-333.
BUYER_LANDING_DESKTOP = "/buyer/recommendations"
BUYER_LANDING_MOBILE = "/buyer/browse"      # <= 1180px (commonHelper.js:173-184)
BUYER_PROFILE_PATH = "/buyer/profile"
BUYER_ONBOARDING_PATH = "/buyer/onboarding"
BUYER_LOGIN_PATH = "/buyer/login"


class BuyerLoginCopy:
    """Exact strings on /buyer/login. Straight quotes are NOT interchangeable with the app's U+2019."""

    PAGE_TITLE = "Login - Done Deal"                          # helper/PageMeta.js:23-25

    # Step 1 (LoginFormField)
    EMAIL_HEADING = "Enter your email to continue"
    EMAIL_SUBTITLE = "We’ll verify your email and take you forward."
    EMAIL_LABEL = "Official Email ID"
    EMAIL_PLACEHOLDER = "Enter your work email"
    EMAIL_HINT = "A 6-digit code will be sent to your email and mobile for verification."
    VERIFY_CTA = "Verify"                                     # StepActionTitle[1]
    SIGNUP_PROMPT = "Don’t have an account?"
    SIGNUP_LINK = "Sign up here"
    GOOGLE_CAPTION = "Use a work email to Sign in"             # uppercased by CSS

    # Step 2 (NewAuthOtpFlow, BuyerLogin footer)
    OTP_HEADING = "Check Your Device"
    OTP_SENT_PREFIX = "We’ve sent a 6-digit code to"
    OTP_SENT_SUFFIX = ". Enter it below to verify and continue securely."
    OTP_LABEL = "Verification code"
    OTP_PLACEHOLDER = "Enter 6-digit code"
    OTP_CTA = "Verify & Login"                                # StepActionTitle[2]
    RESEND_PROMPT = "Didn’t receive the code?"
    RESEND_LINK = "Click here"

    # Errors and snackbars (src/constants/index.js:167-169; NewLoginContainer/index.js:200,377,386)
    INCORRECT_EMAIL_HELPER = "Please enter your registered email ID"
    INCORRECT_OTP_HELPER = "The OTP you entered is incorrect. Please try again."
    SOMETHING_WENT_BAD = "Something went bad!!"
    NOT_PROFESSIONAL_EMAIL = "Please register using your professional email ID."
    PASSCODE_SENT = "Passcode Sent"
    RESEND_FAILED = "Please try again later"

    # Production-only guard, inert on QA (hooks/useViewportGuard.js:24-31)
    VIEWPORT_GUARD = "Screen size changed"


def send_request_label(count):
    return f"Send request ({count})"


def files_in_data_room(count):
    # RequestedDocumentRow.js:45
    return f"{count} file{'' if count == 1 else 's'} in your data room"


def remove_attached_label(row_label):
    # RequestedDocumentRow.js:75
    return f"Remove attached {row_label}"


def share_toggle_label(file_name):
    # DocumentShareRow.js ShareToggle aria-label
    return f"Share {file_name} with the investor"
