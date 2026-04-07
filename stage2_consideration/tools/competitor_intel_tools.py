# File      : competitor_intel_tools.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Competitor intelligence tools for the Campaign Intelligence Crew.

Every tool follows the USE_MOCK pattern:
  - When USE_MOCK=true (default), return realistic mock data.
  - When USE_MOCK=false, call the real external API.
"""

from __future__ import annotations

import json
import os

import httpx
from crewai.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


def _http_get(url: str, headers: dict | None = None, params: dict | None = None) -> dict:
    """Perform a GET request with sensible defaults."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=headers or {}, params=params or {})
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Tool 1: Competitor Positioning
# ---------------------------------------------------------------------------
@tool("get_competitor_positioning")
def get_competitor_positioning(competitor: str) -> str:
    """Analyse a competitor's market positioning, messaging, and value props.

    Args:
        competitor: Name of the competitor company.

    Returns:
        JSON string with positioning analysis including messaging themes,
        strengths, weaknesses, and differentiation opportunities.
    """
    if USE_MOCK:
        analysis = {
            "competitor": competitor,
            "tagline": "The all-in-one revenue acceleration platform",
            "primary_messaging_themes": [
                "Unified data for revenue teams",
                "AI-powered pipeline forecasting",
                "Enterprise-grade security and compliance",
            ],
            "target_personas": [
                "VP of Marketing",
                "Revenue Operations Manager",
                "CMO",
            ],
            "strengths": [
                "Strong brand recognition in enterprise segment",
                "Deep Salesforce integration",
                "Large customer success team (150+ CSMs)",
                "SOC 2 Type II and GDPR certified",
            ],
            "weaknesses": [
                "Slow product velocity — major releases only 2x/year",
                "Pricing perceived as expensive for mid-market",
                "Limited API customisation options",
                "No native CDP — requires third-party integration",
            ],
            "pricing_model": "Per-seat + platform fee, starting at $2,500/mo",
            "recent_moves": [
                "Acquired a small ABM start-up in Q1 2026",
                "Launched AI assistant feature in beta",
                "Lost two marquee customers to newer entrants",
            ],
            "differentiation_opportunities": [
                "Position on speed-to-value (onboard in days, not months)",
                "Emphasise native CDP capabilities",
                "Highlight transparent, usage-based pricing",
                "Showcase mid-market customer success stories",
            ],
            "g2_rating": 4.3,
            "g2_review_count": 512,
        }
        return json.dumps(analysis, indent=2)

    # Real API: custom competitive intelligence endpoint
    api_url = os.environ.get("COMPETE_API_URL", "https://api.example.com/compete")
    api_key = os.environ["COMPETE_API_KEY"]
    data = _http_get(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        params={"competitor": competitor},
    )
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: Search Competitor Campaigns
# ---------------------------------------------------------------------------
@tool("search_competitor_campaigns")
def search_competitor_campaigns(industry: str, channel: str) -> str:
    """Search for competitor marketing campaigns in a given industry and channel.

    Args:
        industry: The industry vertical (e.g. 'B2B SaaS').
        channel: Marketing channel to focus on (e.g. 'email', 'linkedin', 'webinar').

    Returns:
        JSON string with competitor campaign examples including messaging,
        formats, and estimated performance.
    """
    if USE_MOCK:
        campaigns = {
            "industry": industry,
            "channel": channel,
            "campaigns": [
                {
                    "competitor": "RivalTech",
                    "campaign_name": "The Revenue Intelligence Playbook",
                    "channel": channel,
                    "format": "6-part email nurture series" if channel == "email"
                        else "Sponsored content series" if channel == "linkedin"
                        else "Live webinar with panel",
                    "messaging_angle": "Data-driven revenue forecasting",
                    "cta": "Download the playbook" if channel != "webinar"
                        else "Register for the live session",
                    "estimated_engagement": "Above average for industry",
                    "notable_tactics": [
                        "Uses personalised dynamic content blocks",
                        "Includes customer quote in every email",
                        "Progressive disclosure of ROI data",
                    ],
                },
                {
                    "competitor": "PlatformX",
                    "campaign_name": "Unify Your Stack Challenge",
                    "channel": channel,
                    "format": "Interactive assessment + follow-up sequence",
                    "messaging_angle": "Tool consolidation and cost savings",
                    "cta": "Take the 5-minute assessment",
                    "estimated_engagement": "High — gamification drives completion",
                    "notable_tactics": [
                        "Personalised results page with benchmark comparison",
                        "Retargeting ads mirror email content themes",
                        "Sales follow-up triggered by high assessment scores",
                    ],
                },
                {
                    "competitor": "GrowthEngine",
                    "campaign_name": "CMO Roundtable Series",
                    "channel": channel,
                    "format": "Invite-only executive roundtable",
                    "messaging_angle": "Peer learning for marketing leaders",
                    "cta": "Request your seat",
                    "estimated_engagement": "Moderate volume, very high quality",
                    "notable_tactics": [
                        "Exclusivity drives FOMO and urgency",
                        "Post-event recap nurture extends value",
                        "Direct AE introductions during event",
                    ],
                },
            ],
            "insights": (
                f"In the {industry} space on {channel}, top-performing campaigns "
                "combine educational value with interactive elements. Personalisation "
                "at the content-block level (not just first name) is table stakes. "
                "The strongest performers include social proof in every touch."
            ),
        }
        return json.dumps(campaigns, indent=2)

    # Real API: SEMRush or SpyFu campaign data
    api_key = os.environ["SEMRUSH_API_KEY"]
    data = _http_get(
        "https://api.semrush.com/analytics/v1/",
        params={
            "key": api_key,
            "type": "advertising_competitors",
            "domain": f"{industry.lower().replace(' ', '')}.com",
            "database": "us",
        },
    )
    return json.dumps(
        {"industry": industry, "channel": channel, "raw_data": data},
        indent=2,
    )
