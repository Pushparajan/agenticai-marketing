# =============================================================================
# tools.py
# Project: Customer Journey Digital Twin
# Chapter: 2 - OpenAI Agents SDK
# Description: HubSpot CRM read/write tools with mock fallbacks. Each tool
#              attempts a real HubSpot API call and falls back to realistic
#              mock data when USE_MOCK_APIS=true or the API key is absent.
# Author: Pushparajan Ramar
# =============================================================================
"""HubSpot CRM tools with realistic mock fallbacks."""
from __future__ import annotations

import json, logging, os, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

USE_MOCK: bool = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
HUBSPOT_API_KEY: str = os.getenv("HUBSPOT_API_KEY", "")
CONFIG_PATH: Path = Path(__file__).parent / "config.yaml"

logger = logging.getLogger("journey_twin.tools")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

_hubspot_client: Any = None


def _get_hubspot_client() -> Any:
    """Return a cached HubSpot API client or None if unavailable."""
    global _hubspot_client
    if _hubspot_client is not None:
        return _hubspot_client
    if not HUBSPOT_API_KEY:
        return None
    try:
        from hubspot import HubSpot  # type: ignore[import-untyped]
        _hubspot_client = HubSpot(access_token=HUBSPOT_API_KEY)
        return _hubspot_client
    except ImportError:
        logger.warning("hubspot-api-client not installed; using mock data.")
        return None


def _load_product_catalog() -> list[dict[str, Any]]:
    """Load product catalog from config.yaml."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh).get("product_catalog", [])


def _ts() -> str:
    """Return current UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Tool 1: get_contact_history
# ---------------------------------------------------------------------------
def get_contact_history(contact_id: str) -> dict[str, Any]:
    """Fetch contact timeline from HubSpot CRM.

    Args:
        contact_id: The HubSpot contact ID or internal reference.

    Returns:
        Dictionary with contact profile and timeline events.
    """
    logger.info("get_contact_history | contact_id=%s | ts=%s", contact_id, _ts())
    if not USE_MOCK:
        client = _get_hubspot_client()
        if client is not None:
            try:
                resp = client.crm.contacts.basic_api.get_by_id(
                    contact_id=contact_id,
                    properties=["email", "firstname", "lastname", "company",
                                "lifecyclestage", "hubspotscore"],
                )
                p = resp.properties
                engs = client.crm.objects.search_api.do_search(
                    object_type="engagements",
                    public_object_search_request={
                        "filter_groups": [{"filters": [{
                            "property_name": "associations.contact",
                            "operator": "EQ", "value": contact_id}]}],
                        "sorts": [{"propertyName": "hs_timestamp",
                                   "direction": "ASCENDING"}],
                        "limit": 20},
                )
                return {
                    "contact_id": contact_id, "email": p.get("email", ""),
                    "first_name": p.get("firstname", ""),
                    "last_name": p.get("lastname", ""),
                    "company": p.get("company", ""),
                    "lifecycle_stage": p.get("lifecyclestage", ""),
                    "lead_score": int(p.get("hubspotscore", 0)),
                    "timeline": [
                        {"event": e.properties.get("hs_engagement_type", "unknown"),
                         "detail": e.properties.get("hs_body_preview", ""),
                         "timestamp": e.properties.get("hs_timestamp", "")}
                        for e in engs.results],
                }
            except Exception as exc:
                logger.error("HubSpot error in get_contact_history: %s", exc)
    logger.info("Returning mock contact history for %s", contact_id)
    return {
        "contact_id": contact_id, "email": "sarah.chen@growthloop.io",
        "first_name": "Sarah", "last_name": "Chen",
        "company": "GrowthLoop Technologies",
        "lifecycle_stage": "opportunity", "lead_score": 82,
        "timeline": [
            {"event": "page_view", "timestamp": "2026-03-15T09:12:00Z",
             "detail": "Visited blog: '5 Signs Your MarTech Stack Is Broken'"},
            {"event": "form_submission", "timestamp": "2026-03-18T14:30:00Z",
             "detail": "Downloaded whitepaper: 'Unified Data Playbook'"},
            {"event": "email_open", "timestamp": "2026-03-22T08:45:00Z",
             "detail": "Opened nurture email: 'How CDP Saves 15 hrs/week'"},
            {"event": "webinar_attended", "timestamp": "2026-03-28T16:00:00Z",
             "detail": "Attended webinar: 'Attribution That Proves ROI'"},
            {"event": "demo_request", "timestamp": "2026-04-02T11:20:00Z",
             "detail": "Requested product demo via website form"},
        ],
    }


# ---------------------------------------------------------------------------
# Tool 2: get_product_catalogue
# ---------------------------------------------------------------------------
def get_product_catalogue() -> list[dict[str, Any]]:
    """Return the full product catalog from config.yaml.

    Returns:
        List of product dictionaries with SKU, name, pricing, and features.
    """
    logger.info("get_product_catalogue | ts=%s", _ts())
    catalog = _load_product_catalog()
    logger.info("Returning %d products", len(catalog))
    return catalog


# ---------------------------------------------------------------------------
# Tool 3: log_conversation
# ---------------------------------------------------------------------------
def log_conversation(contact_id: str, message: str, sentiment: str) -> dict[str, Any]:
    """Log a conversation interaction to HubSpot CRM.

    Args:
        contact_id: The HubSpot contact ID.
        message: The conversation message to log.
        sentiment: Detected sentiment (positive, neutral, negative).

    Returns:
        Confirmation dictionary with log ID and timestamp.
    """
    logger.info("log_conversation | contact=%s sentiment=%s | ts=%s",
                contact_id, sentiment, _ts())
    if not USE_MOCK:
        client = _get_hubspot_client()
        if client is not None:
            try:
                eng = client.crm.objects.notes.basic_api.create(
                    simple_public_object_input_for_create={
                        "properties": {"hs_timestamp": _ts(),
                                       "hs_note_body": f"[{sentiment.upper()}] {message}"},
                        "associations": [{"to": {"id": contact_id}, "types": [{
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 202}]}]})
                return {"status": "logged", "log_id": eng.id,
                        "contact_id": contact_id, "sentiment": sentiment,
                        "message_preview": message[:80], "logged_at": _ts()}
            except Exception as exc:
                logger.error("HubSpot error in log_conversation: %s", exc)
    return {"status": "logged", "log_id": str(uuid.uuid4()),
            "contact_id": contact_id, "sentiment": sentiment,
            "message_preview": message[:80], "logged_at": _ts()}


# ---------------------------------------------------------------------------
# Tool 4: check_pricing_request
# ---------------------------------------------------------------------------
PRICING_SIGNALS: list[str] = [
    "pricing", "price", "cost", "how much", "quote", "discount",
    "budget", "subscription", "per month", "per year", "annual fee",
    "payment plan", "total cost", "enterprise pricing",
    "negotiate", "deal", "proposal", "contract value",
]


def check_pricing_request(message: str) -> dict[str, Any]:
    """Detect pricing inquiries for human-in-the-loop escalation.

    Args:
        message: The prospect's message text to analyze.

    Returns:
        Dict with detection result, matched signals, and escalation flag.
    """
    logger.info("check_pricing_request | msg_len=%d | ts=%s", len(message), _ts())
    lower = message.lower()
    matched = [s for s in PRICING_SIGNALS if s in lower]
    is_pricing = len(matched) > 0
    result: dict[str, Any] = {
        "is_pricing_request": is_pricing, "matched_signals": matched,
        "confidence": round(min(len(matched) / 3.0, 1.0), 2),
        "escalation_required": is_pricing, "checked_at": _ts(),
    }
    if is_pricing:
        result["escalation_message"] = (
            "Pricing inquiry detected. Flagging for sales representative "
            "review. A human agent will follow up with a custom quote.")
        logger.info("Pricing DETECTED — signals: %s", matched)
    else:
        logger.info("No pricing signals found.")
    return result


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Customer Journey Digital Twin — Tools Demo")
    print("=" * 60, f"\nUSE_MOCK={USE_MOCK}  HUBSPOT_KEY={'set' if HUBSPOT_API_KEY else 'unset'}\n")

    print("--- get_contact_history ---")
    print(json.dumps(get_contact_history("mock-001"), indent=2))

    print("\n--- get_product_catalogue ---")
    for p in get_product_catalogue():
        print(f"  {p['sku']}: {p['name']} ({p['price_range']})")

    print("\n--- log_conversation ---")
    print(json.dumps(log_conversation("mock-001", "Impressed by the demo!", "positive"), indent=2))

    print("\n--- check_pricing_request ---")
    for msg in ["Tell me about attribution features.",
                 "How much does the Enterprise Suite cost per month?"]:
        r = check_pricing_request(msg)
        tag = "PRICING" if r["is_pricing_request"] else "general"
        print(f"  [{tag}] {msg}")
