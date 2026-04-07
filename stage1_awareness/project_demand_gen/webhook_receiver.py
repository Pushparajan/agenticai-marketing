# File      : webhook_receiver.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
FastAPI webhook receiver for HubSpot events.

Accepts ``contact.created`` and ``page_visit`` webhooks, validates the
HMAC signature, and dispatches the lead to the triage pipeline
asynchronously.  Returns HTTP 200 immediately to satisfy webhook SLAs.

Run:
    uvicorn stage1_awareness.project_demand_gen.webhook_receiver:app --port 8000
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
HUBSPOT_WEBHOOK_SECRET = os.getenv("HUBSPOT_WEBHOOK_SECRET", "demo-secret-key")

app = FastAPI(
    title="Awareness Webhook Receiver",
    version="1.0.0",
    description="Receives HubSpot webhooks and dispatches to the triage pipeline.",
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class HubSpotWebhookEvent(BaseModel):
    """Schema for a single HubSpot webhook event."""

    subscriptionType: str
    objectId: int
    propertyName: str | None = None
    propertyValue: str | None = None
    changeSource: str | None = None
    eventId: int | None = None
    occurredAt: int | None = None
    portalId: int | None = None


class WebhookResponse(BaseModel):
    """Acknowledgement response returned to the webhook caller."""

    status: str = "accepted"
    events_received: int = 0
    timestamp: str = ""


# ---------------------------------------------------------------------------
# HMAC signature validation
# ---------------------------------------------------------------------------


def _validate_signature(
    body: bytes,
    signature: str | None,
) -> bool:
    """Verify the HubSpot webhook HMAC-SHA256 signature.

    Args:
        body: Raw request body bytes.
        signature: Value of the ``X-HubSpot-Signature`` header.

    Returns:
        True if the signature is valid (or validation is skipped in mock mode).
    """
    if USE_MOCK:
        logger.info("Mock mode — skipping HMAC validation")
        return True

    if not signature:
        logger.warning("Missing X-HubSpot-Signature header")
        return False

    expected = hmac.new(
        HUBSPOT_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    valid = hmac.compare_digest(expected, signature)
    if not valid:
        logger.warning("HMAC signature mismatch")
    return valid


# ---------------------------------------------------------------------------
# Event dispatch (background)
# ---------------------------------------------------------------------------


async def _dispatch_contact_created(event: HubSpotWebhookEvent) -> None:
    """Handle a contact.created event by running the triage pipeline."""
    logger.info(
        "Dispatching contact.created for object %d", event.objectId
    )
    try:
        if USE_MOCK:
            from stage1_awareness.project_demand_gen.main import run_direct_triage

            lead = {
                "email": f"lead-{event.objectId}@example.com",
                "firstname": "New",
                "lastname": "Lead",
                "company": "Unknown Co",
                "industry": "Technology",
                "title": "Marketing Manager",
                "source": "hubspot_webhook",
            }
            result = run_direct_triage(lead)
            logger.info("Triage result: action=%s", result.get("action"))
        else:
            from stage1_awareness.agents.triage_agent import run_triage
            from stage1_awareness.tools.crm_tools import get_contact

            contact = get_contact(f"lead-{event.objectId}@example.com")
            if contact.get("found"):
                lead = {
                    "email": contact["email"],
                    "firstname": contact.get("firstname", ""),
                    "lastname": contact.get("lastname", ""),
                    "company": contact.get("company", ""),
                    "industry": "Technology",
                    "title": "",
                    "source": "hubspot_webhook",
                    "contact_id": contact.get("contact_id", ""),
                }
                result = await run_triage(lead)
                logger.info("Triage result: agent=%s", result.get("agent"))
    except Exception as exc:
        logger.error("Error dispatching contact.created: %s", exc)


async def _dispatch_page_visit(event: HubSpotWebhookEvent) -> None:
    """Handle a page_visit event by re-scoring intent."""
    logger.info(
        "Dispatching page_visit for object %d (page=%s)",
        event.objectId,
        event.propertyValue,
    )
    try:
        from stage1_awareness.tools.intent_scoring import score_intent_signals

        email = f"lead-{event.objectId}@example.com"
        profile = score_intent_signals(email)
        logger.info(
            "Updated intent score for %s: %d (%s)",
            email, profile["score"], profile["tier"],
        )
    except Exception as exc:
        logger.error("Error dispatching page_visit: %s", exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/webhooks/hubspot", response_model=WebhookResponse)
async def receive_hubspot_webhook(
    request: Request,
    x_hubspot_signature: str | None = Header(None),
) -> WebhookResponse:
    """Receive HubSpot webhook events.

    Validates the HMAC signature, acknowledges immediately with HTTP 200,
    and dispatches processing to a background task.
    """
    body = await request.body()

    # Validate signature
    if not _validate_signature(body, x_hubspot_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse events
    try:
        raw_events = json.loads(body)
        if not isinstance(raw_events, list):
            raw_events = [raw_events]
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = [HubSpotWebhookEvent(**e) for e in raw_events]
    logger.info("Received %d webhook event(s)", len(events))

    # Dispatch each event as a background task
    for event in events:
        sub_type = event.subscriptionType
        if sub_type == "contact.creation":
            asyncio.create_task(_dispatch_contact_created(event))
        elif sub_type == "contact.propertyChange" and event.propertyName == "page_visit":
            asyncio.create_task(_dispatch_page_visit(event))
        else:
            logger.info("Ignoring unhandled event type: %s", sub_type)

    return WebhookResponse(
        status="accepted",
        events_received=len(events),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
