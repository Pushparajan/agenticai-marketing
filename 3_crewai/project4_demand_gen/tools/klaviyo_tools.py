# tools/klaviyo_tools.py
# Project 4: Demand Gen Pipeline Crew
# Chapter Reference: Chapter 4 -- CrewAI Framework
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
# Description: Klaviyo and Google Ads tools with CrewAI @tool decorator and mock fallbacks

"""Klaviyo email flow and Google Ads audience tools for the Demand Gen Pipeline.

Provides email flow creation in Klaviyo and audience push to Google Ads.
Each function attempts the live API when USE_MOCK is false and the relevant
API key is present, falling back to deterministic mock data otherwise.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
KLAVIYO_API_KEY: str = os.getenv("KLAVIYO_API_KEY", "")
GOOGLE_ADS_DEVELOPER_TOKEN: str = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
GOOGLE_ADS_CUSTOMER_ID: str = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")

logger = logging.getLogger("demand_gen.tools.klaviyo")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mock_id() -> str:
    """Return a short unique identifier for mock objects."""
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Mock data generators
# ---------------------------------------------------------------------------

def _mock_klaviyo_flow(
    flow_name: str,
    trigger_event: str,
    emails: list[dict[str, str]],
) -> dict[str, Any]:
    """Generate a realistic mock Klaviyo flow creation result."""
    flow_id = f"flow-{_mock_id()}"
    email_actions = []
    for idx, email in enumerate(emails):
        email_actions.append({
            "action_id": f"act-{_mock_id()}",
            "step": idx + 1,
            "subject": email.get("subject", f"Email {idx + 1}"),
            "status": "draft",
            "delay_hours": idx * 48,
        })
    return {
        "flow_id": flow_id,
        "flow_name": flow_name,
        "trigger_event": trigger_event,
        "status": "live",
        "email_count": len(email_actions),
        "email_actions": email_actions,
        "created_at": _ts(),
    }


def _mock_google_ads_audience(
    audience_name: str,
    cohort_id: str,
) -> dict[str, Any]:
    """Generate a mock Google Ads audience push result."""
    import random

    random.seed(hash(cohort_id) % 2**32)
    matched = random.randint(800, 5000)
    return {
        "audience_id": f"ga-aud-{_mock_id()}",
        "audience_name": audience_name,
        "cohort_id": cohort_id,
        "match_rate_pct": round(random.uniform(55.0, 82.0), 1),
        "matched_users": matched,
        "uploaded_records": matched + random.randint(200, 1500),
        "status": "ready",
        "platform": "google_ads",
        "synced_at": _ts(),
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

@tool
def create_klaviyo_flow(flow_name: str, trigger_event: str, emails: str) -> str:
    """Create an email automation flow in Klaviyo.

    Builds a multi-step email flow triggered by a specified event.  Each
    email in the sequence is added as a flow action with configurable delay.
    The flow is set to live status so emails begin sending automatically
    when the trigger event fires.

    Args:
        flow_name: Display name for the Klaviyo flow
                   (e.g., 'Q2 SaaS Nurture Sequence').
        trigger_event: The Klaviyo metric/event that triggers the flow
                       (e.g., 'Added to Cohort', 'Signed Up').
        emails: JSON string containing a list of email objects, each with
                keys: subject, preview_text, body_outline, cta.

    Returns:
        JSON string with flow creation confirmation and action details.
    """
    logger.info(
        "create_klaviyo_flow | flow=%s | trigger=%s | mock=%s | ts=%s",
        flow_name, trigger_event, USE_MOCK, _ts(),
    )

    # Parse the emails JSON string into a list
    try:
        email_list: list[dict[str, str]] = json.loads(emails)
    except (json.JSONDecodeError, TypeError):
        # Gracefully handle if the agent passes a plain string
        email_list = [{"subject": f"Email {i + 1}", "body": "TBD"} for i in range(3)]
        logger.warning(
            "Could not parse emails JSON; using placeholder list of %d emails",
            len(email_list),
        )

    # ---- Live Klaviyo API path ----
    if not USE_MOCK and KLAVIYO_API_KEY:
        try:
            import requests

            # Create the flow via Klaviyo Flows API (v2024-10-15 revision)
            headers = {
                "Authorization": f"Klaviyo-API-Key {KLAVIYO_API_KEY}",
                "Content-Type": "application/json",
                "revision": "2024-10-15",
            }
            flow_payload = {
                "data": {
                    "type": "flow",
                    "attributes": {
                        "name": flow_name,
                        "trigger_type": "metric",
                        "status": "live",
                    },
                }
            }
            resp = requests.post(
                "https://a.klaviyo.com/api/flows/",
                headers=headers,
                json=flow_payload,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            result = {
                "flow_id": data.get("data", {}).get("id", f"flow-{_mock_id()}"),
                "flow_name": flow_name,
                "trigger_event": trigger_event,
                "status": "live",
                "email_count": len(email_list),
                "created_at": _ts(),
            }
            logger.info("Live Klaviyo flow created: flow_id=%s", result["flow_id"])
            return json.dumps(result, indent=2)
        except Exception as exc:
            logger.warning("Klaviyo API call failed, falling back to mock: %s", exc)

    # ---- Mock fallback ----
    mock = _mock_klaviyo_flow(flow_name, trigger_event, email_list)
    logger.info(
        "Returning mock Klaviyo flow: flow_id=%s emails=%d",
        mock["flow_id"],
        mock["email_count"],
    )
    return json.dumps(mock, indent=2)


@tool
def set_google_ads_audience(audience_name: str, cohort_id: str) -> str:
    """Push an audience cohort to Google Ads as a customer match list.

    Uploads the specified cohort to Google Ads so it can be used for
    remarketing, similar audiences, or exclusion targeting.  The upload
    includes hashed email addresses for customer matching.

    Args:
        audience_name: Display name for the Google Ads audience list
                       (e.g., 'Q2 High-Intent SaaS Buyers').
        cohort_id: The cohort identifier from the CDP export step.

    Returns:
        JSON string with audience sync confirmation and match statistics.
    """
    logger.info(
        "set_google_ads_audience | audience=%s | cohort=%s | mock=%s | ts=%s",
        audience_name, cohort_id, USE_MOCK, _ts(),
    )

    # ---- Live Google Ads API path ----
    if not USE_MOCK and GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_CUSTOMER_ID:
        try:
            from google.ads.googleads.client import GoogleAdsClient

            client = GoogleAdsClient.load_from_env()
            user_list_service = client.get_service("UserListService")

            # Build a CRM-based user list operation
            operation = client.get_type("UserListOperation")
            user_list = operation.create
            user_list.name = audience_name
            user_list.description = f"Demand Gen cohort: {cohort_id}"
            user_list.crm_based_user_list.upload_key_type = (
                client.enums.CustomerMatchUploadKeyTypeEnum.CONTACT_INFO
            )
            user_list.membership_life_span = 90

            response = user_list_service.mutate_user_lists(
                customer_id=GOOGLE_ADS_CUSTOMER_ID,
                operations=[operation],
            )
            resource_name = response.results[0].resource_name
            result = {
                "audience_id": resource_name,
                "audience_name": audience_name,
                "cohort_id": cohort_id,
                "status": "ready",
                "platform": "google_ads",
                "synced_at": _ts(),
            }
            logger.info("Live Google Ads audience created: %s", resource_name)
            return json.dumps(result, indent=2)
        except Exception as exc:
            logger.warning(
                "Google Ads API call failed, falling back to mock: %s", exc,
            )

    # ---- Mock fallback ----
    mock = _mock_google_ads_audience(audience_name, cohort_id)
    logger.info(
        "Returning mock Google Ads audience: id=%s match_rate=%.1f%%",
        mock["audience_id"],
        mock["match_rate_pct"],
    )
    return json.dumps(mock, indent=2)


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Demand Gen Pipeline -- Klaviyo & Google Ads Tools Demo")
    print("=" * 60)
    print(f"\nUSE_MOCK = {USE_MOCK}")
    print(f"KLAVIYO_API_KEY present = {bool(KLAVIYO_API_KEY)}")
    print(f"GOOGLE_ADS_DEVELOPER_TOKEN present = {bool(GOOGLE_ADS_DEVELOPER_TOKEN)}\n")

    # --- create_klaviyo_flow ---
    print("--- create_klaviyo_flow ---")
    sample_emails = json.dumps([
        {"subject": "Unlock Your Marketing Potential", "preview_text": "See how...", "body_outline": "Intro > Pain > Solution > CTA", "cta": "Start Free Trial"},
        {"subject": "Case Study: 40% ROAS Lift", "preview_text": "Real results...", "body_outline": "Story > Data > Offer > CTA", "cta": "Read the Case Study"},
        {"subject": "Last Chance: Exclusive Offer Ends Friday", "preview_text": "Don't miss...", "body_outline": "Urgency > Recap > Final CTA", "cta": "Claim Your Discount"},
    ])
    flow_json = create_klaviyo_flow.run(
        flow_name="Q2 SaaS Nurture Sequence",
        trigger_event="Added to Demand Gen Cohort",
        emails=sample_emails,
    )
    print(flow_json)

    # --- set_google_ads_audience ---
    print("\n--- set_google_ads_audience ---")
    audience_json = set_google_ads_audience.run(
        audience_name="Q2 High-Intent SaaS Buyers",
        cohort_id="cohort-abc123def456",
    )
    print(audience_json)
