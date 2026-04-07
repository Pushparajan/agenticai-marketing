# File      : deal_crm_tools.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
CRM tools for managing deals during the Decision stage.

Every function follows the **USE_MOCK** pattern:
- ``USE_MOCK=true`` (default)  -> deterministic mock data
- ``USE_MOCK=false``           -> calls the real HubSpot API
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from langchain_core.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# ---------------------------------------------------------------------------
# In-memory mock CRM store
# ---------------------------------------------------------------------------

_MOCK_DEALS: dict[str, dict] = {
    "deal-001": {
        "deal_id": "deal-001",
        "company": "Acme Corp",
        "contact_id": "contact-101",
        "stage": "decision",
        "value": 75000.0,
        "owner": "sales-rep-a",
        "created_at": "2026-03-01T10:00:00Z",
        "last_activity": "2026-03-28T14:30:00Z",
        "tasks": [],
    },
    "deal-002": {
        "deal_id": "deal-002",
        "company": "Beta Industries",
        "contact_id": "contact-202",
        "stage": "decision",
        "value": 32000.0,
        "owner": "sales-rep-b",
        "created_at": "2026-03-10T09:00:00Z",
        "last_activity": "2026-03-25T11:00:00Z",
        "tasks": [],
    },
    "deal-003": {
        "deal_id": "deal-003",
        "company": "Gamma Health",
        "contact_id": "contact-303",
        "stage": "decision",
        "value": 120000.0,
        "owner": "sales-rep-c",
        "created_at": "2026-02-20T08:00:00Z",
        "last_activity": "2026-03-15T16:45:00Z",
        "tasks": [],
    },
}

# ---------------------------------------------------------------------------
# Real HubSpot helpers
# ---------------------------------------------------------------------------

def _hubspot_client():
    """Return an authenticated HubSpot API client."""
    from hubspot import HubSpot

    token = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
    return HubSpot(access_token=token)


def _real_get_deal(deal_id: str) -> str:
    """Fetch a deal from HubSpot."""
    client = _hubspot_client()
    deal = client.crm.deals.basic_api.get_by_id(
        deal_id,
        properties=["dealname", "amount", "dealstage", "pipeline"],
    )
    return json.dumps(deal.to_dict(), indent=2, default=str)


def _real_update_deal_stage(deal_id: str, stage: str) -> str:
    """Update a deal stage in HubSpot."""
    from hubspot.crm.deals import SimplePublicObjectInput

    client = _hubspot_client()
    props = SimplePublicObjectInput(properties={"dealstage": stage})
    result = client.crm.deals.basic_api.update(deal_id, props)
    return json.dumps(result.to_dict(), indent=2, default=str)


def _real_create_deal_task(deal_id: str, title: str, owner: str) -> str:
    """Create a task associated with a deal in HubSpot."""
    from hubspot.crm.objects.tasks import SimplePublicObjectInput

    client = _hubspot_client()
    props = SimplePublicObjectInput(
        properties={
            "hs_task_subject": title,
            "hubspot_owner_id": owner,
            "hs_task_status": "NOT_STARTED",
        }
    )
    task = client.crm.objects.tasks.basic_api.create(props)
    return json.dumps(task.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

@tool
def get_deal(deal_id: str) -> str:
    """Fetch deal details from the CRM.

    Args:
        deal_id: The unique deal identifier.

    Returns:
        JSON string with deal properties.
    """
    if USE_MOCK:
        deal = _MOCK_DEALS.get(deal_id)
        if deal:
            return json.dumps(deal, indent=2)
        # Return a sensible default for unknown IDs
        return json.dumps(
            {
                "deal_id": deal_id,
                "company": "Unknown",
                "contact_id": "unknown",
                "stage": "decision",
                "value": 0.0,
                "owner": "unassigned",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "tasks": [],
            },
            indent=2,
        )
    return _real_get_deal(deal_id)


@tool
def update_deal_stage(deal_id: str, stage: str) -> str:
    """Update the stage of a deal in the CRM.

    Args:
        deal_id: The unique deal identifier.
        stage: The new stage name.

    Returns:
        JSON string confirming the update.
    """
    if USE_MOCK:
        deal = _MOCK_DEALS.get(deal_id)
        now = datetime.now(timezone.utc).isoformat()
        if deal:
            deal["stage"] = stage
            deal["last_activity"] = now
            return json.dumps(
                {"status": "updated", "deal_id": deal_id, "new_stage": stage, "at": now},
                indent=2,
            )
        return json.dumps(
            {"status": "updated", "deal_id": deal_id, "new_stage": stage, "at": now},
            indent=2,
        )
    return _real_update_deal_stage(deal_id, stage)


@tool
def create_deal_task(deal_id: str, title: str, owner: str) -> str:
    """Create a follow-up task for a deal in the CRM.

    Args:
        deal_id: The deal to associate the task with.
        title: Short description of the task.
        owner: Owner / assignee identifier.

    Returns:
        JSON string with the created task details.
    """
    if USE_MOCK:
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        task = {
            "task_id": task_id,
            "deal_id": deal_id,
            "title": title,
            "owner": owner,
            "status": "NOT_STARTED",
            "created_at": now,
        }
        # Also store in the mock deal if it exists
        deal = _MOCK_DEALS.get(deal_id)
        if deal:
            deal.setdefault("tasks", []).append(task)
        return json.dumps(task, indent=2)
    return _real_create_deal_task(deal_id, title, owner)
