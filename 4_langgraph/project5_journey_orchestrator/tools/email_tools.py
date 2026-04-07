# tools/email_tools.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: Email dispatch tools via Klaviyo with mock fallback
# Author: Pushparajan Ramar

"""Email dispatch tools for the customer journey orchestrator.

Provides welcome, nurture, and demo-offer email sending capabilities.
Each function attempts the live Klaviyo API when *USE_MOCK* is False and
*KLAVIYO_API_KEY* is present, otherwise returns a deterministic mock
confirmation.

Environment variables consumed (via .env):
    USE_MOCK         -- "true" (default) or "false"
    KLAVIYO_API_KEY  -- Klaviyo private API key
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
KLAVIYO_API_KEY: str = os.getenv("KLAVIYO_API_KEY", "")

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
# Klaviyo API helper
# ---------------------------------------------------------------------------

def _klaviyo_send_event(
    event_name: str,
    email: str,
    properties: dict[str, Any],
) -> dict[str, Any] | None:
    """Push a track event to Klaviyo.  Returns parsed JSON or None on failure."""
    if USE_MOCK or not KLAVIYO_API_KEY:
        return None
    try:
        import httpx

        payload = {
            "data": {
                "type": "event",
                "attributes": {
                    "metric": {"data": {"type": "metric", "attributes": {"name": event_name}}},
                    "profile": {"data": {"type": "profile", "attributes": {"email": email}}},
                    "properties": properties,
                    "time": _ts(),
                },
            }
        }
        resp = httpx.post(
            "https://a.klaviyo.com/api/events/",
            headers={
                "Authorization": f"Klaviyo-API-Key {KLAVIYO_API_KEY}",
                "Content-Type": "application/json",
                "revision": "2024-10-15",
            },
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {"status": "accepted"}
    except Exception as exc:
        log.warning("Klaviyo API call failed, falling back to mock: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def send_welcome_email(contact: dict[str, Any]) -> dict[str, Any]:
    """Send a welcome email to a new contact via Klaviyo.

    Args:
        contact: Dictionary with at least *email* and *first_name* keys.

    Returns:
        Confirmation dict with email_id, recipient, subject, status, and
        sent_at timestamp.
    """
    email = contact.get("email", "unknown@example.com")
    first_name = contact.get("first_name", "there")
    subject = f"Welcome, {first_name}! Let's get started"

    log.info("send_welcome_email  to=%s  mock=%s  ts=%s", email, USE_MOCK, _ts())

    result = _klaviyo_send_event(
        event_name="Journey Welcome Email",
        email=email,
        properties={"subject": subject, "first_name": first_name},
    )

    if result is not None:
        return {
            "email_id": result.get("data", {}).get("id", _mock_id()),
            "recipient": email,
            "subject": subject,
            "status": "SENT",
            "channel": "email",
            "sent_at": _ts(),
        }

    # ----- mock fallback -----
    log.info("Mock welcome email sent to %s", email)
    return {
        "email_id": f"eml-{_mock_id()}",
        "recipient": email,
        "subject": subject,
        "body_preview": (
            f"Hi {first_name}, welcome aboard! We're excited to help you "
            f"unlock the full potential of your marketing stack. Here's what "
            f"to expect over the next few weeks..."
        ),
        "status": "MOCK_SENT",
        "channel": "email",
        "sent_at": _ts(),
    }


def send_nurture_email(
    contact: dict[str, Any],
    content_type: str = "educational",
) -> dict[str, Any]:
    """Send a nurture email with content tailored to the contact's stage.

    Args:
        contact:      Dictionary with at least *email* and *first_name*.
        content_type: One of "educational", "case_study", "product_update",
                      or "roi_report".

    Returns:
        Confirmation dict with email_id, recipient, subject, content_type,
        status, and sent_at timestamp.
    """
    email = contact.get("email", "unknown@example.com")
    first_name = contact.get("first_name", "there")

    subject_map: dict[str, str] = {
        "educational": f"{first_name}, 3 strategies top marketers swear by",
        "case_study": f"How companies like yours boosted ROI by 40%, {first_name}",
        "product_update": f"{first_name}, see what's new this month",
        "roi_report": f"{first_name}, your personalized ROI snapshot is ready",
    }
    subject = subject_map.get(content_type, subject_map["educational"])

    body_map: dict[str, str] = {
        "educational": (
            f"Hi {first_name},\n\nWe put together a quick guide on the three "
            f"strategies that top-performing marketing teams are using right now "
            f"to drive pipeline growth while reducing manual effort.\n\n"
            f"Read the full guide here: [link]"
        ),
        "case_study": (
            f"Hi {first_name},\n\nSee how a company in your space increased "
            f"qualified leads by 40% in just 90 days using our platform.\n\n"
            f"Read the case study: [link]"
        ),
        "product_update": (
            f"Hi {first_name},\n\nThis month we shipped AI-powered journey "
            f"orchestration, smarter segmentation, and faster reporting.\n\n"
            f"See the highlights: [link]"
        ),
        "roi_report": (
            f"Hi {first_name},\n\nBased on your engagement so far, we've "
            f"prepared a personalized ROI snapshot that estimates the impact "
            f"our platform could have on your marketing KPIs.\n\n"
            f"View your report: [link]"
        ),
    }
    body_preview = body_map.get(content_type, body_map["educational"])

    log.info(
        "send_nurture_email  to=%s  content_type=%s  mock=%s  ts=%s",
        email, content_type, USE_MOCK, _ts(),
    )

    result = _klaviyo_send_event(
        event_name="Journey Nurture Email",
        email=email,
        properties={"subject": subject, "content_type": content_type},
    )

    if result is not None:
        return {
            "email_id": result.get("data", {}).get("id", _mock_id()),
            "recipient": email,
            "subject": subject,
            "content_type": content_type,
            "status": "SENT",
            "channel": "email",
            "sent_at": _ts(),
        }

    # ----- mock fallback -----
    log.info("Mock nurture email (%s) sent to %s", content_type, email)
    return {
        "email_id": f"eml-{_mock_id()}",
        "recipient": email,
        "subject": subject,
        "content_type": content_type,
        "body_preview": body_preview[:120],
        "status": "MOCK_SENT",
        "channel": "email",
        "sent_at": _ts(),
    }


def send_demo_offer(contact: dict[str, Any]) -> dict[str, Any]:
    """Send a demo request offer to a high-engagement lead via Klaviyo.

    Args:
        contact: Dictionary with at least *email* and *first_name*.

    Returns:
        Confirmation dict with email_id, recipient, subject, status, and
        sent_at timestamp.
    """
    email = contact.get("email", "unknown@example.com")
    first_name = contact.get("first_name", "there")
    subject = f"{first_name}, let's schedule your personalized demo"

    log.info("send_demo_offer  to=%s  mock=%s  ts=%s", email, USE_MOCK, _ts())

    result = _klaviyo_send_event(
        event_name="Journey Demo Offer",
        email=email,
        properties={"subject": subject, "offer_type": "demo"},
    )

    if result is not None:
        return {
            "email_id": result.get("data", {}).get("id", _mock_id()),
            "recipient": email,
            "subject": subject,
            "status": "SENT",
            "channel": "email",
            "sent_at": _ts(),
        }

    # ----- mock fallback -----
    log.info("Mock demo offer email sent to %s", email)
    return {
        "email_id": f"eml-{_mock_id()}",
        "recipient": email,
        "subject": subject,
        "body_preview": (
            f"Hi {first_name},\n\nYour engagement tells us you're serious "
            f"about leveling up your marketing stack. We'd love to show you "
            f"exactly how our platform can work for your team.\n\n"
            f"Pick a time that works: [calendar link]"
        ),
        "status": "MOCK_SENT",
        "channel": "demo_offer",
        "sent_at": _ts(),
    }


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("Email Tools — Demo")
    print("=" * 60)
    print(f"USE_MOCK = {USE_MOCK}\n")

    sample = {"email": "sarah.chen@acmesaas.com", "first_name": "Sarah"}

    for label, fn, kwargs in [
        ("Welcome", send_welcome_email, {"contact": sample}),
        ("Nurture (educational)", send_nurture_email, {"contact": sample, "content_type": "educational"}),
        ("Nurture (case_study)", send_nurture_email, {"contact": sample, "content_type": "case_study"}),
        ("Demo Offer", send_demo_offer, {"contact": sample}),
    ]:
        print(f"--- {label} ---")
        print(json.dumps(fn(**kwargs), indent=2))
        print()
