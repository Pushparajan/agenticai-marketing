# File      : support_ticket_tools.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Support-ticket and task-management tools for the Customer Success agent.

Covers ticket retrieval, onboarding-task creation, and sentiment scoring.
Follows the USE_MOCK pattern throughout.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

import httpx

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
SUPPORT_API_BASE: str = os.getenv("SUPPORT_API_BASE", "https://support.example.com/api/v1")
SUPPORT_API_KEY: str = os.getenv("SUPPORT_API_KEY", "")
HUBSPOT_API_BASE: str = os.getenv("HUBSPOT_API_BASE", "https://api.hubapi.com")
HUBSPOT_API_KEY: str = os.getenv("HUBSPOT_API_KEY", "")

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_TICKETS: Dict[str, List[Dict[str, Any]]] = {
    "CUST-1001": [
        {
            "ticket_id": "TKT-4010",
            "subject": "How to connect Salesforce data source?",
            "status": "resolved",
            "priority": "medium",
            "created_at": "2026-03-30T14:22:00Z",
            "resolved_at": "2026-03-30T15:10:00Z",
            "category": "integrations",
        },
    ],
    "CUST-1002": [
        {
            "ticket_id": "TKT-4021",
            "subject": "Dashboard is empty after login",
            "status": "open",
            "priority": "high",
            "created_at": "2026-03-27T09:00:00Z",
            "resolved_at": None,
            "category": "dashboard",
        },
        {
            "ticket_id": "TKT-4022",
            "subject": "Cannot invite team members — error 500",
            "status": "open",
            "priority": "high",
            "created_at": "2026-03-28T11:30:00Z",
            "resolved_at": None,
            "category": "team_management",
        },
        {
            "ticket_id": "TKT-4023",
            "subject": "Where do I find onboarding docs?",
            "status": "resolved",
            "priority": "low",
            "created_at": "2026-03-26T16:45:00Z",
            "resolved_at": "2026-03-26T17:00:00Z",
            "category": "documentation",
        },
    ],
}

_MOCK_SENTIMENT: Dict[str, Dict[str, Any]] = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "sentiment_score": 0.82,
        "label": "positive",
        "signals": [
            "Quick ticket resolution",
            "Positive CSAT survey response",
        ],
    },
    "CUST-1002": {
        "customer_id": "CUST-1002",
        "sentiment_score": 0.31,
        "label": "negative",
        "signals": [
            "Multiple open high-priority tickets",
            "No CSAT survey response",
            "Short session durations",
        ],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _support_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {SUPPORT_API_KEY}",
        "Content-Type": "application/json",
    }


def _hubspot_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def get_recent_tickets(customer_id: str) -> str:
    """Return recent support tickets for *customer_id*.

    Returns a JSON object containing a list of ticket summaries with id,
    subject, status, priority, and category.
    """
    if USE_MOCK:
        tickets = _MOCK_TICKETS.get(customer_id, [])
        result = {
            "customer_id": customer_id,
            "tickets": tickets,
            "total": len(tickets),
            "open_count": sum(1 for t in tickets if t["status"] == "open"),
        }
        return json.dumps(result, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{SUPPORT_API_BASE}/tickets",
            params={"customer_id": customer_id, "limit": 10},
            headers=_support_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


def create_onboarding_task(customer_id: str, title: str, owner: str) -> str:
    """Create a CRM onboarding task (e.g. in HubSpot) for *customer_id*.

    Parameters
    ----------
    customer_id : str
        The customer identifier.
    title : str
        Task title / description.
    owner : str
        The CS team member assigned to the task.

    Returns a JSON confirmation with the created task ID.
    """
    if USE_MOCK:
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
        due_date = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
        result = {
            "task_id": task_id,
            "customer_id": customer_id,
            "title": title,
            "owner": owner,
            "due_date": due_date,
            "status": "open",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "success": True,
        }
        return json.dumps(result, indent=2)

    # Real HubSpot task creation
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{HUBSPOT_API_BASE}/crm/v3/objects/tasks",
            json={
                "properties": {
                    "hs_task_subject": title,
                    "hs_task_body": f"Onboarding task for customer {customer_id}",
                    "hubspot_owner_id": owner,
                    "hs_task_status": "NOT_STARTED",
                    "hs_task_priority": "HIGH",
                    "hs_timestamp": datetime.utcnow().isoformat() + "Z",
                }
            },
            headers=_hubspot_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


def get_sentiment_score(customer_id: str) -> str:
    """Return a sentiment score (0.0-1.0) for *customer_id*.

    Combines support-ticket tone, CSAT responses, and session-behaviour
    signals into a single sentiment metric.
    """
    if USE_MOCK:
        data = _MOCK_SENTIMENT.get(customer_id)
        if data is None:
            data = {
                "customer_id": customer_id,
                "sentiment_score": 0.50,
                "label": "neutral",
                "signals": ["Insufficient data for strong signal"],
            }
        return json.dumps(data, indent=2)

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{SUPPORT_API_BASE}/sentiment/{customer_id}",
            headers=_support_headers(),
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
