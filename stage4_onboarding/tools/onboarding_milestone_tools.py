# File      : onboarding_milestone_tools.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Onboarding-milestone management tools.

Provides checklist retrieval, milestone status updates, and time-to-value
metrics.  Follows the USE_MOCK pattern throughout.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import httpx

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
ONBOARDING_API_BASE: str = os.getenv("ONBOARDING_API_BASE", "https://onboard.example.com/api/v1")
ONBOARDING_API_KEY: str = os.getenv("ONBOARDING_API_KEY", "")

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_CHECKLISTS: Dict[str, List[Dict[str, Any]]] = {
    "standard": [
        {"step": 1, "milestone": "account_setup", "label": "Complete account profile", "est_minutes": 10},
        {"step": 2, "milestone": "invite_team", "label": "Invite at least one team member", "est_minutes": 5},
        {"step": 3, "milestone": "connect_data_source", "label": "Connect first data source", "est_minutes": 15},
        {"step": 4, "milestone": "first_dashboard", "label": "Create your first dashboard", "est_minutes": 20},
        {"step": 5, "milestone": "create_automation", "label": "Set up a basic automation", "est_minutes": 15},
        {"step": 6, "milestone": "schedule_report", "label": "Schedule a recurring report", "est_minutes": 10},
    ],
    "enterprise": [
        {"step": 1, "milestone": "account_setup", "label": "Complete account profile", "est_minutes": 10},
        {"step": 2, "milestone": "sso_config", "label": "Configure SSO / SAML", "est_minutes": 30},
        {"step": 3, "milestone": "invite_team", "label": "Invite team members and assign roles", "est_minutes": 15},
        {"step": 4, "milestone": "connect_data_source", "label": "Connect primary data source", "est_minutes": 20},
        {"step": 5, "milestone": "data_governance", "label": "Set up data governance policies", "est_minutes": 25},
        {"step": 6, "milestone": "first_dashboard", "label": "Create executive dashboard", "est_minutes": 25},
        {"step": 7, "milestone": "create_automation", "label": "Create automation workflows", "est_minutes": 20},
        {"step": 8, "milestone": "schedule_report", "label": "Schedule recurring reports", "est_minutes": 10},
        {"step": 9, "milestone": "admin_training", "label": "Complete admin training session", "est_minutes": 60},
    ],
}

_MOCK_MILESTONE_STATUS: Dict[str, Dict[str, str]] = {
    "CUST-1001": {
        "account_setup": "completed",
        "invite_team": "completed",
        "connect_data_source": "completed",
        "first_dashboard": "completed",
        "create_automation": "pending",
        "schedule_report": "pending",
    },
    "CUST-1002": {
        "account_setup": "completed",
        "invite_team": "pending",
        "connect_data_source": "pending",
        "first_dashboard": "pending",
        "create_automation": "pending",
        "schedule_report": "pending",
    },
}

_MOCK_TTV: Dict[str, Dict[str, Any]] = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "signup_date": "2026-03-28",
        "first_value_event": "2026-03-30",
        "days_to_value": 2,
        "value_event": "Created first dashboard with live data",
        "benchmark_days": 5,
        "status": "ahead_of_benchmark",
    },
    "CUST-1002": {
        "customer_id": "CUST-1002",
        "signup_date": "2026-03-25",
        "first_value_event": None,
        "days_to_value": None,
        "value_event": None,
        "benchmark_days": 5,
        "status": "at_risk",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _api_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {ONBOARDING_API_KEY}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def get_onboarding_checklist(plan_type: str = "standard") -> str:
    """Return the onboarding checklist for the given *plan_type*.

    Supported types: ``standard``, ``enterprise``.  Returns a JSON array
    of milestone objects with step number, label, and estimated minutes.
    """
    if USE_MOCK:
        checklist = _MOCK_CHECKLISTS.get(plan_type, _MOCK_CHECKLISTS["standard"])
        result = {"plan_type": plan_type, "milestones": checklist}
        return json.dumps(result, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{ONBOARDING_API_BASE}/checklists/{plan_type}",
            headers=_api_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


def update_milestone_status(customer_id: str, milestone: str, status: str) -> str:
    """Update the status of a specific onboarding *milestone* for *customer_id*.

    Parameters
    ----------
    customer_id : str
        The customer identifier.
    milestone : str
        Milestone key (e.g. ``invite_team``).
    status : str
        New status — ``pending``, ``in_progress``, or ``completed``.

    Returns a JSON confirmation object.
    """
    if USE_MOCK:
        if customer_id in _MOCK_MILESTONE_STATUS:
            _MOCK_MILESTONE_STATUS[customer_id][milestone] = status
        result = {
            "customer_id": customer_id,
            "milestone": milestone,
            "new_status": status,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "success": True,
        }
        return json.dumps(result, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.patch(
            f"{ONBOARDING_API_BASE}/milestones",
            json={
                "customer_id": customer_id,
                "milestone": milestone,
                "status": status,
            },
            headers=_api_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


def get_time_to_value(customer_id: str) -> str:
    """Return time-to-value metrics for *customer_id*.

    Includes signup date, first value event, days elapsed, and comparison
    against the benchmark for the customer's plan type.
    """
    if USE_MOCK:
        data = _MOCK_TTV.get(customer_id)
        if data is None:
            data = {
                "customer_id": customer_id,
                "signup_date": (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d"),
                "first_value_event": None,
                "days_to_value": None,
                "value_event": None,
                "benchmark_days": 5,
                "status": "at_risk",
            }
        return json.dumps(data, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{ONBOARDING_API_BASE}/ttv/{customer_id}",
            headers=_api_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
