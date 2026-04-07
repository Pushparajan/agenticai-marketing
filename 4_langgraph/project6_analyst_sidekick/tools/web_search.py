# tools/web_search.py
# Project 6: MarTech Analyst Sidekick
# Chapter Reference: Chapter 4 - LangGraph
# Description: Marketing news and trend search tool with mock fallback
# Author: Pushparajan Ramar

"""Web search tool for real-time marketing news and trends.

Queries a search API (e.g., Tavily, SerpAPI) for the latest marketing
news, industry benchmarks, and competitive intelligence.  Falls back to
realistic mock results when USE_MOCK is true or the API key is absent.

Environment variables consumed (via .env):
    USE_MOCK          - "true" (default) or "false"
    TAVILY_API_KEY    - Tavily search API key
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
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

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
# Mock search results — categorised by keyword detection
# ---------------------------------------------------------------------------

_MOCK_RESULTS: dict[str, list[dict[str, str]]] = {
    "cac": [
        {"title": "Customer Acquisition Cost Benchmarks 2026: SaaS Industry Report",
         "url": "https://www.profitwell.com/recur/cac-benchmarks-2026",
         "snippet": "Median SaaS CAC rose 18% YoY in 2025 but has started to stabilise in Q1 2026 at $347 for SMB and $4,200 for enterprise. Organic content and partner referrals remain the most efficient acquisition channels with CAC payback under 6 months.",
         "published": "2026-03-15"},
        {"title": "How Top B2B Marketers Cut CAC by 30% with AI-Driven Lead Scoring",
         "url": "https://www.marketingai.io/blog/cut-cac-ai-lead-scoring",
         "snippet": "Companies deploying AI-based lead scoring models saw an average 30% reduction in customer acquisition cost over 12 months by focusing spend on high-intent prospects.",
         "published": "2026-02-28"},
    ],
    "email": [
        {"title": "Email Marketing Benchmarks 2026: Open Rates, CTR, and Deliverability",
         "url": "https://www.mailchimp.com/resources/email-marketing-benchmarks-2026",
         "snippet": "Average email open rates across industries held steady at 28.7% in Q1 2026. Personalised subject lines lifted open rates by 14%. B2B SaaS newsletters saw the highest CTR at 4.2%, while promotional sends averaged 1.8%.",
         "published": "2026-04-01"},
        {"title": "Segmentation Strategies That Double Email Engagement",
         "url": "https://www.hubspot.com/blog/email-segmentation-strategies",
         "snippet": "Marketers using behavioural segmentation report 2x higher click-through rates compared to demographic-only segments. Product-usage signals and intent data are the new gold standard.",
         "published": "2026-03-12"},
    ],
    "pipeline": [
        {"title": "Q1 2026 B2B Pipeline Report: Which Channels Are Winning",
         "url": "https://www.demandgen.com/reports/q1-2026-pipeline",
         "snippet": "Organic search generated 33% of total pipeline in Q1 2026, followed by LinkedIn Ads (23%) and email nurture (17%). Paid social contributed just 2.6% of qualified pipeline despite accounting for 12% of spend.",
         "published": "2026-04-03"},
        {"title": "Multi-Touch Attribution Models for B2B Pipeline Measurement",
         "url": "https://www.bizible.com/blog/multi-touch-attribution-guide",
         "snippet": "Linear and W-shaped attribution models provide the most balanced view of pipeline contribution. First-touch models over-credit content marketing while last-touch models over-credit sales outreach.",
         "published": "2026-03-18"},
    ],
    "martech": [
        {"title": "The 2026 MarTech Landscape: Consolidation Meets AI-Native Tools",
         "url": "https://www.chiefmartec.com/2026/martech-landscape",
         "snippet": "The 2026 MarTech landscape shrank to 9,200 solutions (from 11,038 in 2024) as consolidation accelerated. AI-native platforms are the fastest-growing category at 47% YoY.",
         "published": "2026-03-25"},
        {"title": "Gartner: CMOs Shift Budget from Paid Media to AI and Data Infrastructure",
         "url": "https://www.gartner.com/en/marketing/insights/cmo-spend-2026",
         "snippet": "Gartner's 2026 CMO Spend Survey found that marketing technology now accounts for 28.8% of the total marketing budget, overtaking paid media (26.1%) for the first time.",
         "published": "2026-03-20"},
    ],
    "default": [
        {"title": "State of Marketing 2026: AI, Personalisation, and Data Privacy",
         "url": "https://www.salesforce.com/resources/state-of-marketing-2026",
         "snippet": "Salesforce's annual survey of 6,000+ marketers reveals that 72% now use generative AI in at least one workflow. Personalisation at scale and first-party data strategies are the top two priorities.",
         "published": "2026-03-10"},
        {"title": "Marketing Analytics Maturity Model: Where Does Your Team Stand?",
         "url": "https://www.mckinsey.com/capabilities/growth/marketing-analytics",
         "snippet": "Only 11% of marketing organisations have reached 'predictive' maturity in their analytics capability. Most remain at the 'descriptive' stage, relying on dashboards rather than automated decision-making.",
         "published": "2026-02-22"},
        {"title": "Google Deprecates Third-Party Cookies: What Marketers Need to Know",
         "url": "https://www.thinkwithgoogle.com/marketing-strategies/privacy-cookieless",
         "snippet": "With Chrome finally removing third-party cookies in Q2 2026, marketers must accelerate first-party data collection. Contextual advertising spend is projected to grow 35% YoY.",
         "published": "2026-04-05"},
    ],
}


def _select_results(query: str) -> list[dict[str, str]]:
    """Pick the most relevant mock results based on keyword matching."""
    query_lower = query.lower()
    matched: list[dict[str, str]] = []

    for keyword, results in _MOCK_RESULTS.items():
        if keyword == "default":
            continue
        if keyword in query_lower:
            matched.extend(results)

    # Always include one general result for context
    if not matched:
        matched = _MOCK_RESULTS["default"]
    elif len(matched) < 3:
        matched.append(_MOCK_RESULTS["default"][0])

    return matched[:5]


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------

def search_marketing_news(query: str) -> str:
    """Search for real-time marketing news, benchmarks, and trends.

    Queries a web search API for the latest marketing intelligence.
    Returns relevant article titles, snippets, and URLs.

    Args:
        query: Natural-language search query, e.g. "B2B email open rate
               benchmarks 2026" or "SaaS customer acquisition cost trends".

    Returns:
        JSON string with a list of search results, each containing
        title, url, snippet, and published date.
    """
    log.info(
        "search_marketing_news  query='%s'  mock=%s  ts=%s",
        query, USE_MOCK, _ts(),
    )

    # ----- live API path -----
    if not USE_MOCK and TAVILY_API_KEY:
        try:
            import httpx

            resp = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 5,
                    "include_answer": True,
                    "topic": "general",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:300],
                    "published": r.get("published_date", ""),
                }
                for r in data.get("results", [])
            ]
            return json.dumps(
                {
                    "query": query,
                    "answer": data.get("answer", ""),
                    "results": results,
                    "searched_at": _ts(),
                },
                indent=2,
            )
        except Exception as exc:
            log.warning("Tavily API call failed, using mock data: %s", exc)

    # ----- mock fallback -----
    results = _select_results(query)
    payload: dict[str, Any] = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "searched_at": _ts(),
        "source": "mock",
    }

    log.info("Returning %d mock search results for '%s'", len(results), query)
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MarTech Analyst Sidekick — Web Search Demo")
    print("=" * 60)
    print(f"\nUSE_MOCK = {USE_MOCK}\n")

    print("--- Search: CAC benchmarks ---")
    print(search_marketing_news("SaaS customer acquisition cost benchmarks 2026"))

    print("\n--- Search: email marketing trends ---")
    print(search_marketing_news("email marketing open rate trends B2B"))

    print("\n--- Search: pipeline channels ---")
    print(search_marketing_news("which channels drive most B2B pipeline"))

    print("\n--- Search: generic marketing ---")
    print(search_marketing_news("latest marketing technology news"))
