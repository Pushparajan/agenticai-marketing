# mcp_client.py
# Project 8: Marketing Operations Command Centre (Capstone)
# Chapter Reference: Chapter 6 - MCP (Model Context Protocol)
# Description: MCP client connecting to 6 marketing MCP servers with mock fallback
# Author: Pushparajan Ramar

"""MCP client for the Marketing Operations Command Centre.

Provides a unified interface to six marketing MCP servers:
    - CRM Server        (lead/account management)
    - CDP Server        (audience segmentation, profiles)
    - Email Server      (campaign dispatch, personalisation)
    - Paid Media Server (bid management, campaign creation)
    - Analytics Server  (funnel metrics, attribution)
    - Content Server    (asset generation, approval)

In mock/demo mode the client exposes direct function wrappers that
return deterministic data without requiring running MCP servers.

Environment variables consumed (via .env):
    USE_MOCK          -- "true" (default) or "false"
    OPENAI_API_KEY    -- Required for LLM calls in live mode
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)

# Server executable paths (used in live MCP mode only)
SERVER_PATHS: dict[str, str] = {
    "crm_server": os.getenv("CRM_SERVER_PATH", "servers/crm_server.py"),
    "cdp_server": os.getenv("CDP_SERVER_PATH", "servers/cdp_server.py"),
    "email_server": os.getenv("EMAIL_SERVER_PATH", "servers/email_server.py"),
    "paid_media_server": os.getenv("PAID_MEDIA_SERVER_PATH", "servers/paid_media_server.py"),
    "analytics_server": os.getenv("ANALYTICS_SERVER_PATH", "servers/analytics_server.py"),
    "content_server": os.getenv("CONTENT_SERVER_PATH", "servers/content_server.py"),
}


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mock_id() -> str:
    """Return a short unique identifier for mock objects."""
    return uuid.uuid4().hex[:12]


# ═══════════════════════════════════════════════════════════════════════════
# Mock tool implementations — deterministic data for each MCP server
# ═══════════════════════════════════════════════════════════════════════════


# ---------------------------------------------------------------------------
# CRM Server tools
# ---------------------------------------------------------------------------

def crm_lookup_accounts(industry: str = "enterprise", limit: int = 5) -> str:
    """Look up target accounts by industry segment."""
    accounts = [
        {"account_id": f"acct-{_mock_id()}", "name": name, "industry": industry,
         "arr": arr, "stage": stage, "health_score": hs}
        for name, arr, stage, hs in [
            ("Acme Corp", 2_400_000, "expansion", 87),
            ("GlobalTech Inc", 1_800_000, "prospect", 72),
            ("Nexus Systems", 950_000, "negotiation", 91),
            ("Pinnacle Group", 3_100_000, "renewal", 65),
            ("Vertex Solutions", 1_200_000, "prospect", 78),
        ]
    ][:limit]
    log.info("crm_lookup_accounts  industry=%s  count=%d", industry, len(accounts))
    return json.dumps({"accounts": accounts, "queried_at": _ts()}, indent=2)


def crm_get_pipeline_summary(quarter: str = "Q3") -> str:
    """Get CRM pipeline summary for the given quarter."""
    log.info("crm_get_pipeline_summary  quarter=%s", quarter)
    return json.dumps({
        "quarter": quarter,
        "total_pipeline": 12_750_000,
        "stages": {
            "prospect": {"count": 42, "value": 4_200_000},
            "qualified": {"count": 28, "value": 3_500_000},
            "negotiation": {"count": 15, "value": 2_850_000},
            "closed_won": {"count": 8, "value": 2_200_000},
        },
        "avg_deal_size": 275_000,
        "win_rate": 0.23,
        "avg_cycle_days": 68,
        "queried_at": _ts(),
    }, indent=2)


def crm_create_campaign_record(
    name: str, target_segment: str, budget: float, channel: str,
) -> str:
    """Create a campaign record in the CRM."""
    record_id = f"cmp-{_mock_id()}"
    log.info("crm_create_campaign_record  name=%s  id=%s", name, record_id)
    return json.dumps({
        "campaign_id": record_id, "name": name, "target_segment": target_segment,
        "budget": budget, "channel": channel, "status": "DRAFT",
        "created_at": _ts(),
    }, indent=2)


# ---------------------------------------------------------------------------
# CDP Server tools
# ---------------------------------------------------------------------------

def cdp_get_segment(segment_name: str = "enterprise_high_intent") -> str:
    """Retrieve an audience segment from the CDP."""
    log.info("cdp_get_segment  segment=%s", segment_name)
    return json.dumps({
        "segment_name": segment_name,
        "profile_count": 3_847,
        "top_attributes": {
            "avg_engagement_score": 78.4,
            "avg_page_views_30d": 14.2,
            "pct_demo_requested": 0.32,
            "top_industries": ["SaaS", "FinTech", "HealthTech"],
            "avg_company_size": 2_400,
        },
        "refresh_frequency": "daily",
        "last_refreshed": _ts(),
    }, indent=2)


def cdp_get_profile(email: str = "vp@acmecorp.com") -> str:
    """Get a unified customer profile from the CDP."""
    log.info("cdp_get_profile  email=%s", email)
    return json.dumps({
        "email": email,
        "profile_id": f"prof-{_mock_id()}",
        "first_name": "Jordan",
        "last_name": "Mitchell",
        "title": "VP of Marketing",
        "company": "Acme Corp",
        "engagement_score": 82,
        "lifecycle_stage": "marketing_qualified",
        "preferred_channel": "email",
        "content_affinity": ["ROI reports", "case studies", "webinars"],
        "last_activity": "Downloaded Q2 benchmark report",
        "last_activity_date": _ts(),
    }, indent=2)


def cdp_enrich_audience(segment_name: str, enrichment_type: str = "firmographic") -> str:
    """Enrich a CDP segment with additional data attributes."""
    log.info("cdp_enrich_audience  segment=%s  type=%s", segment_name, enrichment_type)
    return json.dumps({
        "segment_name": segment_name,
        "enrichment_type": enrichment_type,
        "profiles_enriched": 3_412,
        "new_attributes_added": ["tech_stack", "budget_range", "buying_committee_size"],
        "match_rate": 0.89,
        "enriched_at": _ts(),
    }, indent=2)


# ---------------------------------------------------------------------------
# Email Server tools
# ---------------------------------------------------------------------------

def email_create_campaign(
    name: str, segment: str, subject: str, template: str = "enterprise_nurture",
) -> str:
    """Create an email campaign draft."""
    campaign_id = f"emc-{_mock_id()}"
    log.info("email_create_campaign  name=%s  id=%s", name, campaign_id)
    return json.dumps({
        "campaign_id": campaign_id, "name": name, "segment": segment,
        "subject": subject, "template": template, "status": "DRAFT",
        "estimated_recipients": 3_847, "created_at": _ts(),
    }, indent=2)


def email_personalise_content(
    campaign_id: str, personalisation_strategy: str = "dynamic_content",
) -> str:
    """Apply personalisation rules to an email campaign."""
    log.info("email_personalise_content  campaign=%s  strategy=%s",
             campaign_id, personalisation_strategy)
    return json.dumps({
        "campaign_id": campaign_id,
        "strategy": personalisation_strategy,
        "variants_created": 4,
        "variants": [
            {"variant": "A", "industry": "SaaS", "cta": "See SaaS benchmarks"},
            {"variant": "B", "industry": "FinTech", "cta": "Read FinTech case study"},
            {"variant": "C", "industry": "HealthTech", "cta": "Explore compliance tools"},
            {"variant": "D", "industry": "Default", "cta": "Request a demo"},
        ],
        "predicted_lift": 0.18,
        "personalised_at": _ts(),
    }, indent=2)


def email_send_campaign(campaign_id: str, schedule: str = "immediate") -> str:
    """Send or schedule an email campaign (spend-impacting action)."""
    log.info("email_send_campaign  campaign=%s  schedule=%s", campaign_id, schedule)
    return json.dumps({
        "campaign_id": campaign_id, "status": "SCHEDULED" if schedule != "immediate" else "SENDING",
        "recipients": 3_847, "schedule": schedule,
        "estimated_delivery_time": "45 minutes",
        "send_initiated_at": _ts(),
    }, indent=2)


# ---------------------------------------------------------------------------
# Paid Media Server tools
# ---------------------------------------------------------------------------

def paid_media_get_campaigns(platform: str = "linkedin") -> str:
    """Get active paid media campaigns from the specified platform."""
    log.info("paid_media_get_campaigns  platform=%s", platform)
    return json.dumps({
        "platform": platform,
        "campaigns": [
            {"id": f"pm-{_mock_id()}", "name": "Enterprise Pipeline Q3",
             "status": "active", "daily_budget": 850, "spend_mtd": 12_750,
             "impressions": 245_000, "clicks": 3_920, "ctr": 0.016,
             "conversions": 47, "cpa": 271.28, "roas": 3.8},
            {"id": f"pm-{_mock_id()}", "name": "Brand Awareness - FinTech",
             "status": "active", "daily_budget": 500, "spend_mtd": 7_500,
             "impressions": 412_000, "clicks": 2_060, "ctr": 0.005,
             "conversions": 12, "cpa": 625.00, "roas": 1.2},
        ],
        "queried_at": _ts(),
    }, indent=2)


def paid_media_adjust_bids(
    campaign_id: str, adjustment_pct: float, reason: str,
) -> str:
    """Adjust bids for a paid media campaign (spend-impacting action)."""
    log.info("paid_media_adjust_bids  campaign=%s  adj=%.1f%%", campaign_id, adjustment_pct)
    return json.dumps({
        "campaign_id": campaign_id,
        "previous_bid_modifier": 1.0,
        "new_bid_modifier": round(1.0 + adjustment_pct / 100, 3),
        "adjustment_pct": adjustment_pct,
        "reason": reason,
        "effective_daily_budget_change": round(850 * adjustment_pct / 100, 2),
        "status": "APPLIED",
        "applied_at": _ts(),
    }, indent=2)


def paid_media_launch_campaign(
    name: str, platform: str, daily_budget: float, targeting: str,
) -> str:
    """Launch a new paid media campaign (spend-impacting action)."""
    campaign_id = f"pm-{_mock_id()}"
    log.info("paid_media_launch_campaign  name=%s  id=%s  budget=%.2f",
             name, campaign_id, daily_budget)
    return json.dumps({
        "campaign_id": campaign_id, "name": name, "platform": platform,
        "daily_budget": daily_budget, "targeting": targeting,
        "status": "PENDING_REVIEW", "created_at": _ts(),
    }, indent=2)


# ---------------------------------------------------------------------------
# Analytics Server tools
# ---------------------------------------------------------------------------

def analytics_get_funnel(funnel_name: str = "lead_to_demo") -> str:
    """Get funnel conversion metrics from analytics."""
    log.info("analytics_get_funnel  funnel=%s", funnel_name)
    return json.dumps({
        "funnel_name": funnel_name,
        "steps": [
            {"step": 1, "name": "MQL Created", "count": 3_210, "rate": 1.0},
            {"step": 2, "name": "SDR Contacted", "count": 2_568, "rate": 0.80},
            {"step": 3, "name": "Meeting Booked", "count": 1_027, "rate": 0.40},
            {"step": 4, "name": "Demo Completed", "count": 719, "rate": 0.70},
            {"step": 5, "name": "Opportunity Created", "count": 431, "rate": 0.60},
        ],
        "overall_conversion": 0.134,
        "top_dropoff": "SDR Contacted -> Meeting Booked (60% drop)",
        "queried_at": _ts(),
    }, indent=2)


def analytics_get_attribution(model: str = "multi_touch", period: str = "Q3") -> str:
    """Get marketing attribution data."""
    log.info("analytics_get_attribution  model=%s  period=%s", model, period)
    return json.dumps({
        "model": model, "period": period,
        "channels": [
            {"channel": "LinkedIn Ads", "attributed_pipeline": 2_850_000,
             "deals_influenced": 18, "pct_of_total": 0.32},
            {"channel": "Google Organic", "attributed_pipeline": 1_900_000,
             "deals_influenced": 24, "pct_of_total": 0.21},
            {"channel": "Email Nurture", "attributed_pipeline": 1_600_000,
             "deals_influenced": 31, "pct_of_total": 0.18},
            {"channel": "Webinars", "attributed_pipeline": 1_200_000,
             "deals_influenced": 12, "pct_of_total": 0.13},
            {"channel": "Content Syndication", "attributed_pipeline": 850_000,
             "deals_influenced": 9, "pct_of_total": 0.10},
            {"channel": "Direct/Other", "attributed_pipeline": 550_000,
             "deals_influenced": 6, "pct_of_total": 0.06},
        ],
        "total_pipeline": 8_950_000,
        "queried_at": _ts(),
    }, indent=2)


def analytics_get_channel_performance(period: str = "last_30_days") -> str:
    """Get channel-level performance metrics."""
    log.info("analytics_get_channel_performance  period=%s", period)
    return json.dumps({
        "period": period,
        "channels": {
            "linkedin_ads": {"spend": 12_750, "leads": 47, "cpl": 271, "roas": 3.8},
            "google_ads": {"spend": 8_200, "leads": 28, "cpl": 293, "roas": 2.9},
            "email": {"spend": 1_200, "leads": 89, "cpl": 13, "roas": 18.5},
            "content_syndication": {"spend": 5_000, "leads": 34, "cpl": 147, "roas": 4.1},
            "webinars": {"spend": 3_500, "leads": 22, "cpl": 159, "roas": 5.2},
        },
        "total_spend": 30_650,
        "total_leads": 220,
        "blended_cpl": 139.32,
        "queried_at": _ts(),
    }, indent=2)


# ---------------------------------------------------------------------------
# Content Server tools
# ---------------------------------------------------------------------------

def content_generate_brief(
    campaign_name: str, audience: str, tone: str = "professional",
) -> str:
    """Generate a creative brief for campaign content."""
    brief_id = f"brief-{_mock_id()}"
    log.info("content_generate_brief  campaign=%s  id=%s", campaign_name, brief_id)
    return json.dumps({
        "brief_id": brief_id,
        "campaign_name": campaign_name,
        "target_audience": audience,
        "tone": tone,
        "key_messages": [
            "Drive pipeline growth with AI-powered marketing automation",
            "Reduce CAC by 35% through intelligent audience segmentation",
            "Real-time attribution across every touchpoint",
        ],
        "suggested_assets": [
            "Hero email with dynamic industry-specific content",
            "LinkedIn sponsored post with ROI calculator CTA",
            "Landing page with interactive demo booking",
            "Retargeting banner set (3 sizes)",
        ],
        "created_at": _ts(),
    }, indent=2)


def content_approve_asset(asset_id: str, reviewer: str = "marketing_ops") -> str:
    """Approve a content asset for publication."""
    log.info("content_approve_asset  asset=%s  reviewer=%s", asset_id, reviewer)
    return json.dumps({
        "asset_id": asset_id, "reviewer": reviewer,
        "status": "APPROVED",
        "compliance_checks": {"brand_guidelines": "pass", "legal_review": "pass",
                              "accessibility": "pass"},
        "approved_at": _ts(),
    }, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# Tool registry — maps server names to their callable tools
# ═══════════════════════════════════════════════════════════════════════════

ToolFunction = Callable[..., str]

TOOL_REGISTRY: dict[str, dict[str, ToolFunction]] = {
    "crm_server": {
        "crm_lookup_accounts": crm_lookup_accounts,
        "crm_get_pipeline_summary": crm_get_pipeline_summary,
        "crm_create_campaign_record": crm_create_campaign_record,
    },
    "cdp_server": {
        "cdp_get_segment": cdp_get_segment,
        "cdp_get_profile": cdp_get_profile,
        "cdp_enrich_audience": cdp_enrich_audience,
    },
    "email_server": {
        "email_create_campaign": email_create_campaign,
        "email_personalise_content": email_personalise_content,
        "email_send_campaign": email_send_campaign,
    },
    "paid_media_server": {
        "paid_media_get_campaigns": paid_media_get_campaigns,
        "paid_media_adjust_bids": paid_media_adjust_bids,
        "paid_media_launch_campaign": paid_media_launch_campaign,
    },
    "analytics_server": {
        "analytics_get_funnel": analytics_get_funnel,
        "analytics_get_attribution": analytics_get_attribution,
        "analytics_get_channel_performance": analytics_get_channel_performance,
    },
    "content_server": {
        "content_generate_brief": content_generate_brief,
        "content_approve_asset": content_approve_asset,
    },
}

# Flat map for quick lookup by tool name
ALL_TOOLS: dict[str, ToolFunction] = {
    name: fn
    for server_tools in TOOL_REGISTRY.values()
    for name, fn in server_tools.items()
}

# Spend-impacting tools that require HITL approval before execution
SPEND_IMPACTING_TOOLS: set[str] = {
    "email_send_campaign",
    "paid_media_adjust_bids",
    "paid_media_launch_campaign",
}


def get_tools_for_servers(*server_names: str) -> dict[str, ToolFunction]:
    """Return a merged dict of tools from the specified servers.

    Args:
        *server_names: One or more server names from TOOL_REGISTRY.

    Returns:
        Dict mapping tool name to callable function.
    """
    merged: dict[str, ToolFunction] = {}
    for name in server_names:
        if name in TOOL_REGISTRY:
            merged.update(TOOL_REGISTRY[name])
        else:
            log.warning("Unknown server requested: %s", name)
    return merged


def call_tool(tool_name: str, **kwargs: Any) -> str:
    """Call a tool by name, routing to the appropriate mock function.

    Args:
        tool_name: The registered tool name.
        **kwargs:  Keyword arguments passed to the tool function.

    Returns:
        JSON string with the tool result.

    Raises:
        KeyError: If the tool name is not found in the registry.
    """
    if tool_name not in ALL_TOOLS:
        raise KeyError(f"Tool '{tool_name}' not found. Available: {sorted(ALL_TOOLS)}")
    log.info("call_tool  tool=%s  kwargs=%s", tool_name, kwargs)
    return ALL_TOOLS[tool_name](**kwargs)


def is_spend_impacting(tool_name: str) -> bool:
    """Check whether a tool invocation requires human approval."""
    return tool_name in SPEND_IMPACTING_TOOLS


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 72)
    print("  MCP Client — Tool Registry Demo")
    print("=" * 72)
    print(f"\n  USE_MOCK = {USE_MOCK}")
    print(f"  Servers registered:  {len(TOOL_REGISTRY)}")
    print(f"  Total tools:         {len(ALL_TOOLS)}")
    print(f"  Spend-impacting:     {len(SPEND_IMPACTING_TOOLS)}\n")

    for server, tools in TOOL_REGISTRY.items():
        print(f"  [{server}]")
        for tname in tools:
            flag = " (SPEND)" if is_spend_impacting(tname) else ""
            print(f"    - {tname}{flag}")
    print()

    # Quick demo call
    print("--- Demo: crm_get_pipeline_summary ---")
    print(call_tool("crm_get_pipeline_summary", quarter="Q3"))
    print()
    print("--- Demo: cdp_get_segment ---")
    print(call_tool("cdp_get_segment", segment_name="enterprise_high_intent"))
