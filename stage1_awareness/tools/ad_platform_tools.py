# File      : ad_platform_tools.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Ad-platform integration tools.

Retrieve click context from Google / Meta Ads and manage retargeting
audiences, with automatic mock fallback.
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

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_CLICKS: dict[str, dict[str, Any]] = {
    "gclid_abc123": {
        "click_id": "gclid_abc123",
        "platform": "google_ads",
        "campaign": "Awareness_SaaS_Q2",
        "ad_group": "ICP_Enterprise",
        "keyword": "enterprise workflow automation",
        "landing_page": "https://example.com/demo?ref=google",
        "clicked_at": "2026-04-06T14:22:00Z",
        "cost_usd": 4.50,
    },
    "fbclid_xyz789": {
        "click_id": "fbclid_xyz789",
        "platform": "meta_ads",
        "campaign": "Retarget_WebVisitors",
        "ad_group": "Lookalike_1pct",
        "keyword": None,
        "landing_page": "https://example.com/case-study?ref=meta",
        "clicked_at": "2026-04-06T16:05:00Z",
        "cost_usd": 2.10,
    },
}

_mock_audiences: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# get_ad_click_context
# ---------------------------------------------------------------------------

def _get_click_real(click_id: str) -> dict[str, Any]:
    """Query Google Ads / Meta Ads API for click-level data."""
    import httpx

    google_token = os.getenv("GOOGLE_ADS_TOKEN", "")
    meta_token = os.getenv("META_ADS_TOKEN", "")

    # Try Google Ads first
    if click_id.startswith("gclid"):
        try:
            resp = httpx.post(
                "https://googleads.googleapis.com/v16/customers/-/googleAds:searchStream",
                json={
                    "query": (
                        f"SELECT click_view.gclid, campaign.name, "
                        f"ad_group.name, segments.keyword.info.text "
                        f"FROM click_view "
                        f"WHERE click_view.gclid = '{click_id}'"
                    )
                },
                headers={"Authorization": f"Bearer {google_token}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            row = data[0]["results"][0] if data else {}
            return {
                "click_id": click_id,
                "platform": "google_ads",
                "campaign": row.get("campaign", {}).get("name", ""),
                "keyword": row.get("segments", {}).get("keyword", {}).get("info", {}).get("text", ""),
                "landing_page": "",
            }
        except Exception as exc:
            logger.error("Google Ads API error: %s", exc)
            return {"click_id": click_id, "error": str(exc)}

    # Meta Ads
    try:
        resp = httpx.get(
            f"https://graph.facebook.com/v19.0/{click_id}",
            params={"access_token": meta_token},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "click_id": click_id,
            "platform": "meta_ads",
            "campaign": data.get("campaign_name", ""),
            "keyword": None,
            "landing_page": data.get("landing_page_url", ""),
        }
    except Exception as exc:
        logger.error("Meta Ads API error: %s", exc)
        return {"click_id": click_id, "error": str(exc)}


def _get_click_mock(click_id: str) -> dict[str, Any]:
    """Return mock click context."""
    return _MOCK_CLICKS.get(
        click_id,
        {"click_id": click_id, "error": "Click ID not found"},
    )


def get_ad_click_context(click_id: str) -> dict[str, Any]:
    """Retrieve campaign context for an ad click.

    Args:
        click_id: The platform click identifier (gclid / fbclid).

    Returns:
        Dict with campaign, keyword, landing_page, platform, etc.
    """
    logger.info("Fetching ad click context for %s (mock=%s)", click_id, USE_MOCK)
    if USE_MOCK:
        return _get_click_mock(click_id)
    return _get_click_real(click_id)


# ---------------------------------------------------------------------------
# create_retargeting_audience
# ---------------------------------------------------------------------------

def _create_audience_real(segment_name: str, contacts: list[str]) -> dict[str, Any]:
    """Create a custom audience on Meta Ads for retargeting."""
    import httpx

    meta_token = os.getenv("META_ADS_TOKEN", "")
    ad_account_id = os.getenv("META_AD_ACCOUNT_ID", "")
    try:
        resp = httpx.post(
            f"https://graph.facebook.com/v19.0/{ad_account_id}/customaudiences",
            json={
                "name": segment_name,
                "subtype": "CUSTOM",
                "customer_file_source": "USER_PROVIDED_ONLY",
            },
            params={"access_token": meta_token},
            timeout=15,
        )
        resp.raise_for_status()
        audience_id = resp.json().get("id", "")
        # Add users
        httpx.post(
            f"https://graph.facebook.com/v19.0/{audience_id}/users",
            json={"payload": {"schema": "EMAIL", "data": contacts}},
            params={"access_token": meta_token},
            timeout=15,
        )
        return {
            "audience_id": audience_id,
            "segment_name": segment_name,
            "contact_count": len(contacts),
            "created": True,
        }
    except Exception as exc:
        logger.error("Meta Ads audience creation error: %s", exc)
        return {"segment_name": segment_name, "error": str(exc)}


def _create_audience_mock(segment_name: str, contacts: list[str]) -> dict[str, Any]:
    """Create a mock retargeting audience."""
    audience = {
        "audience_id": f"aud_{uuid.uuid4().hex[:8]}",
        "segment_name": segment_name,
        "contact_count": len(contacts),
        "contacts": contacts,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created": True,
    }
    _mock_audiences.append(audience)
    return audience


def create_retargeting_audience(
    segment_name: str,
    contacts: list[str],
) -> dict[str, Any]:
    """Create a retargeting audience segment on the ad platform.

    Args:
        segment_name: Human-readable name for the audience segment.
        contacts: List of email addresses to include.

    Returns:
        Dict with ``audience_id``, ``contact_count``, and ``created`` flag.
    """
    logger.info(
        "Creating retargeting audience '%s' with %d contacts (mock=%s)",
        segment_name, len(contacts), USE_MOCK,
    )
    if USE_MOCK:
        return _create_audience_mock(segment_name, contacts)
    return _create_audience_real(segment_name, contacts)
