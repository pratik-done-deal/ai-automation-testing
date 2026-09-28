"""Environment-driven settings for the document-request suite."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


def _flag(name, default="1"):
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "")


@dataclass(frozen=True)
class Settings:
    app_url: str = os.getenv("DD_APP_URL", "https://qa.done.deals/").rstrip("/") + "/"
    api_url: str = os.getenv("DD_API_URL", "https://qa.done.deals/api/company-service/v1/").rstrip("/") + "/"

    buyer_state: Path = ROOT / os.getenv("DD_BUYER_STATE", "auth/buyer.json")
    seller_state: Path = ROOT / os.getenv("DD_SELLER_STATE", "auth/seller.json")
    admin_state: Path = ROOT / os.getenv("DD_ADMIN_STATE", "auth/admin.json")
    # star-seller-fundraising: a biz user (userType 4), kept apart from the userType 2 admin session
    biz_user_state: Path = ROOT / os.getenv("DD_BIZ_USER_STATE", "auth/biz_user.json")

    seller_company_id: str = os.getenv("DD_SELLER_COMPANY_ID", "")
    # Phase 1: how many companies get a document request. Phase 2: which phase 1 uid to test now.
    browse_interest_count: int = int(os.getenv("DD_BROWSE_INTEREST_COUNT", "1"))
    # Phase 1 also expresses interest in one more company and closes without requesting (DR-13/18/31/47).
    phase1_no_request_round: bool = _flag("DD_PHASE1_NO_REQUEST_ROUND")
    phase2_seller_cue_card_uid: str = os.getenv("DD_PHASE2_SELLER_CUE_CARD_UID", "")
    # How many /buyer/browse listings a picker opens before giving up.
    browse_max_cards: int = int(os.getenv("DD_BROWSE_MAX_CARDS", "40"))

    # Optional overrides for the admin Data Room pair (DR-46/47); otherwise phase 1's deals are used.
    admin_deal_with_request_uid: str = os.getenv("DD_ADMIN_DEAL_WITH_REQUEST_UID", "")
    admin_deal_without_request_uid: str = os.getenv("DD_ADMIN_DEAL_WITHOUT_REQUEST_UID", "")

    # buyer-login (BUY-LGN): only the live login test and the real not_registered check need these.
    # Everything else on /buyer/login runs against rewritten responses, with no account at all.
    buyer_login_email: str = os.getenv("DD_BUYER_LOGIN_EMAIL", "")
    buyer_login_otp: str = os.getenv("DD_BUYER_LOGIN_OTP", "")
    buyer_login_unregistered_email: str = os.getenv("DD_BUYER_LOGIN_UNREGISTERED_EMAIL", "")

    # hot-lead-engagement-visibility (HLE): hot-lead flows use dedicated, never-hot buyer leads,
    # never auth/buyer.json. Each value is keyed by the test case it feeds (see .env.example).
    hle_buyer_state: Path = ROOT / os.getenv("DD_HLE_BUYER_STATE", "auth/hle_buyer.json")
    hle_poc_links: str = os.getenv("DD_HLE_POC_LINKS", "")
    hle_lead_names: str = os.getenv("DD_HLE_LEAD_NAMES", "")
    hle_fresh_company_uids: str = os.getenv("DD_HLE_FRESH_COMPANY_UIDS", "")
    hle_teaser_unlocked_link: str = os.getenv("DD_HLE_TEASER_UNLOCKED_LINK", "")
    # One scheduler cycle (5 min) plus a 2 min buffer.
    hle_hot_poll_seconds: int = int(os.getenv("DD_HLE_HOT_POLL_SECONDS", "420"))

    # star-seller-fundraising (SSF): the test sellers, keyed by their name in test-cases.md section 6,
    # e.g. "F-ready:<uid>,F-nodeck:<uid>". A missing name skips the cases that need it.
    ssf_sellers: str = os.getenv("DD_SSF_SELLERS", "")


settings = Settings()
