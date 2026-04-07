# tools/crm_tools.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: HubSpot CRM lifecycle and sales handoff tools with mock fallback
# Author: Pushparajan Ramar

"""CRM tools for the customer journey orchestrator.

Provides lifecycle-stage updates, sales-task creation, and full sales-
handoff capabilities via HubSpot CRM.  Each function attempts the live
HubSpot API when *USE_MOCK* is False and *HUBSPOT_API_KEY* is present,
otherwise returns a deterministic mock confirmation.

Environment variables consumed (via .env):
    USE_MOCK         -- "true" (default) or "false"
    HUBSPOT_API_KEY  -- HubSpot private app access token
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
HUBSPOT_API_KEY: str = os.getenv("HUBSPOT_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mock_id() -> str:
    """Return a short unique identifier for mock objects."""
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# HubSpot API helpers
# ---------------------------------------------------------------------------

def _hubspot_patch_contact(
    contact_id: str,
    properties: dict[str, Any],
) -> dict[str, Any] | None:
    """PATCH a HubSpot contact's properties.  Returns parsed JSON or None."""
    if USE_MOCK or not HUBSPOT_API_KEY:
        return None
    try:
        import httpx

        resp = httpx.patch(
            f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
            headers={
                "Authorization": f"Bearer {HUBSPOT_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"properties": properties},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        log.warning("HubSpot PATCH failed, falling back to mock: %s", exc)
        return None


def _hubspot_create_task(
    contact_id: str,
    subject: str,
    body: str,
) -> dict[str, Any] | None:
    """Create an engagement task in HubSpot.  Returns parsed JSON or None."""
    if USE_MOCK or not HUBSPOT_API_KEY:
        return None
    try:
        import httpx

        payload = {
            "properties": {
                "hs_task_subject": subject,
                "hs_task_body": body,
                "hs_task_status": "NOT_STARTED",
                "hs_task_priority": "HIGH",
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 204,  # task-to-contact
                        }
                    ],
                }
            ],
        }
        resp = httpx.post(
            "https://api.hubapi.com/crm/v3/objects/tasks",
            headers={
                "Authorization": f"Bearer {HUBSPOT_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        log.warning("HubSpot task creation failed, falling back to mock: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def update_lifecycle_stage(
    contact_id: str,
    stage: str,
) -> dict[str, Any]:
    """Update the lifecycle stage of a contact in HubSpot CRM.

    Args:
        contact_id: HubSpot contact ID.
        stage:      New lifecycle stage value.  Common values are "lead",
                    "marketingqualifiedlead", "salesqualifiedlead",
                    "opportunity", and "customer".

    Returns:
        Confirmation dict with contact_id, previous_stage (mock only),
        new_stage, status, and updated_at timestamp.
    """
    log.info(
        "update_lifecycle_stage  contact_id=%s  stage=%s  mock=%s  ts=%s",
        contact_id, stage, USE_MOCK, _ts(),
    )

    result = _hubspot_patch_contact(
        contact_id,
        {"lifecyclestage": stage},
    )

    if result is not None:
        return {
            "contact_id": contact_id,
            "new_stage": stage,
            "status": "UPDATED",
            "updated_at": _ts(),
        }

    # ----- mock fallback -----
    previous_stage = "lead" if stage != "lead" else "subscriber"
    log.info("Mock lifecycle update for %s: %s -> %s", contact_id, previous_stage, stage)
    return {
        "contact_id": contact_id,
        "previous_stage": previous_stage,
        "new_stage": stage,
        "status": "MOCK_UPDATED",
        "updated_at": _ts(),
    }


def create_sales_task(
    contact_id: str,
    description: str,
) -> dict[str, Any]:
    """Create a follow-up task for a sales rep in HubSpot CRM.

    Args:
        contact_id:  HubSpot contact ID to associate the task with.
        description: Plain-text task description for the sales rep.

    Returns:
        Confirmation dict with task_id, contact_id, subject, description,
        priority, status, and created_at timestamp.
    """
    subject = f"Follow up with contact {contact_id}"

    log.info(
        "create_sales_task  contact_id=%s  mock=%s  ts=%s",
        contact_id, USE_MOCK, _ts(),
    )

    result = _hubspot_create_task(contact_id, subject, description)

    if result is not None:
        return {
            "task_id": result.get("id", _mock_id()),
            "contact_id": contact_id,
            "subject": subject,
            "description": description,
            "priority": "HIGH",
            "status": "CREATED",
            "created_at": _ts(),
        }

    # ----- mock fallback -----
    task_id = f"task-{_mock_id()}"
    log.info("Mock sales task created: %s for contact %s", task_id, contact_id)
    return {
        "task_id": task_id,
        "contact_id": contact_id,
        "subject": subject,
        "description": description,
        "priority": "HIGH",
        "status": "MOCK_CREATED",
        "created_at": _ts(),
    }


def handoff_to_sales(
    contact_id: str,
    context: str,
) -> dict[str, Any]:
    """Perform a full sales handoff for a marketing-qualified contact.

    This combines a lifecycle-stage update to *salesqualifiedlead*, a
    high-priority sales task, and a notification payload.

    Args:
        contact_id: HubSpot contact ID.
        context:    Summary of the contact's engagement journey so far.

    Returns:
        Confirmation dict with handoff_id, contact_id, lifecycle_update,
        task, notification payload, status, and handed_off_at timestamp.
    """
    log.info(
        "handoff_to_sales  contact_id=%s  mock=%s  ts=%s",
        contact_id, USE_MOCK, _ts(),
    )

    # Step 1: Update lifecycle stage
    lifecycle_result = update_lifecycle_stage(contact_id, "salesqualifiedlead")

    # Step 2: Create a sales task with full context
    task_description = (
        f"Marketing-qualified contact ready for outreach.\n\n"
        f"Journey context:\n{context}\n\n"
        f"Recommended action: Schedule discovery call within 24 hours."
    )
    task_result = create_sales_task(contact_id, task_description)

    # Step 3: Build handoff confirmation
    handoff_id = f"handoff-{_mock_id()}"
    log.info("Sales handoff complete: %s for contact %s", handoff_id, contact_id)

    return {
        "handoff_id": handoff_id,
        "contact_id": contact_id,
        "lifecycle_update": lifecycle_result,
        "task": task_result,
        "notification": {
            "type": "sales_handoff",
            "message": f"Contact {contact_id} is marketing-qualified and ready for sales outreach.",
            "urgency": "high",
        },
        "status": "HANDED_OFF",
        "handed_off_at": _ts(),
    }


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("CRM Tools — Demo")
    print("=" * 60)
    print(f"USE_MOCK = {USE_MOCK}\n")

    cid = "contact-high-001"

    for label, fn, kwargs in [
        (
            "Update Lifecycle Stage",
            update_lifecycle_stage,
            {"contact_id": cid, "stage": "marketingqualifiedlead"},
        ),
        (
            "Create Sales Task",
            create_sales_task,
            {"contact_id": cid, "description": "High engagement — schedule discovery call."},
        ),
        (
            "Full Sales Handoff",
            handoff_to_sales,
            {
                "contact_id": cid,
                "context": "12 email opens, 34 page views, attended webinar, requested demo.",
            },
        ),
    ]:
        print(f"--- {label} ---")
        print(json.dumps(fn(**kwargs), indent=2))
        print()
