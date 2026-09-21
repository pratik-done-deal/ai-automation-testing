"""Environment-driven settings for the document-request suite."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


def _list(name):
    return [v.strip() for v in os.getenv(name, "").split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    app_url: str = os.getenv("DD_APP_URL", "https://qa.done.deals/").rstrip("/") + "/"
    api_url: str = os.getenv("DD_API_URL", "https://qa.done.deals/api/company-service/v1/").rstrip("/") + "/"

    buyer_state: Path = ROOT / os.getenv("DD_BUYER_STATE", "auth/buyer.json")
    seller_state: Path = ROOT / os.getenv("DD_SELLER_STATE", "auth/seller.json")
    admin_state: Path = ROOT / os.getenv("DD_ADMIN_STATE", "auth/admin.json")

    seller_company_id: str = os.getenv("DD_SELLER_COMPANY_ID", "")
    buyer_display_name: str = os.getenv("DD_BUYER_DISPLAY_NAME", "")
    # Phase 1: how many companies to pick from /buyer/browse. Phase 2: which one to test now.
    browse_interest_count: int = int(os.getenv("DD_BROWSE_INTEREST_COUNT", "1"))
    phase2_seller_cue_card_uid: str = os.getenv("DD_PHASE2_SELLER_CUE_CARD_UID", "")
    fresh_company_uids: list = field(default_factory=lambda: _list("DD_FRESH_COMPANY_UIDS"))
    outside_pref_company_uid: str = os.getenv("DD_OUTSIDE_PREF_COMPANY_UID", "")

    admin_deal_with_request_uid: str = os.getenv("DD_ADMIN_DEAL_WITH_REQUEST_UID", "")
    admin_deal_without_request_uid: str = os.getenv("DD_ADMIN_DEAL_WITHOUT_REQUEST_UID", "")


settings = Settings()
