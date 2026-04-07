# File      : nps_tools.py
# Stage     : 6 — Advocacy
# Chapter   : 12
# Framework : MCP + OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
NPS tools for the Advocacy stage.
Retrieve scores, identify advocates, analyse distributions, trigger follow-ups.
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

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_NPS: dict[str, dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "contact_email": "sarah@techcorp.com",
        "nps_score": 10,
        "ltv": 185000.00,
        "segment": "enterprise",
        "last_survey_date": "2026-03-15",
        "comment": "Incredible platform — transformed our pipeline.",
        "recent_expansion": False,
        "active_community": True,
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "contact_email": "james@growthio.com",
        "nps_score": 8,
        "ltv": 62000.00,
        "segment": "mid-market",
        "last_survey_date": "2026-03-20",
        "comment": "Great product, onboarding could be smoother.",
        "recent_expansion": True,
        "active_community": False,
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "contact_email": "mei@communityplus.org",
        "nps_score": 9,
        "ltv": 41000.00,
        "segment": "mid-market",
        "last_survey_date": "2026-03-22",
        "comment": "Love the community features, very engaged team.",
        "recent_expansion": False,
        "active_community": True,
    },
    "CUST-004": {
        "customer_id": "CUST-004",
        "contact_email": "pat@smallbiz.co",
        "nps_score": 6,
        "ltv": 12000.00,
        "segment": "smb",
        "last_survey_date": "2026-02-28",
        "comment": "Decent but missing some integrations.",
        "recent_expansion": False,
        "active_community": False,
    },
}

_MOCK_FOLLOWUP_LOG: list[dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------

def _fetch_nps_real(customer_id: str) -> dict[str, Any]:
    """Fetch NPS data from a survey platform (e.g. Delighted)."""
    import httpx

    api_url = os.getenv("NPS_API_URL", "https://api.delighted.com/v1")
    api_key = os.getenv("NPS_API_KEY", "")

    resp = httpx.get(
        f"{api_url}/survey_responses.json",
        params={"customer_id": customer_id, "per_page": 1},
        auth=(api_key, ""),
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return {"error": f"No NPS record for {customer_id}"}
    latest = data[0]
    return {
        "customer_id": customer_id,
        "nps_score": latest.get("score", 0),
        "comment": latest.get("comment", ""),
        "last_survey_date": latest.get("created_at", ""),
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------


def get_nps_score(customer_id: str) -> str:
    """Return the latest NPS score and profile for a customer.

    Args:
        customer_id: Unique customer identifier (e.g. 'CUST-001').

    Returns:
        JSON string with NPS score, segment, LTV, and survey metadata.
    """
    logger.info("get_nps_score called for %s (mock=%s)", customer_id, USE_MOCK)

    if USE_MOCK:
        record = _MOCK_NPS.get(customer_id)
        if record is None:
            return json.dumps({"error": f"Customer {customer_id} not found"})
        return json.dumps(record, default=str)

    try:
        result = _fetch_nps_real(customer_id)
        return json.dumps(result, default=str)
    except Exception as exc:
        logger.error("NPS API error: %s", exc)
        return json.dumps({"error": str(exc)})


def get_nps_distribution() -> str:
    """Return the NPS score distribution across all customers.

    Returns:
        JSON string with promoters/passives/detractors counts and overall NPS.
    """
    logger.info("get_nps_distribution called (mock=%s)", USE_MOCK)

    if USE_MOCK:
        scores = [r["nps_score"] for r in _MOCK_NPS.values()]
    else:
        try:
            import httpx
            api_url = os.getenv("NPS_API_URL", "https://api.delighted.com/v1")
            api_key = os.getenv("NPS_API_KEY", "")
            resp = httpx.get(
                f"{api_url}/metrics.json",
                auth=(api_key, ""),
                timeout=10,
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), default=str)
        except Exception as exc:
            logger.error("NPS distribution API error: %s", exc)
            return json.dumps({"error": str(exc)})

    promoters = sum(1 for s in scores if s >= 9)
    passives = sum(1 for s in scores if 7 <= s <= 8)
    detractors = sum(1 for s in scores if s <= 6)
    total = len(scores)
    nps = int(((promoters - detractors) / total) * 100) if total else 0

    distribution = {
        "total_respondents": total,
        "promoters": promoters,
        "passives": passives,
        "detractors": detractors,
        "nps": nps,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(distribution, default=str)


def identify_advocates(min_nps: int, min_ltv: float) -> str:
    """Identify customers who qualify as advocates based on NPS and LTV.

    Args:
        min_nps: Minimum NPS score to qualify (e.g. 9).
        min_ltv: Minimum lifetime value in USD (e.g. 50000.0).

    Returns:
        JSON string with list of qualifying advocate profiles.
    """
    logger.info(
        "identify_advocates called (min_nps=%d, min_ltv=%.0f, mock=%s)",
        min_nps, min_ltv, USE_MOCK,
    )

    if USE_MOCK:
        advocates = [
            r for r in _MOCK_NPS.values()
            if r["nps_score"] >= min_nps and r["ltv"] >= min_ltv
        ]
        return json.dumps(
            {"advocates": advocates, "count": len(advocates)},
            default=str,
        )

    try:
        import httpx
        api_url = os.getenv("CRM_API_URL", "https://api.hubspot.com/crm/v3")
        api_key = os.getenv("CRM_API_KEY", "")
        resp = httpx.post(
            f"{api_url}/objects/contacts/search",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "filterGroups": [{
                    "filters": [
                        {"propertyName": "nps_score", "operator": "GTE",
                         "value": str(min_nps)},
                        {"propertyName": "ltv", "operator": "GTE",
                         "value": str(min_ltv)},
                    ]
                }]
            },
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return json.dumps({"advocates": results, "count": len(results)}, default=str)
    except Exception as exc:
        logger.error("CRM advocate search error: %s", exc)
        return json.dumps({"error": str(exc)})


def send_nps_followup(customer_id: str, nps_score: int) -> str:
    """Send an appropriate NPS follow-up based on the score.

    For promoters (9-10): thank-you + advocacy ask.
    For passives (7-8): improvement commitment.
    For detractors (0-6): escalation to CS manager.

    Args:
        customer_id: Customer identifier.
        nps_score: The NPS score that was given.

    Returns:
        JSON string confirming the follow-up action taken.
    """
    logger.info(
        "send_nps_followup for %s score=%d (mock=%s)",
        customer_id, nps_score, USE_MOCK,
    )

    if nps_score >= 9:
        action = "promoter_thank_you"
        message = (
            "Thank you for your outstanding feedback! We'd love to explore "
            "ways you can share your success story with peers."
        )
    elif nps_score >= 7:
        action = "passive_improvement"
        message = (
            "Thank you for your feedback. We're committed to making your "
            "experience even better — your CSM will follow up shortly."
        )
    else:
        action = "detractor_escalation"
        message = (
            "We're sorry to hear about your experience. A senior CS manager "
            "has been notified and will reach out within 24 hours."
        )

    followup_record = {
        "followup_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "nps_score": nps_score,
        "action": action,
        "message": message,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    if USE_MOCK:
        _MOCK_FOLLOWUP_LOG.append(followup_record)
        return json.dumps(followup_record, default=str)

    try:
        import httpx
        webhook_url = os.getenv("NPS_FOLLOWUP_WEBHOOK", "")
        resp = httpx.post(webhook_url, json=followup_record, timeout=10)
        resp.raise_for_status()
        followup_record["webhook_status"] = resp.status_code
        return json.dumps(followup_record, default=str)
    except Exception as exc:
        logger.error("NPS follow-up webhook error: %s", exc)
        followup_record["webhook_error"] = str(exc)
        return json.dumps(followup_record, default=str)
