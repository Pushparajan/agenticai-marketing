# File      : nps_sentiment_tools.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
NPS and sentiment analysis tools.

Provides functions to retrieve NPS scores, sentiment trends, and
support-ticket sentiment for retention analysis.
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
        "current_nps": 4,
        "previous_nps": 8,
        "nps_trend": "declining",
        "category": "detractor",
        "survey_date": "2026-03-15",
        "verbatim": "The platform keeps crashing. We barely use it anymore.",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "current_nps": 6,
        "previous_nps": 8,
        "nps_trend": "declining",
        "category": "passive",
        "survey_date": "2026-03-20",
        "verbatim": "We are evaluating alternatives. Your competitor has better integrations.",
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "current_nps": 7,
        "previous_nps": 9,
        "nps_trend": "declining",
        "category": "passive",
        "survey_date": "2026-03-18",
        "verbatim": "The product is okay but we are not seeing the ROI we expected.",
    },
}

_MOCK_SENTIMENT_TRENDS: dict[str, dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "period_days": 90,
        "overall_sentiment": "negative",
        "sentiment_score": -0.65,
        "trend_direction": "worsening",
        "weekly_scores": [
            {"week": "2026-W04", "score": -0.20},
            {"week": "2026-W05", "score": -0.35},
            {"week": "2026-W06", "score": -0.50},
            {"week": "2026-W07", "score": -0.60},
            {"week": "2026-W08", "score": -0.72},
            {"week": "2026-W09", "score": -0.68},
            {"week": "2026-W10", "score": -0.75},
        ],
        "key_themes": ["product_stability", "slow_support_response", "missing_features"],
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "period_days": 90,
        "overall_sentiment": "mixed",
        "sentiment_score": -0.25,
        "trend_direction": "stable_negative",
        "weekly_scores": [
            {"week": "2026-W06", "score": -0.10},
            {"week": "2026-W07", "score": -0.20},
            {"week": "2026-W08", "score": -0.30},
            {"week": "2026-W09", "score": -0.25},
        ],
        "key_themes": ["competitor_comparison", "integration_gaps"],
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "period_days": 90,
        "overall_sentiment": "neutral",
        "sentiment_score": -0.10,
        "trend_direction": "slightly_declining",
        "weekly_scores": [
            {"week": "2026-W06", "score": 0.10},
            {"week": "2026-W07", "score": 0.00},
            {"week": "2026-W08", "score": -0.15},
            {"week": "2026-W09", "score": -0.12},
        ],
        "key_themes": ["roi_uncertainty", "underutilization"],
    },
}

_MOCK_TICKET_SENTIMENT: dict[str, dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "total_tickets_30d": 5,
        "negative_tickets": 4,
        "neutral_tickets": 1,
        "positive_tickets": 0,
        "consecutive_negative": 4,
        "escalated": True,
        "tickets": [
            {"id": "TKT-1001", "subject": "Dashboard keeps timing out", "sentiment": "negative", "created": "2026-03-01"},
            {"id": "TKT-1002", "subject": "Data export broken again", "sentiment": "negative", "created": "2026-03-05"},
            {"id": "TKT-1003", "subject": "API rate limits too low", "sentiment": "neutral", "created": "2026-03-08"},
            {"id": "TKT-1004", "subject": "Still waiting on fix for TKT-1001", "sentiment": "negative", "created": "2026-03-12"},
            {"id": "TKT-1005", "subject": "Considering alternatives due to reliability", "sentiment": "negative", "created": "2026-03-18"},
        ],
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "total_tickets_30d": 2,
        "negative_tickets": 1,
        "neutral_tickets": 1,
        "positive_tickets": 0,
        "consecutive_negative": 1,
        "escalated": False,
        "tickets": [
            {"id": "TKT-2001", "subject": "Competitor X has Salesforce integration", "sentiment": "negative", "created": "2026-03-10"},
            {"id": "TKT-2002", "subject": "Feature request: CRM sync", "sentiment": "neutral", "created": "2026-03-22"},
        ],
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "total_tickets_30d": 3,
        "negative_tickets": 3,
        "neutral_tickets": 0,
        "positive_tickets": 0,
        "consecutive_negative": 3,
        "escalated": False,
        "tickets": [
            {"id": "TKT-3001", "subject": "Report numbers do not match our internal data", "sentiment": "negative", "created": "2026-03-05"},
            {"id": "TKT-3002", "subject": "Training resources are outdated", "sentiment": "negative", "created": "2026-03-12"},
            {"id": "TKT-3003", "subject": "Need clearer ROI dashboard", "sentiment": "negative", "created": "2026-03-19"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------


def _fetch_nps_real(customer_id: str) -> dict[str, Any]:
    """Fetch NPS from a real survey platform (e.g. Delighted, Qualtrics)."""
    import httpx

    api_url = os.getenv("NPS_API_URL", "https://api.delighted.com/v1")
    api_key = os.getenv("NPS_API_KEY", "")
    try:
        resp = httpx.get(
            f"{api_url}/survey_responses",
            params={"customer_id": customer_id, "per_page": 2, "order": "desc"},
            headers={"Authorization": f"Basic {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            current = data[0].get("score", 0)
            previous = data[1].get("score", current) if len(data) > 1 else current
            trend = "declining" if current < previous else ("improving" if current > previous else "stable")
            category = "promoter" if current >= 9 else ("passive" if current >= 7 else "detractor")
            return {
                "customer_id": customer_id,
                "current_nps": current,
                "previous_nps": previous,
                "nps_trend": trend,
                "category": category,
                "survey_date": data[0].get("created_at", ""),
                "verbatim": data[0].get("comment", ""),
            }
    except Exception as exc:
        logger.warning("NPS API error for %s: %s — falling back to mock", customer_id, exc)

    return _MOCK_NPS.get(customer_id, _default_nps(customer_id))


def _fetch_sentiment_real(customer_id: str, days: int) -> dict[str, Any]:
    """Fetch sentiment trend from an analytics API."""
    import httpx

    api_url = os.getenv("SENTIMENT_API_URL", "https://analytics.internal/api/v1/sentiment")
    api_key = os.getenv("SENTIMENT_API_KEY", "")
    try:
        resp = httpx.get(
            f"{api_url}/trend",
            params={"customer_id": customer_id, "days": days},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Sentiment API error: %s — using mock", exc)
        return _MOCK_SENTIMENT_TRENDS.get(customer_id, _default_sentiment(customer_id, days))


def _fetch_ticket_sentiment_real(customer_id: str) -> dict[str, Any]:
    """Fetch support-ticket sentiment from a helpdesk API (e.g. Zendesk)."""
    import httpx

    api_url = os.getenv("HELPDESK_API_URL", "https://company.zendesk.com/api/v2")
    api_key = os.getenv("HELPDESK_API_KEY", "")
    try:
        resp = httpx.get(
            f"{api_url}/tickets",
            params={"customer_id": customer_id, "sort_by": "created_at", "sort_order": "desc"},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Helpdesk API error: %s — using mock", exc)
        return _MOCK_TICKET_SENTIMENT.get(customer_id, _default_tickets(customer_id))


# ---------------------------------------------------------------------------
# Defaults for unknown customers
# ---------------------------------------------------------------------------


def _default_nps(customer_id: str) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "current_nps": 8,
        "previous_nps": 8,
        "nps_trend": "stable",
        "category": "passive",
        "survey_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "verbatim": "",
    }


def _default_sentiment(customer_id: str, days: int) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "period_days": days,
        "overall_sentiment": "neutral",
        "sentiment_score": 0.0,
        "trend_direction": "stable",
        "weekly_scores": [],
        "key_themes": [],
    }


def _default_tickets(customer_id: str) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "total_tickets_30d": 0,
        "negative_tickets": 0,
        "neutral_tickets": 0,
        "positive_tickets": 0,
        "consecutive_negative": 0,
        "escalated": False,
        "tickets": [],
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------


def get_nps_score(customer_id: str) -> str:
    """Return the latest NPS score and survey details for a customer.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON string with current_nps, previous_nps, trend, category,
        and verbatim feedback.
    """
    logger.info("get_nps_score(%s) mock=%s", customer_id, USE_MOCK)

    if USE_MOCK:
        result = _MOCK_NPS.get(customer_id, _default_nps(customer_id))
    else:
        result = _fetch_nps_real(customer_id)

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)


def get_sentiment_trend(customer_id: str, days: int) -> str:
    """Return the sentiment trend for a customer over N days.

    Args:
        customer_id: Unique customer identifier.
        days: Look-back period in days.

    Returns:
        JSON string with overall sentiment, weekly scores, and key themes.
    """
    logger.info("get_sentiment_trend(%s, %d) mock=%s", customer_id, days, USE_MOCK)

    if USE_MOCK:
        result = _MOCK_SENTIMENT_TRENDS.get(customer_id, _default_sentiment(customer_id, days))
    else:
        result = _fetch_sentiment_real(customer_id, days)

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)


def get_support_ticket_sentiment(customer_id: str) -> str:
    """Return support-ticket sentiment analysis for the last 30 days.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON string with ticket counts, sentiment breakdown,
        consecutive-negative streak, and individual ticket details.
    """
    logger.info("get_support_ticket_sentiment(%s) mock=%s", customer_id, USE_MOCK)

    if USE_MOCK:
        result = _MOCK_TICKET_SENTIMENT.get(customer_id, _default_tickets(customer_id))
    else:
        result = _fetch_ticket_sentiment_real(customer_id)

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)
