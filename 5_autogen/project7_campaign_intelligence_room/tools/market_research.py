# tools/market_research.py
# Project 7: Campaign Intelligence Room
# Chapter Reference: Chapter 5 - AutoGen
# Description: Market research and competitive analysis tools with mock fallbacks
# Author: Pushparajan Ramar

"""Market research and competitive intelligence tools.

Provides web-based market trend search and structured competitor analysis.
Each function attempts real API calls first, falling back to deterministic
mock data when USE_MOCK is true or API keys are absent.

Environment variables consumed (via .env):
    USE_MOCK            - "true" (default) or "false"
    SERPER_API_KEY      - Serper.dev API key for web search
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Mock data — market trends
# ---------------------------------------------------------------------------

_MOCK_TRENDS: dict[str, dict[str, Any]] = {
    "b2b_saas": {
        "industry": "B2B SaaS",
        "top_trends": [
            {
                "trend": "AI-Powered Product-Led Growth",
                "momentum": "accelerating",
                "description": (
                    "B2B SaaS companies are embedding generative AI directly into "
                    "onboarding flows, reducing time-to-value by 40-60%. Companies "
                    "with AI-assisted onboarding report 2.3x higher trial-to-paid "
                    "conversion rates."
                ),
            },
            {
                "trend": "Usage-Based Pricing Expansion",
                "momentum": "strong",
                "description": (
                    "58% of SaaS companies now offer at least one usage-based "
                    "pricing tier, up from 34% in 2024. Consumption models drive "
                    "18% higher net revenue retention on average."
                ),
            },
            {
                "trend": "Vertical SaaS Consolidation",
                "momentum": "growing",
                "description": (
                    "Horizontal platforms are acquiring vertical-specific solutions. "
                    "Enterprise buyers prefer integrated vertical suites over best-of-breed, "
                    "with 67% consolidating their stack in the last 12 months."
                ),
            },
            {
                "trend": "First-Party Data Activation",
                "momentum": "critical",
                "description": (
                    "With third-party cookies deprecated, B2B SaaS firms investing in "
                    "CDPs and first-party intent data see 35% lower CAC. Composable "
                    "CDP architectures are replacing monolithic platforms."
                ),
            },
        ],
        "market_size_usd_billions": 232.0,
        "yoy_growth_pct": 14.2,
        "key_conferences": [
            "SaaStr Annual 2026",
            "Dreamforce 2026",
            "MarTech Conference West 2026",
        ],
    },
    "enterprise_technology": {
        "industry": "Enterprise Technology",
        "top_trends": [
            {
                "trend": "Agentic AI in Enterprise Workflows",
                "momentum": "explosive",
                "description": (
                    "Enterprises are deploying multi-agent AI systems for complex "
                    "workflows including procurement, compliance, and marketing ops. "
                    "Gartner predicts 25% of enterprise software will include agentic "
                    "AI capabilities by 2028."
                ),
            },
            {
                "trend": "Platform Engineering Maturity",
                "momentum": "strong",
                "description": (
                    "Internal developer platforms are now standard in 72% of "
                    "Fortune 500 companies, reducing deployment friction and "
                    "enabling faster go-to-market for digital products."
                ),
            },
            {
                "trend": "Cybersecurity Mesh Architecture",
                "momentum": "accelerating",
                "description": (
                    "Distributed security architectures replace perimeter-based "
                    "models. Companies adopting CSMA report 62% fewer breach "
                    "incidents and 40% lower security tool costs."
                ),
            },
        ],
        "market_size_usd_billions": 685.0,
        "yoy_growth_pct": 9.8,
        "key_conferences": [
            "AWS re:Invent 2026",
            "Google Cloud Next 2026",
            "Microsoft Ignite 2026",
        ],
    },
}

_MOCK_TRENDS_BY_REGION: dict[str, dict[str, Any]] = {
    "north_america": {
        "region": "North America",
        "market_share_pct": 42.5,
        "growth_outlook": "steady",
        "regulatory_landscape": (
            "SEC climate disclosure rules impacting B2B messaging; FTC cracking "
            "down on AI-generated claims; CCPA 2.0 enforcement ramping up."
        ),
        "buyer_sentiment": "cautiously optimistic — budgets recovering after 2025 cuts",
    },
    "europe": {
        "region": "Europe",
        "market_share_pct": 28.3,
        "growth_outlook": "moderate",
        "regulatory_landscape": (
            "EU AI Act enforcement underway; GDPR Article 22 automated decision-making "
            "restrictions affecting personalization strategies; Digital Markets Act "
            "reshaping platform advertising."
        ),
        "buyer_sentiment": "conservative — compliance costs weighing on adoption velocity",
    },
    "asia_pacific": {
        "region": "Asia-Pacific",
        "market_share_pct": 22.1,
        "growth_outlook": "accelerating",
        "regulatory_landscape": (
            "India DPDP Act 2024 fully in force; China's AI governance framework "
            "mandating algorithmic transparency; Southeast Asia emerging as a "
            "regulation-light growth corridor."
        ),
        "buyer_sentiment": "bullish — rapid digital transformation driving demand",
    },
}

# ---------------------------------------------------------------------------
# Mock data — competitor analysis
# ---------------------------------------------------------------------------

_MOCK_COMPETITORS: dict[str, dict[str, Any]] = {
    "hubspot": {
        "name": "HubSpot",
        "category": "Marketing Automation / CRM",
        "market_position": "Leader in mid-market, expanding into enterprise",
        "recent_moves": [
            "Launched AI Content Agent for automated blog and email generation",
            "Acquired Clearbit for intent data enrichment (integrated into Smart CRM)",
            "Released Commerce Hub targeting B2B payments and CPQ",
            "Expanded Breeze AI copilot across all hubs with custom agent builder",
        ],
        "strengths": [
            "Unified platform (marketing, sales, service, CMS, commerce)",
            "Strong ecosystem with 1,500+ app marketplace integrations",
            "Freemium model driving massive top-of-funnel adoption",
            "Excellent developer experience and API documentation",
        ],
        "weaknesses": [
            "Enterprise feature gaps vs. Salesforce/Adobe for large-scale ops",
            "Contact-based pricing can get expensive at scale",
            "Reporting depth lags behind dedicated BI tools",
            "Custom object limitations compared to Salesforce",
        ],
        "estimated_arr_usd_millions": 2_650,
        "customer_count_approx": 228_000,
        "key_messaging": "The AI-powered customer platform for scaling companies",
    },
    "salesforce": {
        "name": "Salesforce",
        "category": "CRM / Enterprise Cloud Platform",
        "market_position": "Market leader in enterprise CRM and marketing cloud",
        "recent_moves": [
            "Launched Agentforce — autonomous AI agents for sales, service, marketing",
            "Deepened Data Cloud integration for real-time customer 360 profiles",
            "Released Marketing Cloud Growth Edition targeting mid-market",
            "Expanded Slack integration as collaboration layer for all clouds",
        ],
        "strengths": [
            "Dominant enterprise market share and brand trust",
            "Comprehensive platform spanning CRM, marketing, commerce, analytics",
            "Massive partner and ISV ecosystem (AppExchange)",
            "Aggressive AI investment with Einstein and Agentforce",
        ],
        "weaknesses": [
            "Implementation complexity and long deployment timelines",
            "High total cost of ownership (licensing, consultants, customization)",
            "User experience perceived as dated compared to modern SaaS",
            "Cloud fragmentation — Marketing Cloud still partially siloed",
        ],
        "estimated_arr_usd_millions": 38_500,
        "customer_count_approx": 150_000,
        "key_messaging": "The #1 AI CRM — bring companies and customers together",
    },
    "adobe": {
        "name": "Adobe (Experience Cloud)",
        "category": "Digital Experience Platform / MarTech",
        "market_position": "Leader in enterprise content and experience management",
        "recent_moves": [
            "Launched Adobe GenStudio for Performance Marketing",
            "Integrated Firefly generative AI across Experience Cloud workflows",
            "Released Adobe Real-Time CDP enhancements with predictive audiences",
            "Expanded Adobe Journey Optimizer with AI-driven orchestration",
        ],
        "strengths": [
            "Unmatched creative-to-delivery workflow (Creative Cloud + Experience Cloud)",
            "Deep analytics capability via Adobe Analytics and Customer Journey Analytics",
            "Strong content supply chain and DAM (AEM Assets)",
            "Enterprise-grade personalization at scale (Adobe Target)",
        ],
        "weaknesses": [
            "Steep learning curve and heavy reliance on implementation partners",
            "Premium pricing limits mid-market penetration",
            "Less intuitive UI compared to modern marketing platforms",
            "Integration between Creative Cloud and Experience Cloud still maturing",
        ],
        "estimated_arr_usd_millions": 5_800,
        "customer_count_approx": 12_000,
        "key_messaging": "Make it personal — AI-powered experiences across every channel",
    },
    "braze": {
        "name": "Braze",
        "category": "Customer Engagement Platform",
        "market_position": "Leader in real-time cross-channel engagement",
        "recent_moves": [
            "Launched BrazeAI with predictive churn and send-time optimization",
            "Expanded Sage AI copywriting assistant across all channels",
            "Released Canvas Flow 2.0 for visual journey orchestration",
            "Deepened Snowflake and Databricks integrations for warehouse-native audiences",
        ],
        "strengths": [
            "Real-time event streaming and sub-second personalization",
            "Developer-friendly APIs and SDKs for mobile-first brands",
            "Strong in cross-channel orchestration (push, email, SMS, in-app)",
            "Modern architecture — cloud-native, event-driven, scalable",
        ],
        "weaknesses": [
            "Limited CRM / sales functionality — marketing-only focus",
            "Smaller partner ecosystem compared to Salesforce/HubSpot",
            "Reporting capabilities not as deep as dedicated analytics platforms",
            "Higher per-message costs at very large volumes",
        ],
        "estimated_arr_usd_millions": 520,
        "customer_count_approx": 2_100,
        "key_messaging": "Power brilliant customer experiences in real time",
    },
}


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def search_market_trends(industry: str, region: str = "north_america") -> str:
    """Search for current market trends in a given industry and region.

    Retrieves trend data including momentum indicators, market sizing,
    growth rates, and regional regulatory context.

    Args:
        industry: Industry vertical to research, e.g. "B2B SaaS",
                  "enterprise technology", "ecommerce", "fintech".
        region:   Geographic region for regional context, e.g.
                  "north_america", "europe", "asia_pacific".

    Returns:
        JSON string with market trends, sizing, and regional insights.
    """
    log.info(
        "search_market_trends  industry=%s  region=%s  mock=%s  ts=%s",
        industry, region, USE_MOCK, _ts(),
    )

    if not USE_MOCK and SERPER_API_KEY:
        try:
            import requests

            resp = requests.post(
                "https://google.serper.dev/search",
                json={"q": f"{industry} market trends {region} 2026"},
                headers={"X-API-KEY": SERPER_API_KEY},
                timeout=15,
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), indent=2)
        except Exception as exc:
            log.warning("Serper API call failed, using mock data: %s", exc)

    # ----- mock fallback -----
    normalized_industry = industry.lower().replace(" ", "_").replace("-", "_")
    alias_map = {
        "saas": "b2b_saas",
        "b2b_saas": "b2b_saas",
        "b2b": "b2b_saas",
        "enterprise": "enterprise_technology",
        "enterprise_technology": "enterprise_technology",
        "enterprise_tech": "enterprise_technology",
    }
    industry_key = alias_map.get(normalized_industry, "b2b_saas")
    industry_data = _MOCK_TRENDS.get(industry_key, _MOCK_TRENDS["b2b_saas"])

    normalized_region = region.lower().replace(" ", "_").replace("-", "_")
    region_data = _MOCK_TRENDS_BY_REGION.get(
        normalized_region, _MOCK_TRENDS_BY_REGION["north_america"]
    )

    result: dict[str, Any] = {
        **industry_data,
        "regional_context": region_data,
        "queried_at": _ts(),
    }

    log.info("Returning mock market trends for industry=%s, region=%s", industry, region)
    return json.dumps(result, indent=2)


def analyze_competitor(competitor_name: str) -> str:
    """Perform a competitive analysis for a named competitor.

    Returns structured intelligence including market position, recent
    strategic moves, strengths, weaknesses, estimated revenue, and
    key messaging.

    Args:
        competitor_name: The competitor to analyze, e.g. "HubSpot",
                         "Salesforce", "Adobe", "Braze".

    Returns:
        JSON string with competitive intelligence data.
    """
    log.info(
        "analyze_competitor  competitor=%s  mock=%s  ts=%s",
        competitor_name, USE_MOCK, _ts(),
    )

    if not USE_MOCK and SERPER_API_KEY:
        try:
            import requests

            resp = requests.post(
                "https://google.serper.dev/search",
                json={"q": f"{competitor_name} company analysis strategy 2026"},
                headers={"X-API-KEY": SERPER_API_KEY},
                timeout=15,
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), indent=2)
        except Exception as exc:
            log.warning("Serper API call failed, using mock data: %s", exc)

    # ----- mock fallback -----
    normalized = competitor_name.lower().replace(" ", "_").replace("-", "_")
    # Handle common aliases
    alias_map = {
        "adobe_experience_cloud": "adobe",
        "adobe_experience": "adobe",
        "sfdc": "salesforce",
        "salesforce_marketing_cloud": "salesforce",
    }
    competitor_key = alias_map.get(normalized, normalized)
    data = _MOCK_COMPETITORS.get(competitor_key)

    if data is None:
        data = {
            "name": competitor_name,
            "category": "Unknown",
            "market_position": "Data not available in mock database",
            "recent_moves": [
                "No specific intelligence available — consider manual research"
            ],
            "strengths": ["Insufficient data for automated assessment"],
            "weaknesses": ["Insufficient data for automated assessment"],
            "note": (
                f"Competitor '{competitor_name}' not found in mock database. "
                "Available competitors: HubSpot, Salesforce, Adobe, Braze. "
                "Enable live search by setting USE_MOCK=false and providing "
                "a SERPER_API_KEY."
            ),
        }

    result: dict[str, Any] = {**data, "analyzed_at": _ts()}
    log.info("Returning mock competitor analysis for '%s'", competitor_name)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Campaign Intelligence Room — Market Research Tools Demo")
    print("=" * 60)
    print(f"\nUSE_MOCK = {USE_MOCK}\n")

    print("--- Market Trends: B2B SaaS, North America ---")
    print(search_market_trends("B2B SaaS", "north_america"))

    print("\n--- Competitor Analysis: HubSpot ---")
    print(analyze_competitor("HubSpot"))

    print("\n--- Competitor Analysis: Salesforce ---")
    print(analyze_competitor("Salesforce"))
