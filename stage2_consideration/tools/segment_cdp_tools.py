# File      : segment_cdp_tools.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Segment CDP tools for the Campaign Intelligence Crew.

Every tool follows the USE_MOCK pattern:
  - When USE_MOCK=true (default), return realistic mock data.
  - When USE_MOCK=false, call the real Segment API.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import httpx
from crewai.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


def _http_get(url: str, headers: dict | None = None, params: dict | None = None) -> dict:
    """Perform a GET request with sensible defaults."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=headers or {}, params=params or {})
        resp.raise_for_status()
        return resp.json()


def _segment_headers() -> dict:
    """Return authorization headers for Segment API."""
    token = os.environ["SEGMENT_ACCESS_TOKEN"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Tool 1: Query Segment CDP
# ---------------------------------------------------------------------------
@tool("query_segment_cdp")
def query_segment_cdp(audience_name: str) -> str:
    """Query the Segment CDP for an audience/segment and return its profile.

    Args:
        audience_name: Name of the audience or segment to query
            (e.g. 'high_intent_mql', 'enterprise_evaluators').

    Returns:
        JSON string with audience metadata, size, top traits, and sample
        profiles.
    """
    if USE_MOCK:
        audience = {
            "audience_name": audience_name,
            "audience_id": "aud_2xK9mR4vLp",
            "status": "active",
            "size": 1_247,
            "created_at": "2026-01-15T09:00:00Z",
            "last_computed": datetime.now().isoformat(),
            "definition": {
                "conditions": [
                    {"trait": "lifecycle_stage", "operator": "equals", "value": "MQL"},
                    {"event": "page_viewed", "count_gte": 5, "within_days": 30},
                    {"trait": "company_size", "operator": "gte", "value": 50},
                ],
            },
            "top_traits": {
                "avg_page_views_30d": 12.4,
                "avg_content_downloads": 2.8,
                "top_industries": ["B2B SaaS", "FinTech", "HealthTech"],
                "top_company_sizes": ["51-200", "201-500", "501-1000"],
                "avg_intent_score": 72.5,
            },
            "sample_profiles": [
                {
                    "email": "alex.rivera@acmecorp.com",
                    "name": "Alex Rivera",
                    "company": "Acme Corp",
                    "title": "VP of Marketing",
                    "intent_score": 85,
                },
                {
                    "email": "jordan.lee@techstart.io",
                    "name": "Jordan Lee",
                    "company": "TechStart",
                    "title": "Head of Growth",
                    "intent_score": 68,
                },
                {
                    "email": "sam.patel@finserve.com",
                    "name": "Sam Patel",
                    "company": "FinServe",
                    "title": "Marketing Director",
                    "intent_score": 74,
                },
            ],
        }
        return json.dumps(audience, indent=2)

    # Real API: Segment Profiles API
    space_id = os.environ["SEGMENT_SPACE_ID"]
    data = _http_get(
        f"https://profiles.segment.com/v1/spaces/{space_id}/collections/users/audiences/{audience_name}",
        headers=_segment_headers(),
    )
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: Get Contact Journey Events
# ---------------------------------------------------------------------------
@tool("get_contact_journey_events")
def get_contact_journey_events(email: str) -> str:
    """Retrieve the journey event timeline for a specific contact from the CDP.

    Args:
        email: The contact's email address.

    Returns:
        JSON string with an ordered list of journey events including
        timestamps, event types, and metadata.
    """
    if USE_MOCK:
        now = datetime.now()
        events = {
            "email": email,
            "profile_id": "prof_8xN3kW2qRt",
            "total_events": 14,
            "events": [
                {
                    "event": "page_viewed",
                    "page": "/pricing",
                    "timestamp": (now - timedelta(days=21)).isoformat(),
                    "source": "website",
                },
                {
                    "event": "content_downloaded",
                    "asset": "B2B Marketing Automation Buyers Guide",
                    "timestamp": (now - timedelta(days=18)).isoformat(),
                    "source": "website",
                },
                {
                    "event": "email_opened",
                    "campaign": "nurture_welcome_series",
                    "email_id": "em_001",
                    "timestamp": (now - timedelta(days=16)).isoformat(),
                    "source": "klaviyo",
                },
                {
                    "event": "email_clicked",
                    "campaign": "nurture_welcome_series",
                    "email_id": "em_001",
                    "link": "/case-study/fintech",
                    "timestamp": (now - timedelta(days=16)).isoformat(),
                    "source": "klaviyo",
                },
                {
                    "event": "page_viewed",
                    "page": "/case-study/fintech",
                    "timestamp": (now - timedelta(days=16)).isoformat(),
                    "source": "website",
                    "time_on_page_seconds": 245,
                },
                {
                    "event": "page_viewed",
                    "page": "/product/integrations",
                    "timestamp": (now - timedelta(days=14)).isoformat(),
                    "source": "website",
                },
                {
                    "event": "webinar_registered",
                    "webinar": "AI in Marketing: 2026 Playbook",
                    "timestamp": (now - timedelta(days=12)).isoformat(),
                    "source": "website",
                },
                {
                    "event": "webinar_attended",
                    "webinar": "AI in Marketing: 2026 Playbook",
                    "duration_minutes": 38,
                    "timestamp": (now - timedelta(days=10)).isoformat(),
                    "source": "zoom",
                },
                {
                    "event": "email_opened",
                    "campaign": "nurture_mid_funnel",
                    "email_id": "em_005",
                    "timestamp": (now - timedelta(days=7)).isoformat(),
                    "source": "klaviyo",
                },
                {
                    "event": "page_viewed",
                    "page": "/pricing",
                    "timestamp": (now - timedelta(days=5)).isoformat(),
                    "source": "website",
                    "time_on_page_seconds": 312,
                },
                {
                    "event": "form_submitted",
                    "form": "request_demo",
                    "timestamp": (now - timedelta(days=3)).isoformat(),
                    "source": "website",
                },
            ],
            "journey_summary": {
                "first_touch": (now - timedelta(days=21)).isoformat()[:10],
                "last_touch": (now - timedelta(days=3)).isoformat()[:10],
                "total_page_views": 8,
                "total_content_downloads": 1,
                "total_emails_opened": 2,
                "total_emails_clicked": 1,
                "webinars_attended": 1,
                "forms_submitted": 1,
                "current_stage": "MQL — demo requested",
            },
        }
        return json.dumps(events, indent=2)

    # Real API: Segment Profile Events
    space_id = os.environ["SEGMENT_SPACE_ID"]
    data = _http_get(
        f"https://profiles.segment.com/v1/spaces/{space_id}/collections/users/profiles/email:{email}/events",
        headers=_segment_headers(),
        params={"limit": 50},
    )
    return json.dumps(data, indent=2)
