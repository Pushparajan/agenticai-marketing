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

import json, logging, os
from datetime import datetime, timezone
from typing import Any

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_NPS: dict[str, dict[str, Any]] = {
    "CUST-001": dict(customer_id="CUST-001", current_nps=4, previous_nps=8,
        nps_trend="declining", category="detractor", survey_date="2026-03-15",
        verbatim="The platform keeps crashing. We barely use it anymore."),
    "CUST-002": dict(customer_id="CUST-002", current_nps=6, previous_nps=8,
        nps_trend="declining", category="passive", survey_date="2026-03-20",
        verbatim="We are evaluating alternatives. Your competitor has better integrations."),
    "CUST-003": dict(customer_id="CUST-003", current_nps=7, previous_nps=9,
        nps_trend="declining", category="passive", survey_date="2026-03-18",
        verbatim="The product is okay but we are not seeing the ROI we expected."),
}

_SENTIMENT: dict[str, dict[str, Any]] = {
    "CUST-001": dict(customer_id="CUST-001", period_days=90,
        overall_sentiment="negative", sentiment_score=-0.65,
        trend_direction="worsening",
        weekly_scores=[
            {"week": "2026-W04", "score": -0.20}, {"week": "2026-W06", "score": -0.50},
            {"week": "2026-W08", "score": -0.72}, {"week": "2026-W10", "score": -0.75},
        ],
        key_themes=["product_stability", "slow_support_response", "missing_features"]),
    "CUST-002": dict(customer_id="CUST-002", period_days=90,
        overall_sentiment="mixed", sentiment_score=-0.25,
        trend_direction="stable_negative",
        weekly_scores=[
            {"week": "2026-W06", "score": -0.10}, {"week": "2026-W08", "score": -0.30},
        ],
        key_themes=["competitor_comparison", "integration_gaps"]),
    "CUST-003": dict(customer_id="CUST-003", period_days=90,
        overall_sentiment="neutral", sentiment_score=-0.10,
        trend_direction="slightly_declining",
        weekly_scores=[
            {"week": "2026-W06", "score": 0.10}, {"week": "2026-W08", "score": -0.15},
        ],
        key_themes=["roi_uncertainty", "underutilization"]),
}

_TICKETS: dict[str, dict[str, Any]] = {
    "CUST-001": dict(customer_id="CUST-001", total_tickets_30d=5,
        negative_tickets=4, neutral_tickets=1, positive_tickets=0,
        consecutive_negative=4, escalated=True,
        tickets=[
            dict(id="TKT-1001", subject="Dashboard keeps timing out",
                 sentiment="negative", created="2026-03-01"),
            dict(id="TKT-1002", subject="Data export broken again",
                 sentiment="negative", created="2026-03-05"),
            dict(id="TKT-1003", subject="API rate limits too low",
                 sentiment="neutral", created="2026-03-08"),
            dict(id="TKT-1004", subject="Still waiting on fix for TKT-1001",
                 sentiment="negative", created="2026-03-12"),
            dict(id="TKT-1005", subject="Considering alternatives due to reliability",
                 sentiment="negative", created="2026-03-18"),
        ]),
    "CUST-002": dict(customer_id="CUST-002", total_tickets_30d=2,
        negative_tickets=1, neutral_tickets=1, positive_tickets=0,
        consecutive_negative=1, escalated=False,
        tickets=[
            dict(id="TKT-2001", subject="Competitor X has Salesforce integration",
                 sentiment="negative", created="2026-03-10"),
            dict(id="TKT-2002", subject="Feature request: CRM sync",
                 sentiment="neutral", created="2026-03-22"),
        ]),
    "CUST-003": dict(customer_id="CUST-003", total_tickets_30d=3,
        negative_tickets=3, neutral_tickets=0, positive_tickets=0,
        consecutive_negative=3, escalated=False,
        tickets=[
            dict(id="TKT-3001", subject="Report numbers do not match our internal data",
                 sentiment="negative", created="2026-03-05"),
            dict(id="TKT-3002", subject="Training resources are outdated",
                 sentiment="negative", created="2026-03-12"),
            dict(id="TKT-3003", subject="Need clearer ROI dashboard",
                 sentiment="negative", created="2026-03-19"),
        ]),
}

# ---------------------------------------------------------------------------
# Real API helper
# ---------------------------------------------------------------------------

def _api_get(url_env: str, default_url: str, path: str,
             key_env: str, params: dict | None = None) -> dict[str, Any]:
    """Shared GET helper for NPS / sentiment / helpdesk APIs."""
    import httpx
    url = os.getenv(url_env, default_url)
    key = os.getenv(key_env, "")
    resp = httpx.get(f"{url}{path}", params=params,
                     headers={"Authorization": f"Bearer {key}"}, timeout=10)
    resp.raise_for_status()
    return resp.json()

# ---------------------------------------------------------------------------
# Defaults for unknown customers
# ---------------------------------------------------------------------------

def _def_nps(cid: str) -> dict[str, Any]:
    return dict(customer_id=cid, current_nps=8, previous_nps=8,
                nps_trend="stable", category="passive",
                survey_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                verbatim="")

def _def_sentiment(cid: str, days: int) -> dict[str, Any]:
    return dict(customer_id=cid, period_days=days, overall_sentiment="neutral",
                sentiment_score=0.0, trend_direction="stable",
                weekly_scores=[], key_themes=[])

def _def_tickets(cid: str) -> dict[str, Any]:
    return dict(customer_id=cid, total_tickets_30d=0, negative_tickets=0,
                neutral_tickets=0, positive_tickets=0,
                consecutive_negative=0, escalated=False, tickets=[])

# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def get_nps_score(customer_id: str) -> str:
    """Return the latest NPS score and survey details for a customer.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON with current_nps, previous_nps, trend, category, verbatim.
    """
    logger.info("get_nps_score(%s) mock=%s", customer_id, USE_MOCK)
    if USE_MOCK:
        result = _NPS.get(customer_id, _def_nps(customer_id))
    else:
        try:
            data = _api_get("NPS_API_URL", "https://api.delighted.com/v1",
                            "/survey_responses", "NPS_API_KEY",
                            {"customer_id": customer_id, "per_page": 2, "order": "desc"})
            if data:
                cur = data[0].get("score", 0)
                prev = data[1].get("score", cur) if len(data) > 1 else cur
                trend = "declining" if cur < prev else ("improving" if cur > prev else "stable")
                cat = "promoter" if cur >= 9 else ("passive" if cur >= 7 else "detractor")
                result = dict(customer_id=customer_id, current_nps=cur,
                              previous_nps=prev, nps_trend=trend, category=cat,
                              survey_date=data[0].get("created_at", ""),
                              verbatim=data[0].get("comment", ""))
            else:
                result = _def_nps(customer_id)
        except Exception as exc:
            logger.warning("NPS API error: %s — mock", exc)
            result = _NPS.get(customer_id, _def_nps(customer_id))

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)


def get_sentiment_trend(customer_id: str, days: int) -> str:
    """Return the sentiment trend for a customer over N days.

    Args:
        customer_id: Unique customer identifier.
        days: Look-back period in days.

    Returns:
        JSON with overall sentiment, weekly scores, and key themes.
    """
    logger.info("get_sentiment_trend(%s, %d) mock=%s", customer_id, days, USE_MOCK)
    if USE_MOCK:
        result = _SENTIMENT.get(customer_id, _def_sentiment(customer_id, days))
    else:
        try:
            result = _api_get("SENTIMENT_API_URL",
                              "https://analytics.internal/api/v1/sentiment",
                              "/trend", "SENTIMENT_API_KEY",
                              {"customer_id": customer_id, "days": days})
        except Exception as exc:
            logger.warning("Sentiment API error: %s — mock", exc)
            result = _SENTIMENT.get(customer_id, _def_sentiment(customer_id, days))

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)


def get_support_ticket_sentiment(customer_id: str) -> str:
    """Return support-ticket sentiment analysis for the last 30 days.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON with ticket counts, sentiment breakdown, consecutive-negative
        streak, and individual ticket details.
    """
    logger.info("get_support_ticket_sentiment(%s) mock=%s", customer_id, USE_MOCK)
    if USE_MOCK:
        result = _TICKETS.get(customer_id, _def_tickets(customer_id))
    else:
        try:
            result = _api_get("HELPDESK_API_URL",
                              "https://company.zendesk.com/api/v2",
                              "/tickets", "HELPDESK_API_KEY",
                              {"customer_id": customer_id})
        except Exception as exc:
            logger.warning("Helpdesk API error: %s — mock", exc)
            result = _TICKETS.get(customer_id, _def_tickets(customer_id))

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)
