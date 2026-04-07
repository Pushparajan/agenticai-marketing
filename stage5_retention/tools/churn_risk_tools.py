# File      : churn_risk_tools.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Churn-risk scoring and prediction tools.

Provides functions to assess customer churn risk, predict churn probability
over a time window, retrieve similar churned customers, and look up
historically successful retention plays.
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

_MOCK_CHURN_PROFILES: dict[str, dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "risk_level": "critical",
        "risk_score": 92,
        "primary_driver": "usage_gap",
        "secondary_driver": "support",
        "active_features_pct": 0.28,
        "baseline_features_pct": 0.85,
        "nps_current": 4,
        "nps_previous": 8,
        "days_to_renewal": 45,
        "support_tickets_30d": 5,
        "negative_tickets_streak": 4,
        "last_login_days_ago": 14,
        "health_score": 22,
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "risk_level": "high",
        "risk_score": 78,
        "primary_driver": "competitor",
        "secondary_driver": "price",
        "active_features_pct": 0.55,
        "baseline_features_pct": 0.80,
        "nps_current": 6,
        "nps_previous": 8,
        "days_to_renewal": 30,
        "support_tickets_30d": 2,
        "negative_tickets_streak": 1,
        "last_login_days_ago": 3,
        "health_score": 45,
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "risk_level": "medium",
        "risk_score": 55,
        "primary_driver": "value_gap",
        "secondary_driver": "relationship",
        "active_features_pct": 0.60,
        "baseline_features_pct": 0.75,
        "nps_current": 7,
        "nps_previous": 9,
        "days_to_renewal": 55,
        "support_tickets_30d": 3,
        "negative_tickets_streak": 3,
        "last_login_days_ago": 2,
        "health_score": 58,
    },
}

_MOCK_CHURN_PREDICTIONS: dict[str, dict[int, float]] = {
    "CUST-001": {30: 0.85, 60: 0.92, 90: 0.96},
    "CUST-002": {30: 0.60, 60: 0.72, 90: 0.81},
    "CUST-003": {30: 0.35, 60: 0.48, 90: 0.55},
}

_MOCK_SIMILAR_CHURNED: dict[str, list[dict[str, Any]]] = {
    "critical|usage_gap": [
        {
            "customer_id": "CHURNED-101",
            "industry": "SaaS",
            "arr": 120000,
            "driver": "usage_gap",
            "months_before_churn": 3,
            "intervention_attempted": "product_training",
            "outcome": "churned",
            "lesson": "Training offered too late; needed executive outreach earlier.",
        },
        {
            "customer_id": "CHURNED-102",
            "industry": "FinTech",
            "arr": 95000,
            "driver": "usage_gap",
            "months_before_churn": 2,
            "intervention_attempted": "executive_outreach",
            "outcome": "saved",
            "lesson": "VP-level call within 1 week reversed the decline.",
        },
    ],
    "high|competitor": [
        {
            "customer_id": "CHURNED-201",
            "industry": "MarTech",
            "arr": 80000,
            "driver": "competitor",
            "months_before_churn": 2,
            "intervention_attempted": "competitive_repositioning",
            "outcome": "saved",
            "lesson": "Side-by-side ROI comparison won the internal champion back.",
        },
    ],
    "medium|value_gap": [
        {
            "customer_id": "CHURNED-301",
            "industry": "E-commerce",
            "arr": 60000,
            "driver": "value_gap",
            "months_before_churn": 4,
            "intervention_attempted": "success_story_sharing",
            "outcome": "saved",
            "lesson": "Peer case study + QBR reset expectations.",
        },
    ],
}

_MOCK_RETENTION_PLAYS: dict[str, list[dict[str, Any]]] = {
    "usage_gap": [
        {"play": "executive_outreach", "success_rate": 0.62, "avg_time_to_save_days": 14},
        {"play": "product_training", "success_rate": 0.55, "avg_time_to_save_days": 21},
    ],
    "competitor": [
        {"play": "competitive_repositioning", "success_rate": 0.58, "avg_time_to_save_days": 10},
        {"play": "commercial_offer", "success_rate": 0.50, "avg_time_to_save_days": 7},
    ],
    "value_gap": [
        {"play": "success_story_sharing", "success_rate": 0.60, "avg_time_to_save_days": 18},
        {"play": "product_training", "success_rate": 0.52, "avg_time_to_save_days": 25},
    ],
    "price": [
        {"play": "commercial_offer", "success_rate": 0.65, "avg_time_to_save_days": 5},
        {"play": "executive_outreach", "success_rate": 0.40, "avg_time_to_save_days": 12},
    ],
    "support": [
        {"play": "executive_outreach", "success_rate": 0.58, "avg_time_to_save_days": 7},
        {"play": "product_training", "success_rate": 0.45, "avg_time_to_save_days": 14},
    ],
    "relationship": [
        {"play": "executive_outreach", "success_rate": 0.70, "avg_time_to_save_days": 10},
        {"play": "success_story_sharing", "success_rate": 0.48, "avg_time_to_save_days": 20},
    ],
}

# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------


def _fetch_churn_risk_real(customer_id: str) -> dict[str, Any]:
    """Call a real churn-prediction microservice (e.g. internal ML API)."""
    import httpx

    api_url = os.getenv("CHURN_API_URL", "https://ml.internal/api/v1/churn")
    api_key = os.getenv("CHURN_API_KEY", "")
    try:
        resp = httpx.get(
            f"{api_url}/risk/{customer_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Churn API error for %s: %s — falling back to mock", customer_id, exc)
        return _MOCK_CHURN_PROFILES.get(customer_id, _default_profile(customer_id))


def _predict_churn_real(customer_id: str, days: int) -> dict[str, Any]:
    """Call the prediction endpoint for a specific time horizon."""
    import httpx

    api_url = os.getenv("CHURN_API_URL", "https://ml.internal/api/v1/churn")
    api_key = os.getenv("CHURN_API_KEY", "")
    try:
        resp = httpx.post(
            f"{api_url}/predict",
            json={"customer_id": customer_id, "horizon_days": days},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Churn predict API error: %s — falling back to mock", exc)
        prob = _MOCK_CHURN_PREDICTIONS.get(customer_id, {}).get(days, 0.50)
        return {"customer_id": customer_id, "horizon_days": days, "probability": prob}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_profile(customer_id: str) -> dict[str, Any]:
    """Generate a low-risk default profile for unknown customers."""
    return {
        "customer_id": customer_id,
        "risk_level": "low",
        "risk_score": 20,
        "primary_driver": "none",
        "secondary_driver": "none",
        "active_features_pct": 0.80,
        "baseline_features_pct": 0.80,
        "nps_current": 8,
        "nps_previous": 8,
        "days_to_renewal": 180,
        "support_tickets_30d": 0,
        "negative_tickets_streak": 0,
        "last_login_days_ago": 1,
        "health_score": 85,
    }


# ---------------------------------------------------------------------------
# Public tool functions (return JSON strings for AutoGen)
# ---------------------------------------------------------------------------


def get_churn_risk_score(customer_id: str) -> str:
    """Return the full churn-risk profile for a customer.

    Args:
        customer_id: Unique customer identifier (e.g. 'CUST-001').

    Returns:
        JSON string with risk_level, risk_score, primary_driver, health
        metrics, and trigger flags.
    """
    logger.info("get_churn_risk_score(%s) mock=%s", customer_id, USE_MOCK)

    if USE_MOCK:
        profile = _MOCK_CHURN_PROFILES.get(customer_id, _default_profile(customer_id))
    else:
        profile = _fetch_churn_risk_real(customer_id)

    # Enrich with trigger evaluation
    triggers_fired = []
    if profile.get("active_features_pct", 1.0) < 0.50 * profile.get("baseline_features_pct", 1.0):
        triggers_fired.append("usage_decline_below_50pct_baseline")
    if profile.get("nps_current", 10) < 7:
        triggers_fired.append("nps_below_7")
    if profile.get("negative_tickets_streak", 0) >= 3:
        triggers_fired.append("3_consecutive_negative_tickets")
    if profile.get("days_to_renewal", 999) < 60:
        triggers_fired.append("renewal_under_60_days")

    profile["triggers_fired"] = triggers_fired
    profile["assessed_at"] = datetime.now(timezone.utc).isoformat()
    profile["assessment_id"] = str(uuid.uuid4())

    return json.dumps(profile, indent=2)


def predict_churn_probability(customer_id: str, days: int) -> str:
    """Predict the probability that a customer will churn within N days.

    Args:
        customer_id: Unique customer identifier.
        days: Prediction horizon in days (e.g. 30, 60, 90).

    Returns:
        JSON string with customer_id, horizon_days, probability, and
        confidence_interval.
    """
    logger.info("predict_churn_probability(%s, %d) mock=%s", customer_id, days, USE_MOCK)

    if USE_MOCK:
        prob = _MOCK_CHURN_PREDICTIONS.get(customer_id, {}).get(days, 0.50)
        result = {"customer_id": customer_id, "horizon_days": days, "probability": prob}
    else:
        result = _predict_churn_real(customer_id, days)

    result["confidence_interval"] = [
        round(max(0.0, result["probability"] - 0.08), 2),
        round(min(1.0, result["probability"] + 0.08), 2),
    ]
    result["predicted_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)


def get_similar_churned_customers(risk_level: str, driver: str) -> str:
    """Retrieve profiles of similar customers who previously churned.

    Args:
        risk_level: One of low, medium, high, critical.
        driver: Primary churn driver (e.g. usage_gap, competitor).

    Returns:
        JSON string with a list of similar churned-customer case summaries.
    """
    logger.info("get_similar_churned_customers(%s, %s) mock=%s", risk_level, driver, USE_MOCK)

    key = f"{risk_level}|{driver}"
    if USE_MOCK:
        cases = _MOCK_SIMILAR_CHURNED.get(key, [])
    else:
        import httpx
        api_url = os.getenv("CHURN_API_URL", "https://ml.internal/api/v1/churn")
        api_key = os.getenv("CHURN_API_KEY", "")
        try:
            resp = httpx.get(
                f"{api_url}/similar",
                params={"risk_level": risk_level, "driver": driver},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            cases = resp.json().get("cases", [])
        except Exception as exc:
            logger.warning("Similar-churned API error: %s — using mock", exc)
            cases = _MOCK_SIMILAR_CHURNED.get(key, [])

    return json.dumps({"risk_level": risk_level, "driver": driver, "similar_cases": cases}, indent=2)


def get_successful_retention_plays(driver: str) -> str:
    """Look up historically successful retention plays for a given driver.

    Args:
        driver: Primary churn driver (usage_gap|value_gap|price|competitor|
                support|relationship).

    Returns:
        JSON string listing plays sorted by success rate.
    """
    logger.info("get_successful_retention_plays(%s) mock=%s", driver, USE_MOCK)

    if USE_MOCK:
        plays = _MOCK_RETENTION_PLAYS.get(driver, [])
    else:
        import httpx
        api_url = os.getenv("CHURN_API_URL", "https://ml.internal/api/v1/churn")
        api_key = os.getenv("CHURN_API_KEY", "")
        try:
            resp = httpx.get(
                f"{api_url}/retention-plays",
                params={"driver": driver},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            plays = resp.json().get("plays", [])
        except Exception as exc:
            logger.warning("Retention-plays API error: %s — using mock", exc)
            plays = _MOCK_RETENTION_PLAYS.get(driver, [])

    return json.dumps({"driver": driver, "plays": plays}, indent=2)
