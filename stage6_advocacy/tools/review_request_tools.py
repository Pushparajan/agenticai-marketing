# File      : review_request_tools.py
# Stage     : 6 — Advocacy
# Chapter   : 12
# Framework : MCP + OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Review-request tools for the Advocacy stage.

Manages outbound review requests to G2, Capterra, and similar platforms.
Includes cooldown/throttle logic to avoid over-soliciting customers.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
COOLDOWN_DAYS = int(os.getenv("REVIEW_COOLDOWN_DAYS", "90"))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_REVIEW_HISTORY: dict[str, list[dict[str, Any]]] = {
    "sarah@techcorp.com": [
        {
            "request_id": "REQ-101",
            "platform": "g2",
            "requested_at": "2025-11-10T14:00:00Z",
            "status": "completed",
            "review_url": "https://www.g2.com/products/example/reviews/12345",
        },
    ],
    "james@growthio.com": [
        {
            "request_id": "REQ-102",
            "platform": "capterra",
            "requested_at": "2026-03-25T10:00:00Z",
            "status": "pending",
            "review_url": None,
        },
    ],
    "mei@communityplus.org": [],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _is_within_cooldown(history: list[dict[str, Any]]) -> bool:
    """Check if any request was sent within the cooldown window."""
    cutoff = _now_utc() - timedelta(days=COOLDOWN_DAYS)
    for entry in history:
        req_time = datetime.fromisoformat(
            entry["requested_at"].replace("Z", "+00:00")
        )
        if req_time >= cutoff:
            return True
    return False


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------


def request_g2_review(contact_email: str, personalisation_note: str) -> str:
    """Send a personalised G2 review request to a customer.

    Checks cooldown before sending. Returns error if throttled.

    Args:
        contact_email: Customer email address.
        personalisation_note: A short personalised message for the invite.

    Returns:
        JSON string with request confirmation or throttle notice.
    """
    logger.info("request_g2_review for %s (mock=%s)", contact_email, USE_MOCK)

    # --- Cooldown check ---
    if USE_MOCK:
        history = _MOCK_REVIEW_HISTORY.get(contact_email, [])
    else:
        history = json.loads(get_review_request_history(contact_email))
        history = history.get("history", [])

    if _is_within_cooldown(history):
        return json.dumps({
            "status": "throttled",
            "reason": f"Review request already sent within {COOLDOWN_DAYS} days",
            "contact_email": contact_email,
        })

    request_record = {
        "request_id": str(uuid.uuid4()),
        "platform": "g2",
        "contact_email": contact_email,
        "personalisation_note": personalisation_note,
        "requested_at": _now_utc().isoformat(),
        "status": "sent",
        "g2_invite_url": f"https://www.g2.com/products/example/reviews/new?ref={uuid.uuid4().hex[:8]}",
    }

    if USE_MOCK:
        _MOCK_REVIEW_HISTORY.setdefault(contact_email, []).append(request_record)
        return json.dumps(request_record, default=str)

    try:
        import httpx
        g2_token = os.getenv("G2_API_KEY", "")
        resp = httpx.post(
            "https://api.g2.com/v1/review_requests",
            headers={"Authorization": f"Bearer {g2_token}"},
            json={
                "email": contact_email,
                "note": personalisation_note,
            },
            timeout=10,
        )
        resp.raise_for_status()
        request_record["g2_response"] = resp.json()
        return json.dumps(request_record, default=str)
    except Exception as exc:
        logger.error("G2 review request error: %s", exc)
        request_record["error"] = str(exc)
        return json.dumps(request_record, default=str)


def request_capterra_review(contact_email: str, use_case_angle: str) -> str:
    """Send a Capterra review request with a specific use-case angle.

    Args:
        contact_email: Customer email address.
        use_case_angle: The product use-case to highlight in the review prompt.

    Returns:
        JSON string with request confirmation or throttle notice.
    """
    logger.info("request_capterra_review for %s (mock=%s)", contact_email, USE_MOCK)

    if USE_MOCK:
        history = _MOCK_REVIEW_HISTORY.get(contact_email, [])
    else:
        history = json.loads(get_review_request_history(contact_email))
        history = history.get("history", [])

    if _is_within_cooldown(history):
        return json.dumps({
            "status": "throttled",
            "reason": f"Review request already sent within {COOLDOWN_DAYS} days",
            "contact_email": contact_email,
        })

    request_record = {
        "request_id": str(uuid.uuid4()),
        "platform": "capterra",
        "contact_email": contact_email,
        "use_case_angle": use_case_angle,
        "requested_at": _now_utc().isoformat(),
        "status": "sent",
    }

    if USE_MOCK:
        _MOCK_REVIEW_HISTORY.setdefault(contact_email, []).append(request_record)
        return json.dumps(request_record, default=str)

    try:
        import httpx
        capterra_key = os.getenv("CAPTERRA_API_KEY", "")
        resp = httpx.post(
            "https://api.capterra.com/v1/review_invitations",
            headers={"X-API-Key": capterra_key},
            json={
                "email": contact_email,
                "use_case": use_case_angle,
            },
            timeout=10,
        )
        resp.raise_for_status()
        request_record["capterra_response"] = resp.json()
        return json.dumps(request_record, default=str)
    except Exception as exc:
        logger.error("Capterra review request error: %s", exc)
        request_record["error"] = str(exc)
        return json.dumps(request_record, default=str)


def check_review_request_cooldown(contact_email: str) -> str:
    """Check whether a contact is within the review-request cooldown window.

    Args:
        contact_email: Customer email address.

    Returns:
        JSON string with 'in_cooldown' boolean and details.
    """
    logger.info("check_review_request_cooldown for %s (mock=%s)", contact_email, USE_MOCK)

    if USE_MOCK:
        history = _MOCK_REVIEW_HISTORY.get(contact_email, [])
    else:
        raw = json.loads(get_review_request_history(contact_email))
        history = raw.get("history", [])

    in_cooldown = _is_within_cooldown(history)
    last_request = history[-1] if history else None

    return json.dumps({
        "contact_email": contact_email,
        "in_cooldown": in_cooldown,
        "cooldown_days": COOLDOWN_DAYS,
        "last_request": last_request,
        "checked_at": _now_utc().isoformat(),
    }, default=str)


def get_review_request_history(contact_email: str) -> str:
    """Retrieve the full review-request history for a contact.

    Args:
        contact_email: Customer email address.

    Returns:
        JSON string with list of past review requests.
    """
    logger.info("get_review_request_history for %s (mock=%s)", contact_email, USE_MOCK)

    if USE_MOCK:
        history = _MOCK_REVIEW_HISTORY.get(contact_email, [])
        return json.dumps({
            "contact_email": contact_email,
            "history": history,
            "total": len(history),
        }, default=str)

    try:
        import httpx
        api_url = os.getenv("CRM_API_URL", "https://api.hubspot.com/crm/v3")
        api_key = os.getenv("CRM_API_KEY", "")
        resp = httpx.get(
            f"{api_url}/objects/contacts/search",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"email": contact_email, "properties": "review_requests"},
            timeout=10,
        )
        resp.raise_for_status()
        return json.dumps({
            "contact_email": contact_email,
            "history": resp.json().get("results", []),
        }, default=str)
    except Exception as exc:
        logger.error("Review history API error: %s", exc)
        return json.dumps({"error": str(exc)})
