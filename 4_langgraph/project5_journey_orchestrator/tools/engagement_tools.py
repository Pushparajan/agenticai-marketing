# tools/engagement_tools.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: CDP / CRM engagement signal retrieval with mock fallback
# Author: Pushparajan Ramar

"""Engagement evaluation tools for the customer journey orchestrator.

Reads engagement signals -- email opens, page views, form fills, and a
composite score -- from a CDP or CRM.  When *USE_MOCK* is true (the
default) or the API key is absent, the tool returns deterministic mock
data that exercises realistic scoring patterns.

Environment variables consumed (via .env):
    USE_MOCK         -- "true" (default) or "false"
    CDP_API_KEY      -- API key for the Customer Data Platform
    CDP_API_BASE_URL -- Base URL for the CDP REST API
"""

from __future__ import annotations

import logging
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
CDP_API_KEY: str = os.getenv("CDP_API_KEY", "")
CDP_API_BASE_URL: str = os.getenv("CDP_API_BASE_URL", "https://api.cdp.example.com")

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
# Mock engagement profiles
# ---------------------------------------------------------------------------
_MOCK_PROFILES: dict[str, dict[str, Any]] = {
    "contact-high-001": {
        "email_opens": 12,
        "page_views": 34,
        "form_fills": 3,
        "webinar_attended": True,
        "demo_requested": True,
        "engagement_score": 88,
        "lifecycle_stage": "opportunity",
    },
    "contact-mid-002": {
        "email_opens": 6,
        "page_views": 15,
        "form_fills": 1,
        "webinar_attended": False,
        "demo_requested": False,
        "engagement_score": 55,
        "lifecycle_stage": "marketingqualifiedlead",
    },
    "contact-low-003": {
        "email_opens": 1,
        "page_views": 3,
        "form_fills": 0,
        "webinar_attended": False,
        "demo_requested": False,
        "engagement_score": 18,
        "lifecycle_stage": "lead",
    },
}


def _generate_fallback_profile(contact_id: str) -> dict[str, Any]:
    """Build a plausible engagement profile for an unknown contact_id."""
    seed = hash(contact_id) % 100
    return {
        "email_opens": seed % 15,
        "page_views": (seed * 3) % 40,
        "form_fills": seed % 4,
        "webinar_attended": seed > 70,
        "demo_requested": seed > 85,
        "engagement_score": seed,
        "lifecycle_stage": (
            "opportunity" if seed >= 80
            else "marketingqualifiedlead" if seed >= 50
            else "lead"
        ),
    }


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------

def evaluate_engagement(contact_id: str) -> dict[str, Any]:
    """Read engagement signals from the CDP / CRM for *contact_id*.

    Attempts a live API call when *USE_MOCK* is False and *CDP_API_KEY* is
    set.  Otherwise returns realistic mock data.

    Args:
        contact_id: Unique contact identifier in the CDP/CRM.

    Returns:
        Dictionary containing:
            - contact_id
            - email_opens, page_views, form_fills (int counts)
            - webinar_attended, demo_requested (bool flags)
            - engagement_score (0-100 composite)
            - lifecycle_stage
            - evaluated_at (ISO timestamp)
    """
    log.info(
        "evaluate_engagement  contact_id=%s  mock=%s  ts=%s",
        contact_id, USE_MOCK, _ts(),
    )

    # ----- live API path -----
    if not USE_MOCK and CDP_API_KEY:
        try:
            import httpx

            resp = httpx.get(
                f"{CDP_API_BASE_URL}/v1/contacts/{contact_id}/engagement",
                headers={"Authorization": f"Bearer {CDP_API_KEY}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "contact_id": contact_id,
                "email_opens": data.get("email_opens", 0),
                "page_views": data.get("page_views", 0),
                "form_fills": data.get("form_fills", 0),
                "webinar_attended": data.get("webinar_attended", False),
                "demo_requested": data.get("demo_requested", False),
                "engagement_score": data.get("engagement_score", 0),
                "lifecycle_stage": data.get("lifecycle_stage", "lead"),
                "evaluated_at": _ts(),
            }
        except Exception as exc:
            log.warning("CDP API call failed, falling back to mock: %s", exc)

    # ----- mock fallback -----
    profile = _MOCK_PROFILES.get(
        contact_id,
        _generate_fallback_profile(contact_id),
    )
    log.info(
        "Mock engagement for %s: score=%d  stage=%s",
        contact_id, profile["engagement_score"], profile["lifecycle_stage"],
    )
    return {
        "contact_id": contact_id,
        **profile,
        "evaluated_at": _ts(),
    }


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("Engagement Tools — Demo")
    print("=" * 60)
    print(f"USE_MOCK = {USE_MOCK}\n")

    for cid in ["contact-high-001", "contact-mid-002", "contact-low-003", "contact-unknown-999"]:
        result = evaluate_engagement(cid)
        print(f"--- {cid} ---")
        print(json.dumps(result, indent=2))
        print()
