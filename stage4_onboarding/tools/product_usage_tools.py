# File      : product_usage_tools.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Product-usage analytics tools used by the Product Specialist agent.

Each function follows the USE_MOCK pattern:
  * When ``USE_MOCK=true`` (default) a deterministic mock response is returned.
  * When ``USE_MOCK=false`` the function calls the real analytics API.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import httpx

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
ANALYTICS_API_BASE: str = os.getenv("ANALYTICS_API_BASE", "https://analytics.example.com/api/v1")
ANALYTICS_API_KEY: str = os.getenv("ANALYTICS_API_KEY", "")

# ---------------------------------------------------------------------------
# Mock data stores
# ---------------------------------------------------------------------------

_MOCK_HEATMAPS: Dict[str, Dict[str, Any]] = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "period_days": 7,
        "features": {
            "dashboard": {"sessions": 18, "avg_duration_sec": 240},
            "reports": {"sessions": 12, "avg_duration_sec": 180},
            "integrations": {"sessions": 3, "avg_duration_sec": 60},
            "settings": {"sessions": 2, "avg_duration_sec": 30},
            "automations": {"sessions": 0, "avg_duration_sec": 0},
        },
        "peak_hours": ["09:00-11:00", "14:00-16:00"],
    },
    "CUST-1002": {
        "customer_id": "CUST-1002",
        "period_days": 7,
        "features": {
            "dashboard": {"sessions": 4, "avg_duration_sec": 45},
            "reports": {"sessions": 1, "avg_duration_sec": 20},
            "integrations": {"sessions": 0, "avg_duration_sec": 0},
            "settings": {"sessions": 1, "avg_duration_sec": 15},
            "automations": {"sessions": 0, "avg_duration_sec": 0},
        },
        "peak_hours": ["10:00-10:30"],
    },
}

_MOCK_ADOPTION: Dict[str, float] = {
    "CUST-1001": 0.72,
    "CUST-1002": 0.18,
}

_MOCK_FEATURE_COMPLETION: Dict[str, Dict[str, Any]] = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "completed": ["account_setup", "invite_team", "first_dashboard", "connect_data_source"],
        "pending": ["create_automation", "schedule_report"],
        "completion_rate": 0.67,
    },
    "CUST-1002": {
        "customer_id": "CUST-1002",
        "completed": ["account_setup"],
        "pending": [
            "invite_team",
            "first_dashboard",
            "connect_data_source",
            "create_automation",
            "schedule_report",
        ],
        "completion_rate": 0.17,
    },
}

_MOCK_FRICTION: Dict[str, List[Dict[str, str]]] = {
    "CUST-1001": [
        {"area": "integrations", "signal": "Visited page 3 times without completing setup"},
    ],
    "CUST-1002": [
        {"area": "dashboard", "signal": "Average session < 1 min — likely confused by layout"},
        {"area": "invite_team", "signal": "Started invite flow twice, abandoned both times"},
        {"area": "data_source", "signal": "No data-source connected after 7 days"},
    ],
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _api_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {ANALYTICS_API_KEY}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def get_usage_heatmap(customer_id: str, days: int = 7) -> str:
    """Return a feature-usage heatmap for *customer_id* over the last *days*.

    Returns a JSON string with per-feature session counts, average duration,
    and peak-usage hours.
    """
    if USE_MOCK:
        data = _MOCK_HEATMAPS.get(customer_id)
        if data is None:
            # Generate plausible random data for unknown IDs
            features = {
                feat: {
                    "sessions": random.randint(0, 20),
                    "avg_duration_sec": random.randint(0, 300),
                }
                for feat in ["dashboard", "reports", "integrations", "settings", "automations"]
            }
            data = {
                "customer_id": customer_id,
                "period_days": days,
                "features": features,
                "peak_hours": ["09:00-11:00"],
            }
        return json.dumps(data, indent=2)

    # Real API call
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{ANALYTICS_API_BASE}/usage/heatmap",
            params={"customer_id": customer_id, "days": days},
            headers=_api_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


def get_adoption_score(customer_id: str) -> str:
    """Return a 0.0-1.0 adoption score for *customer_id*.

    The score aggregates feature breadth, depth and recency into a single
    number that indicates how well the customer has adopted the product.
    """
    if USE_MOCK:
        score = _MOCK_ADOPTION.get(customer_id, round(random.uniform(0.1, 0.9), 2))
        result = {"customer_id": customer_id, "adoption_score": score}
        return json.dumps(result, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{ANALYTICS_API_BASE}/adoption/score",
            params={"customer_id": customer_id},
            headers=_api_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


def get_feature_completion_rate(customer_id: str) -> str:
    """Return onboarding-feature completion status for *customer_id*.

    The response lists completed milestones, pending milestones, and an
    overall completion rate (0.0-1.0).
    """
    if USE_MOCK:
        data = _MOCK_FEATURE_COMPLETION.get(customer_id)
        if data is None:
            all_features = [
                "account_setup", "invite_team", "first_dashboard",
                "connect_data_source", "create_automation", "schedule_report",
            ]
            done = random.sample(all_features, k=random.randint(0, len(all_features)))
            pending = [f for f in all_features if f not in done]
            data = {
                "customer_id": customer_id,
                "completed": done,
                "pending": pending,
                "completion_rate": round(len(done) / len(all_features), 2),
            }
        return json.dumps(data, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{ANALYTICS_API_BASE}/features/completion",
            params={"customer_id": customer_id},
            headers=_api_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


def identify_friction_points(customer_id: str) -> str:
    """Identify UX friction points for *customer_id* during onboarding.

    Analyses short sessions, repeated page visits without completion, and
    abandoned flows to flag areas that need attention.
    """
    if USE_MOCK:
        points = _MOCK_FRICTION.get(customer_id, [])
        result = {
            "customer_id": customer_id,
            "friction_points": points,
            "total_friction_signals": len(points),
        }
        return json.dumps(result, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{ANALYTICS_API_BASE}/friction/identify",
            params={"customer_id": customer_id},
            headers=_api_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
