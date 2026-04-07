# File      : community_invite_tools.py
# Stage     : 6 — Advocacy
# Chapter   : 12
# Framework : MCP + OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Community-invite and case-study tools for the Advocacy stage.

Manages community invitations (Slack, forum, advisory board),
tracks community engagement, and coordinates case-study participation.
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

VALID_COMMUNITY_TYPES = {
    "slack_channel",
    "community_forum",
    "advisory_board",
    "moderator",
    "beta_testers",
}

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_COMMUNITY_ACTIVITY: dict[str, dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "contact_email": "sarah@techcorp.com",
        "communities": ["slack_channel", "community_forum"],
        "posts_last_90_days": 34,
        "helpful_answers": 12,
        "events_attended": 3,
        "is_moderator": False,
        "engagement_score": 85,
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "contact_email": "james@growthio.com",
        "communities": [],
        "posts_last_90_days": 0,
        "helpful_answers": 0,
        "events_attended": 1,
        "is_moderator": False,
        "engagement_score": 10,
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "contact_email": "mei@communityplus.org",
        "communities": ["slack_channel", "community_forum", "advisory_board"],
        "posts_last_90_days": 67,
        "helpful_answers": 28,
        "events_attended": 6,
        "is_moderator": True,
        "engagement_score": 97,
    },
}

_MOCK_CASE_STUDY_LOG: list[dict[str, Any]] = []
_MOCK_INVITE_LOG: list[dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------


def invite_to_community(contact_email: str, community_type: str) -> str:
    """Invite a customer to a specific community channel or group.

    Args:
        contact_email: Customer email address.
        community_type: Type of community — one of 'slack_channel',
            'community_forum', 'advisory_board', 'moderator', 'beta_testers'.

    Returns:
        JSON string with invitation confirmation or error.
    """
    logger.info(
        "invite_to_community %s type=%s (mock=%s)",
        contact_email, community_type, USE_MOCK,
    )

    ctype = community_type.lower().strip()
    if ctype not in VALID_COMMUNITY_TYPES:
        return json.dumps({
            "error": (
                f"Invalid community_type '{community_type}'. "
                f"Must be one of {sorted(VALID_COMMUNITY_TYPES)}."
            )
        })

    invite_record = {
        "invite_id": str(uuid.uuid4()),
        "contact_email": contact_email,
        "community_type": ctype,
        "invited_at": datetime.now(timezone.utc).isoformat(),
        "status": "invitation_sent",
        "join_link": _community_link(ctype),
    }

    if USE_MOCK:
        _MOCK_INVITE_LOG.append(invite_record)
        # Update activity record if it exists
        for record in _MOCK_COMMUNITY_ACTIVITY.values():
            if record["contact_email"] == contact_email:
                if ctype not in record["communities"]:
                    record["communities"].append(ctype)
                break
        return json.dumps(invite_record, default=str)

    try:
        import httpx
        if ctype in ("slack_channel", "moderator"):
            slack_token = os.getenv("SLACK_BOT_TOKEN", "")
            resp = httpx.post(
                "https://slack.com/api/conversations.invite",
                headers={"Authorization": f"Bearer {slack_token}"},
                json={
                    "channel": os.getenv("COMMUNITY_SLACK_CHANNEL", ""),
                    "users": contact_email,
                },
                timeout=10,
            )
            resp.raise_for_status()
            invite_record["slack_response"] = resp.json()
        else:
            webhook = os.getenv("COMMUNITY_INVITE_WEBHOOK", "")
            resp = httpx.post(webhook, json=invite_record, timeout=10)
            resp.raise_for_status()
            invite_record["webhook_status"] = resp.status_code

        return json.dumps(invite_record, default=str)
    except Exception as exc:
        logger.error("Community invite error: %s", exc)
        invite_record["error"] = str(exc)
        return json.dumps(invite_record, default=str)


def get_community_activity(customer_id: str) -> str:
    """Retrieve a customer's community engagement activity.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON string with community membership, post counts, and
        engagement score.
    """
    logger.info("get_community_activity %s (mock=%s)", customer_id, USE_MOCK)

    if USE_MOCK:
        activity = _MOCK_COMMUNITY_ACTIVITY.get(customer_id)
        if activity is None:
            return json.dumps({
                "customer_id": customer_id,
                "communities": [],
                "engagement_score": 0,
                "message": "No community activity found.",
            })
        return json.dumps(activity, default=str)

    try:
        import httpx
        api_url = os.getenv("COMMUNITY_API_URL", "https://api.commsor.com/v1")
        api_key = os.getenv("COMMUNITY_API_KEY", "")
        resp = httpx.get(
            f"{api_url}/members/{customer_id}/activity",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), default=str)
    except Exception as exc:
        logger.error("Community activity error: %s", exc)
        return json.dumps({"error": str(exc)})


def request_case_study_participation(customer_id: str, use_case: str) -> str:
    """Request a customer to participate in a case study.

    Args:
        customer_id: Unique customer identifier.
        use_case: The specific use case or success story to highlight.

    Returns:
        JSON string with case-study request details.
    """
    logger.info(
        "request_case_study_participation %s use_case='%s' (mock=%s)",
        customer_id, use_case, USE_MOCK,
    )

    case_study_request = {
        "request_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "use_case": use_case,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "status": "outreach_sent",
        "next_steps": [
            "Customer receives personalised email from marketing",
            "30-minute discovery call scheduled if accepted",
            "Draft review and approval cycle (2-3 weeks)",
            "Publication on website and social channels",
        ],
        "incentive": "Co-branded promotion + conference speaking slot",
    }

    if USE_MOCK:
        _MOCK_CASE_STUDY_LOG.append(case_study_request)
        return json.dumps(case_study_request, default=str)

    try:
        import httpx
        webhook = os.getenv("CASE_STUDY_WEBHOOK", "")
        resp = httpx.post(webhook, json=case_study_request, timeout=10)
        resp.raise_for_status()
        case_study_request["webhook_status"] = resp.status_code
        return json.dumps(case_study_request, default=str)
    except Exception as exc:
        logger.error("Case study request error: %s", exc)
        case_study_request["error"] = str(exc)
        return json.dumps(case_study_request, default=str)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _community_link(community_type: str) -> str:
    """Generate a join link for the given community type."""
    base_links = {
        "slack_channel": "https://join.slack.com/t/example-community/shared_invite/abc123",
        "community_forum": "https://community.example.com/invite/new-member",
        "advisory_board": "https://community.example.com/advisory-board/apply",
        "moderator": "https://community.example.com/moderator/onboarding",
        "beta_testers": "https://community.example.com/beta/enrol",
    }
    return base_links.get(community_type, "https://community.example.com")
