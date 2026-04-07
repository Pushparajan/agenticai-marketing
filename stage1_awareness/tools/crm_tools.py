# File      : crm_tools.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
HubSpot CRM tool wrappers.

Provides create / read / update operations on HubSpot contacts with
automatic mock fallback controlled by the USE_MOCK_APIS env var.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY", "")
HUBSPOT_BASE = "https://api.hubapi.com"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# In-memory mock store
# ---------------------------------------------------------------------------

_mock_contacts: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# create_crm_contact
# ---------------------------------------------------------------------------

def _create_contact_real(
    email: str,
    firstname: str,
    lastname: str,
    company: str,
    source: str,
) -> dict[str, Any]:
    """Create a contact in HubSpot via the v3 API."""
    import httpx

    payload = {
        "properties": {
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "company": company,
            "hs_lead_status": "NEW",
            "lifecyclestage": "subscriber",
            "source": source,
        }
    }
    resp = httpx.post(
        f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
        json=payload,
        headers={
            "Authorization": f"Bearer {HUBSPOT_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "contact_id": data["id"],
        "email": email,
        "stage": "subscriber",
        "created": True,
    }


def _create_contact_mock(
    email: str,
    firstname: str,
    lastname: str,
    company: str,
    source: str,
) -> dict[str, Any]:
    """Store a contact in the in-memory mock CRM."""
    contact_id = str(uuid.uuid4())
    record = {
        "contact_id": contact_id,
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        "company": company,
        "source": source,
        "stage": "subscriber",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _mock_contacts[email] = record
    return {"contact_id": contact_id, "email": email, "stage": "subscriber", "created": True}


def create_crm_contact(
    email: str,
    firstname: str,
    lastname: str,
    company: str,
    source: str,
) -> dict[str, Any]:
    """Create a new CRM contact.

    Args:
        email: Contact email address.
        firstname: First name.
        lastname: Last name.
        company: Company / organisation name.
        source: Lead source identifier (e.g. ``"google_ads"``).

    Returns:
        Dict with ``contact_id``, ``email``, ``stage``, and ``created`` flag.
    """
    logger.info("Creating CRM contact for %s (mock=%s)", email, USE_MOCK)
    if USE_MOCK:
        return _create_contact_mock(email, firstname, lastname, company, source)
    return _create_contact_real(email, firstname, lastname, company, source)


# ---------------------------------------------------------------------------
# get_contact
# ---------------------------------------------------------------------------

def _get_contact_real(email: str) -> dict[str, Any]:
    """Look up a HubSpot contact by email."""
    import httpx

    resp = httpx.get(
        f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{email}",
        params={"idProperty": "email"},
        headers={"Authorization": f"Bearer {HUBSPOT_API_KEY}"},
        timeout=10,
    )
    if resp.status_code == 404:
        return {"found": False, "email": email}
    resp.raise_for_status()
    data = resp.json()
    props = data.get("properties", {})
    return {
        "found": True,
        "contact_id": data["id"],
        "email": props.get("email", email),
        "firstname": props.get("firstname", ""),
        "lastname": props.get("lastname", ""),
        "company": props.get("company", ""),
        "stage": props.get("lifecyclestage", "unknown"),
    }


def _get_contact_mock(email: str) -> dict[str, Any]:
    """Retrieve a contact from the in-memory mock store."""
    if email in _mock_contacts:
        return {"found": True, **_mock_contacts[email]}
    return {"found": False, "email": email}


def get_contact(email: str) -> dict[str, Any]:
    """Look up a contact by email.

    Args:
        email: The contact's email address.

    Returns:
        Dict with ``found`` flag and contact properties when found.
    """
    logger.info("Looking up CRM contact %s (mock=%s)", email, USE_MOCK)
    if USE_MOCK:
        return _get_contact_mock(email)
    return _get_contact_real(email)


# ---------------------------------------------------------------------------
# update_contact_stage
# ---------------------------------------------------------------------------

def _update_stage_real(contact_id: str, stage: str) -> dict[str, Any]:
    """Update lifecycle stage on an existing HubSpot contact."""
    import httpx

    resp = httpx.patch(
        f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
        json={"properties": {"lifecyclestage": stage}},
        headers={
            "Authorization": f"Bearer {HUBSPOT_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return {"contact_id": contact_id, "stage": stage, "updated": True}


def _update_stage_mock(contact_id: str, stage: str) -> dict[str, Any]:
    """Update the stage in the in-memory mock store."""
    for record in _mock_contacts.values():
        if record.get("contact_id") == contact_id:
            record["stage"] = stage
            return {"contact_id": contact_id, "stage": stage, "updated": True}
    return {"contact_id": contact_id, "stage": stage, "updated": False, "error": "not found"}


def update_contact_stage(contact_id: str, stage: str) -> dict[str, Any]:
    """Update a contact's lifecycle stage.

    Args:
        contact_id: The CRM contact ID.
        stage: New lifecycle stage (e.g. ``"lead"``, ``"opportunity"``).

    Returns:
        Dict with ``contact_id``, ``stage``, and ``updated`` flag.
    """
    logger.info("Updating contact %s to stage '%s' (mock=%s)", contact_id, stage, USE_MOCK)
    if USE_MOCK:
        return _update_stage_mock(contact_id, stage)
    return _update_stage_real(contact_id, stage)
