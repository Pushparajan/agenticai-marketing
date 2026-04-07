# tools/segment_cdp.py
# Project 3: Campaign Intelligence Crew
# Chapter Reference: Chapter 3 - CrewAI
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
#
# Segment CDP query tool — retrieves audience segment data including
# demographics, behavioral signals, and engagement metrics.
# Falls back to realistic mock data when USE_MOCK is enabled.

"""Segment CDP audience query tool with mock fallback.

Queries the Twilio Segment Profiles API for audience segment data.
When USE_MOCK is true (default) or the API key is absent, returns
pre-built realistic audience profiles for demonstration.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
SEGMENT_API_KEY: str = os.getenv("SEGMENT_API_KEY", "")
SEGMENT_SPACE_ID: str = os.getenv("SEGMENT_SPACE_ID", "")

logger = logging.getLogger("campaign_intel.tools.segment_cdp")

# ---------------------------------------------------------------------------
# Mock audience data
# ---------------------------------------------------------------------------
MOCK_AUDIENCES: dict[str, dict] = {
    "high_value_saas_buyers": {
        "segment_name": "High-Value SaaS Buyers",
        "segment_id": "seg_hv_saas_001",
        "total_profiles": 24_850,
        "growth_30d_pct": 12.3,
        "last_computed": "2026-04-06T08:00:00Z",
        "demographics": {
            "age_distribution": {
                "25-34": 28,
                "35-44": 41,
                "45-54": 22,
                "55+": 9,
            },
            "gender_split": {"male": 54, "female": 43, "non_binary_or_undisclosed": 3},
            "top_job_titles": [
                "VP of Marketing",
                "Head of Growth",
                "CMO",
                "Director of Demand Generation",
                "Marketing Operations Manager",
            ],
            "company_size_distribution": {
                "1-50": 8,
                "51-200": 22,
                "201-1000": 38,
                "1001-5000": 24,
                "5000+": 8,
            },
            "top_industries": [
                "SaaS / Cloud Software",
                "FinTech",
                "E-Commerce",
                "Healthcare IT",
                "AdTech / MarTech",
            ],
            "household_income_median_usd": 165_000,
            "education": {"bachelors": 42, "masters_mba": 48, "phd": 5, "other": 5},
            "top_geographies": [
                {"region": "US - West Coast", "pct": 32},
                {"region": "US - East Coast", "pct": 28},
                {"region": "UK / Ireland", "pct": 14},
                {"region": "DACH (Germany/Austria/Switzerland)", "pct": 10},
                {"region": "Canada", "pct": 8},
                {"region": "Other", "pct": 8},
            ],
        },
        "behavioral_signals": {
            "avg_sessions_per_month": 8.4,
            "avg_pages_per_session": 5.2,
            "top_content_categories": [
                "Product comparisons",
                "ROI calculators",
                "Case studies",
                "Integration guides",
                "Pricing pages",
            ],
            "preferred_channels": [
                {"channel": "Email", "engagement_rate_pct": 34.2},
                {"channel": "LinkedIn", "engagement_rate_pct": 28.7},
                {"channel": "Organic Search", "engagement_rate_pct": 18.5},
                {"channel": "Webinars", "engagement_rate_pct": 12.1},
                {"channel": "Paid Search", "engagement_rate_pct": 6.5},
            ],
            "buying_triggers": [
                "Contract renewal window (Q3-Q4)",
                "Headcount growth > 20% YoY",
                "New VP/C-level marketing hire",
                "Competitor displacement event",
                "Budget planning cycle (Oct-Dec)",
            ],
            "avg_deal_cycle_days": 62,
            "avg_contract_value_usd": 48_500,
        },
        "psychographics": {
            "motivations": [
                "Proving marketing ROI to the C-suite",
                "Consolidating martech stack to reduce costs",
                "Scaling personalization without adding headcount",
                "Gaining competitive advantage through data-driven decisions",
            ],
            "pain_points": [
                "Fragmented data across 8+ tools",
                "Attribution remains a black box",
                "Manual reporting consumes 15+ hrs/week",
                "Difficulty aligning sales and marketing on pipeline metrics",
            ],
            "aspirations": [
                "Single source of truth for customer journey",
                "Automated campaign optimization",
                "Board-ready analytics dashboards",
                "AI-powered audience discovery",
            ],
        },
        "engagement_scores": {
            "highly_engaged_pct": 31,
            "moderately_engaged_pct": 44,
            "low_engagement_pct": 25,
        },
    },
    "enterprise_decision_makers": {
        "segment_name": "Enterprise Decision Makers",
        "segment_id": "seg_edm_002",
        "total_profiles": 8_720,
        "growth_30d_pct": 6.8,
        "last_computed": "2026-04-06T08:00:00Z",
        "demographics": {
            "age_distribution": {
                "35-44": 32,
                "45-54": 42,
                "55+": 26,
            },
            "gender_split": {"male": 58, "female": 39, "non_binary_or_undisclosed": 3},
            "top_job_titles": [
                "Chief Marketing Officer",
                "Chief Digital Officer",
                "SVP of Marketing",
                "VP of Digital Strategy",
                "Head of MarTech",
            ],
            "company_size_distribution": {
                "1001-5000": 35,
                "5000-20000": 40,
                "20000+": 25,
            },
            "top_industries": [
                "Financial Services",
                "Retail / CPG",
                "Technology",
                "Healthcare / Pharma",
                "Telecommunications",
            ],
            "household_income_median_usd": 285_000,
            "education": {"bachelors": 25, "masters_mba": 62, "phd": 8, "other": 5},
            "top_geographies": [
                {"region": "US - Northeast", "pct": 30},
                {"region": "US - West Coast", "pct": 22},
                {"region": "UK / Western Europe", "pct": 20},
                {"region": "Asia-Pacific", "pct": 15},
                {"region": "Other", "pct": 13},
            ],
        },
        "behavioral_signals": {
            "avg_sessions_per_month": 4.1,
            "avg_pages_per_session": 3.8,
            "top_content_categories": [
                "Executive briefs",
                "Analyst reports (Gartner/Forrester)",
                "Customer success stories",
                "Security & compliance docs",
                "Platform architecture overviews",
            ],
            "preferred_channels": [
                {"channel": "Email", "engagement_rate_pct": 22.8},
                {"channel": "LinkedIn", "engagement_rate_pct": 31.5},
                {"channel": "Events / Conferences", "engagement_rate_pct": 24.2},
                {"channel": "Direct Sales", "engagement_rate_pct": 15.3},
                {"channel": "Analyst referrals", "engagement_rate_pct": 6.2},
            ],
            "buying_triggers": [
                "Board mandate for digital transformation",
                "M&A activity requiring platform consolidation",
                "Competitive pressure from digital-native disruptors",
                "Regulatory changes requiring new data capabilities",
                "Annual strategic planning cycle (Q4)",
            ],
            "avg_deal_cycle_days": 128,
            "avg_contract_value_usd": 285_000,
        },
        "psychographics": {
            "motivations": [
                "Demonstrating innovation leadership to the board",
                "Driving measurable revenue impact from marketing",
                "Future-proofing the martech architecture",
                "Attracting and retaining top marketing talent",
            ],
            "pain_points": [
                "Legacy systems creating data silos",
                "Vendor sprawl with 20+ marketing tools",
                "Inability to measure cross-channel attribution",
                "Slow time-to-insight from current BI stack",
            ],
            "aspirations": [
                "Unified customer data platform",
                "Real-time decisioning at scale",
                "AI-first marketing operations",
                "Predictive revenue forecasting",
            ],
        },
        "engagement_scores": {
            "highly_engaged_pct": 18,
            "moderately_engaged_pct": 47,
            "low_engagement_pct": 35,
        },
    },
}

# Default fallback for unknown audience names
_DEFAULT_AUDIENCE: dict = {
    "segment_name": "General Marketing Audience",
    "segment_id": "seg_gen_999",
    "total_profiles": 15_400,
    "growth_30d_pct": 4.5,
    "last_computed": "2026-04-06T08:00:00Z",
    "demographics": {
        "age_distribution": {"25-34": 30, "35-44": 35, "45-54": 25, "55+": 10},
        "gender_split": {"male": 50, "female": 47, "non_binary_or_undisclosed": 3},
        "top_job_titles": [
            "Marketing Manager",
            "Digital Marketing Specialist",
            "Content Strategist",
            "Growth Marketing Lead",
            "Brand Manager",
        ],
        "company_size_distribution": {"1-50": 15, "51-200": 30, "201-1000": 35, "1001+": 20},
        "top_industries": ["Technology", "Retail", "Financial Services", "Healthcare", "Media"],
        "household_income_median_usd": 120_000,
        "education": {"bachelors": 50, "masters_mba": 38, "phd": 4, "other": 8},
        "top_geographies": [
            {"region": "US", "pct": 55},
            {"region": "Europe", "pct": 25},
            {"region": "Asia-Pacific", "pct": 12},
            {"region": "Other", "pct": 8},
        ],
    },
    "behavioral_signals": {
        "avg_sessions_per_month": 6.0,
        "avg_pages_per_session": 4.5,
        "top_content_categories": [
            "Blog posts",
            "Webinars",
            "Product pages",
            "Case studies",
            "Newsletters",
        ],
        "preferred_channels": [
            {"channel": "Email", "engagement_rate_pct": 28.0},
            {"channel": "Social Media", "engagement_rate_pct": 25.0},
            {"channel": "Organic Search", "engagement_rate_pct": 22.0},
            {"channel": "Paid Ads", "engagement_rate_pct": 15.0},
            {"channel": "Referrals", "engagement_rate_pct": 10.0},
        ],
        "buying_triggers": [
            "Budget approval cycle",
            "Team expansion",
            "Pain point escalation",
            "Competitor switch",
        ],
        "avg_deal_cycle_days": 45,
        "avg_contract_value_usd": 25_000,
    },
    "psychographics": {
        "motivations": [
            "Improving campaign performance",
            "Reducing manual work",
            "Better data visibility",
        ],
        "pain_points": [
            "Tool fragmentation",
            "Limited analytics",
            "Time-consuming reporting",
        ],
        "aspirations": [
            "Unified marketing platform",
            "Data-driven decision making",
            "Automated workflows",
        ],
    },
    "engagement_scores": {
        "highly_engaged_pct": 22,
        "moderately_engaged_pct": 48,
        "low_engagement_pct": 30,
    },
}


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_key(audience_name: str) -> str:
    """Convert an audience display name to a lookup key."""
    return audience_name.strip().lower().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# CrewAI Tool
# ---------------------------------------------------------------------------

@tool("query_segment_cdp")
def query_segment_cdp(audience_name: str) -> str:
    """Query the Segment CDP for audience segment data.

    Retrieves demographics, behavioral signals, psychographics, and
    engagement metrics for the specified audience segment.

    Args:
        audience_name: Name of the audience segment to query
            (e.g. "high_value_saas_buyers", "enterprise_decision_makers").

    Returns:
        JSON string with full audience segment profile.
    """
    logger.info(
        "query_segment_cdp called | audience=%s | mock=%s | ts=%s",
        audience_name, USE_MOCK, _ts(),
    )

    # ---- Live Segment API path (when configured) ----
    if not USE_MOCK and SEGMENT_API_KEY and SEGMENT_SPACE_ID:
        try:
            import requests

            url = (
                f"https://profiles.segment.com/v1/spaces/{SEGMENT_SPACE_ID}"
                f"/collections/users/profiles"
            )
            resp = requests.get(
                url,
                auth=(SEGMENT_API_KEY, ""),
                params={"class": "audience", "name": audience_name, "limit": 1},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("Segment CDP returned live data for audience=%s", audience_name)
            return json.dumps(data, indent=2)
        except Exception as exc:
            logger.warning("Segment API error, falling back to mock: %s", exc)

    # ---- Mock fallback ----
    key = _normalize_key(audience_name)
    audience = MOCK_AUDIENCES.get(key, _DEFAULT_AUDIENCE.copy())

    # Customize the default with the requested name if it was a fallback
    if key not in MOCK_AUDIENCES:
        audience["segment_name"] = audience_name.replace("_", " ").title()
        audience["segment_id"] = f"seg_{key[:10]}_{hash(key) % 1000:03d}"

    logger.info(
        "Returning mock CDP data | audience=%s | profiles=%d",
        audience["segment_name"], audience["total_profiles"],
    )
    return json.dumps(audience, indent=2)


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Segment CDP Tool — Demo")
    print("=" * 60)
    for name in ["high_value_saas_buyers", "enterprise_decision_makers", "unknown_test"]:
        print(f"\n--- Audience: {name} ---")
        result = query_segment_cdp.run(audience_name=name)
        parsed = json.loads(result)
        print(f"  Segment: {parsed['segment_name']}")
        print(f"  Profiles: {parsed['total_profiles']:,}")
        print(f"  30-day growth: {parsed['growth_30d_pct']}%")
