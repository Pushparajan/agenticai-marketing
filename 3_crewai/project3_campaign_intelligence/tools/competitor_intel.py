# tools/competitor_intel.py
# Project 3: Campaign Intelligence Crew
# Chapter Reference: Chapter 3 - CrewAI
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
#
# Competitive intelligence tool — searches for competitor campaign data
# across specified industries and channels.
# Falls back to realistic mock data when USE_MOCK is enabled.

"""Competitive intelligence search tool with mock fallback.

Searches the web (via SerpAPI or similar) for competitor campaign
activity in a given industry and channel.  When USE_MOCK is true
(default) or the API key is absent, returns pre-built realistic
competitor campaign data for demonstration.
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
SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")

logger = logging.getLogger("campaign_intel.tools.competitor_intel")

# ---------------------------------------------------------------------------
# Mock competitor data
# ---------------------------------------------------------------------------
MOCK_COMPETITOR_DATA: dict[str, dict[str, list[dict]]] = {
    "saas": {
        "email": [
            {
                "competitor": "HubSpot",
                "campaign_name": "Grow Better 2026",
                "channel": "Email",
                "strategy": "7-email nurture drip with progressive profiling; heavy use of customer success stories",
                "subject_line_examples": [
                    "Your competitors are already automating this...",
                    "See how [Company] grew pipeline 3x with HubSpot",
                    "Free assessment: Is your CRM holding you back?",
                ],
                "estimated_frequency": "2-3 emails/week during onboarding, 1/week ongoing",
                "cta_pattern": "Book a Demo / Start Free Trial",
                "notable_tactics": [
                    "Dynamic content blocks personalized by industry",
                    "ROI calculator embedded in email",
                    "Social proof with real revenue numbers",
                ],
            },
            {
                "competitor": "Salesforce Marketing Cloud",
                "campaign_name": "Trailblazer AI Launch",
                "channel": "Email",
                "strategy": "Event-triggered sequences tied to Dreamforce; AI-first messaging",
                "subject_line_examples": [
                    "Einstein AI just changed the game for marketers",
                    "[First Name], your personalized marketing roadmap",
                    "Join 150K+ Trailblazers transforming marketing",
                ],
                "estimated_frequency": "3 emails/week during launch, tapering to 1/week",
                "cta_pattern": "Watch Demo / Join Webinar / Download Report",
                "notable_tactics": [
                    "Countdown timers for event registration",
                    "Personalized product recommendations based on tech stack",
                    "Customer video testimonials embedded in email",
                ],
            },
        ],
        "linkedin": [{
            "competitor": "HubSpot",
            "campaign_name": "State of Marketing 2026",
            "channel": "LinkedIn",
            "strategy": "Thought leadership + gated report promotion; sponsored content to ICP titles",
            "ad_copy_examples": [
                "The data is in: AI-powered marketing teams see 47% higher ROI. Get the report.",
                "Stop guessing. Start growing. Download the 2026 State of Marketing Report.",
            ],
            "targeting": "VP/Director/CMO titles at 200-5000 employee tech companies",
            "estimated_spend": "$45K-$65K/month",
            "notable_tactics": ["Lead gen forms with 3 fields max", "Retargeting website visitors with case study ads"],
        }, {
            "competitor": "Drift (Salesloft)",
            "campaign_name": "Revenue Acceleration Hub",
            "channel": "LinkedIn",
            "strategy": "ABM-focused campaigns targeting named accounts; conversational landing pages",
            "ad_copy_examples": ["Your buyers don't want to fill out forms. Give them a conversation instead."],
            "targeting": "Sales and Marketing leaders at enterprise B2B companies",
            "estimated_spend": "$30K-$50K/month",
            "notable_tactics": ["Video testimonial ads from recognizable brands", "Interactive ROI calculator as lead magnet"],
        }],
        "paid_search": [{
            "competitor": "Marketo (Adobe)",
            "campaign_name": "Marketing Automation Domination",
            "channel": "Paid Search",
            "strategy": "Aggressive bidding on competitor keywords and category terms",
            "keyword_themes": ["marketing automation software", "HubSpot alternative", "campaign management tool"],
            "ad_copy_examples": [
                "Enterprise Marketing Automation | Trusted by 5,000+ Brands | Adobe Marketo",
                "Outgrown Your Current Platform? | See Why Leaders Choose Marketo | Free Demo",
            ],
            "estimated_spend": "$120K-$180K/month",
            "notable_tactics": [
                "Sitelink extensions to case studies and pricing",
                "Competitor comparison landing pages",
                "Dynamic keyword insertion in headlines",
            ],
        }],
    },
    "ecommerce": {
        "email": [{
            "competitor": "Shopify",
            "campaign_name": "Start Your Empire",
            "channel": "Email",
            "strategy": "Founder success stories paired with free trial CTAs; lifecycle-based sequences",
            "subject_line_examples": [
                "She started in her garage. Now she does $2M/year.",
                "Your free trial is waiting — launch your store today",
            ],
            "estimated_frequency": "Daily during trial period, 3x/week post-trial",
            "cta_pattern": "Start Free Trial / Upgrade Now",
            "notable_tactics": [
                "Abandoned trial re-engagement sequences",
                "Revenue milestone celebration emails",
            ],
        }],
        "linkedin": [{
            "competitor": "BigCommerce",
            "campaign_name": "Enterprise Commerce Redefined",
            "channel": "LinkedIn",
            "strategy": "Enterprise-focused messaging targeting mid-market retailers",
            "ad_copy_examples": [
                "Outgrowing your ecommerce platform? See why enterprise brands choose BigCommerce.",
            ],
            "targeting": "eCommerce Directors, CTOs, and VPs at $50M+ revenue retailers",
            "estimated_spend": "$25K-$40K/month",
            "notable_tactics": [
                "Analyst report sponsorship (Forrester Wave)",
                "Customer migration success stories",
            ],
        }],
    },
}

# Default fallback data for unknown industry/channel combinations
_DEFAULT_COMPETITOR_DATA: list[dict] = [
    {
        "competitor": "Industry Leader A",
        "campaign_name": "Brand Awareness Push Q2 2026",
        "channel": "Multi-Channel",
        "strategy": "Full-funnel approach combining paid media, content marketing, and email nurture",
        "ad_copy_examples": ["Transform your business with the #1 rated platform"],
        "estimated_spend": "$50K-$100K/month",
        "notable_tactics": ["Heavy investment in video content", "Gated content with interactive assessments"],
    },
    {
        "competitor": "Industry Leader B",
        "campaign_name": "Challenger Brand Campaign",
        "channel": "Multi-Channel",
        "strategy": "Aggressive competitive positioning with free migration offers",
        "ad_copy_examples": ["Tired of overpaying? Switch and save 40%"],
        "estimated_spend": "$30K-$60K/month",
        "notable_tactics": ["Competitor comparison landing pages", "Free audit/assessment offers"],
    },
]


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize(value: str) -> str:
    """Lower-case and strip a string for lookup matching."""
    return value.strip().lower().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# CrewAI Tool
# ---------------------------------------------------------------------------

@tool("search_competitor_campaigns")
def search_competitor_campaigns(industry: str, channel: str) -> str:
    """Search for competitor campaign intelligence in a given industry and channel.

    Retrieves competitive campaign data including strategies, ad copy
    examples, estimated spend, and notable tactics for the specified
    industry and marketing channel.

    Args:
        industry: Industry vertical to research
            (e.g. "saas", "ecommerce", "fintech").
        channel: Marketing channel to focus on
            (e.g. "email", "linkedin", "paid_search").

    Returns:
        JSON string with competitor campaign intelligence data.
    """
    logger.info(
        "search_competitor_campaigns called | industry=%s | channel=%s | mock=%s | ts=%s",
        industry, channel, USE_MOCK, _ts(),
    )

    # ---- Live SerpAPI path (when configured) ----
    if not USE_MOCK and SERPAPI_KEY:
        try:
            import requests

            query = f"{industry} marketing campaigns {channel} 2026 competitor analysis"
            resp = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": SERPAPI_KEY,
                    "engine": "google",
                    "num": 10,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract and structure the organic results
            results = []
            for item in data.get("organic_results", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "source": "SerpAPI Live Search",
                })

            payload = {
                "industry": industry,
                "channel": channel,
                "query": query,
                "results": results,
                "retrieved_at": _ts(),
            }
            logger.info(
                "SerpAPI returned %d results for industry=%s channel=%s",
                len(results), industry, channel,
            )
            return json.dumps(payload, indent=2)
        except Exception as exc:
            logger.warning("SerpAPI error, falling back to mock: %s", exc)

    # ---- Mock fallback ----
    ind_key = _normalize(industry)
    ch_key = _normalize(channel)

    # Try exact match, then fall back to defaults
    industry_data = MOCK_COMPETITOR_DATA.get(ind_key, {})
    competitors = industry_data.get(ch_key, _DEFAULT_COMPETITOR_DATA)

    payload = {
        "industry": industry,
        "channel": channel,
        "competitors_analyzed": len(competitors),
        "data": competitors,
        "retrieved_at": _ts(),
        "source": "mock" if USE_MOCK else "serpapi_fallback",
    }

    logger.info(
        "Returning mock competitor data | industry=%s | channel=%s | count=%d",
        industry, channel, len(competitors),
    )
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Competitor Intelligence Tool — Demo")
    print("=" * 60)
    for ind, ch in [("saas", "email"), ("saas", "linkedin"), ("ecommerce", "email"), ("fintech", "paid_search")]:
        print(f"\n--- Industry: {ind} | Channel: {ch} ---")
        result = search_competitor_campaigns.run(industry=ind, channel=ch)
        parsed = json.loads(result)
        print(f"  Competitors found: {parsed['competitors_analyzed']}")
        for comp in parsed.get("data", []):
            print(f"    - {comp['competitor']}: {comp['campaign_name']}")
