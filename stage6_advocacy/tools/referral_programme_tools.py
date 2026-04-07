# File      : referral_programme_tools.py
# Stage     : 6 — Advocacy
# Chapter   : 12
# Framework : MCP + OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Referral-programme tools for the Advocacy stage.

Manages referral programme enrolment, link generation, and pipeline
tracking.  Supports tiered programmes (silver / gold / platinum).
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

VALID_TIERS = {"silver", "gold", "platinum"}

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_REFERRAL_DB: dict[str, dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "programme_tier": "gold",
        "referral_link": "https://refer.example.com/sarah-tc-ab12",
        "enrolled_at": "2026-01-10T09:00:00Z",
        "referrals": [
            {
                "referred_email": "nadia@acme.com",
                "status": "converted",
                "deal_value": 28000.00,
                "reward_credited": True,
            },
            {
                "referred_email": "lee@widgets.io",
                "status": "in_trial",
                "deal_value": None,
                "reward_credited": False,
            },
        ],
    },
}

_MOCK_LINKS: dict[str, str] = {
    "CUST-001": "https://refer.example.com/sarah-tc-ab12",
}

# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------


def trigger_referral_programme(customer_id: str, programme_tier: str) -> str:
    """Enrol a customer in the referral programme at the given tier.

    Args:
        customer_id: Unique customer identifier.
        programme_tier: One of 'silver', 'gold', or 'platinum'.

    Returns:
        JSON string with enrolment confirmation or error.
    """
    logger.info(
        "trigger_referral_programme %s tier=%s (mock=%s)",
        customer_id, programme_tier, USE_MOCK,
    )

    tier = programme_tier.lower().strip()
    if tier not in VALID_TIERS:
        return json.dumps({
            "error": f"Invalid tier '{programme_tier}'. Must be one of {sorted(VALID_TIERS)}."
        })

    # Check if already enrolled
    if USE_MOCK:
        existing = _MOCK_REFERRAL_DB.get(customer_id)
        if existing:
            return json.dumps({
                "status": "already_enrolled",
                "customer_id": customer_id,
                "current_tier": existing["programme_tier"],
                "referral_link": existing["referral_link"],
                "message": "Customer is already enrolled. Use upgrade flow to change tier.",
            })

    referral_code = uuid.uuid4().hex[:8]
    referral_link = f"https://refer.example.com/{referral_code}"
    enrolment = {
        "enrolment_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "programme_tier": tier,
        "referral_link": referral_link,
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "rewards_summary": _tier_rewards(tier),
    }

    if USE_MOCK:
        _MOCK_REFERRAL_DB[customer_id] = enrolment
        _MOCK_LINKS[customer_id] = referral_link
        return json.dumps(enrolment, default=str)

    try:
        import httpx
        api_url = os.getenv("REFERRAL_API_URL", "https://api.referralrock.com/v1")
        api_key = os.getenv("REFERRAL_API_KEY", "")
        resp = httpx.post(
            f"{api_url}/members",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "customer_id": customer_id,
                "tier": tier,
            },
            timeout=10,
        )
        resp.raise_for_status()
        enrolment["api_response"] = resp.json()
        return json.dumps(enrolment, default=str)
    except Exception as exc:
        logger.error("Referral programme enrolment error: %s", exc)
        return json.dumps({"error": str(exc)})


def get_referral_pipeline(customer_id: str) -> str:
    """Retrieve the referral pipeline for an enrolled customer.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON string with referral pipeline details.
    """
    logger.info("get_referral_pipeline %s (mock=%s)", customer_id, USE_MOCK)

    if USE_MOCK:
        record = _MOCK_REFERRAL_DB.get(customer_id)
        if record is None:
            return json.dumps({
                "customer_id": customer_id,
                "status": "not_enrolled",
                "referrals": [],
            })

        referrals = record.get("referrals", [])
        converted = sum(1 for r in referrals if r["status"] == "converted")
        pipeline_value = sum(
            r.get("deal_value", 0) or 0 for r in referrals
        )
        return json.dumps({
            "customer_id": customer_id,
            "programme_tier": record.get("programme_tier", "unknown"),
            "total_referrals": len(referrals),
            "converted": converted,
            "in_pipeline": len(referrals) - converted,
            "pipeline_value": pipeline_value,
            "referrals": referrals,
        }, default=str)

    try:
        import httpx
        api_url = os.getenv("REFERRAL_API_URL", "https://api.referralrock.com/v1")
        api_key = os.getenv("REFERRAL_API_KEY", "")
        resp = httpx.get(
            f"{api_url}/members/{customer_id}/referrals",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), default=str)
    except Exception as exc:
        logger.error("Referral pipeline error: %s", exc)
        return json.dumps({"error": str(exc)})


def create_referral_link(customer_id: str) -> str:
    """Generate a unique referral link for a customer.

    If the customer already has a link, returns the existing one.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON string with the referral link.
    """
    logger.info("create_referral_link %s (mock=%s)", customer_id, USE_MOCK)

    if USE_MOCK:
        existing = _MOCK_LINKS.get(customer_id)
        if existing:
            return json.dumps({
                "customer_id": customer_id,
                "referral_link": existing,
                "is_new": False,
            })

        new_code = uuid.uuid4().hex[:8]
        link = f"https://refer.example.com/{new_code}"
        _MOCK_LINKS[customer_id] = link
        return json.dumps({
            "customer_id": customer_id,
            "referral_link": link,
            "is_new": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    try:
        import httpx
        api_url = os.getenv("REFERRAL_API_URL", "https://api.referralrock.com/v1")
        api_key = os.getenv("REFERRAL_API_KEY", "")
        resp = httpx.post(
            f"{api_url}/members/{customer_id}/link",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), default=str)
    except Exception as exc:
        logger.error("Referral link creation error: %s", exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _tier_rewards(tier: str) -> dict[str, Any]:
    """Return the reward structure for a programme tier."""
    rewards = {
        "silver": {
            "per_referral_credit": 250,
            "currency": "USD",
            "bonus_at_5": 500,
            "description": "USD 250 credit per converted referral, USD 500 bonus at 5 referrals.",
        },
        "gold": {
            "per_referral_credit": 500,
            "currency": "USD",
            "bonus_at_5": 1500,
            "description": "USD 500 credit per converted referral, USD 1500 bonus at 5 referrals.",
        },
        "platinum": {
            "per_referral_credit": 1000,
            "currency": "USD",
            "bonus_at_5": 3000,
            "co_marketing": True,
            "description": (
                "USD 1000 credit per converted referral, USD 3000 bonus at 5 "
                "referrals, plus co-marketing opportunities."
            ),
        },
    }
    return rewards.get(tier, rewards["silver"])
