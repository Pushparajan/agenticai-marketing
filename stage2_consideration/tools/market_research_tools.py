# File      : market_research_tools.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Market-research tools for the Campaign Intelligence Crew.

Every tool follows the USE_MOCK pattern:
  - When USE_MOCK=true (default), return realistic mock data.
  - When USE_MOCK=false, call the real external API.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import httpx
from crewai.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Helper: real HTTP GET with timeout
# ---------------------------------------------------------------------------
def _http_get(url: str, headers: dict | None = None, params: dict | None = None) -> dict:
    """Perform a GET request with sensible defaults."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=headers or {}, params=params or {})
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Tool 1: Web Search
# ---------------------------------------------------------------------------
@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for information about a company, product, or topic.

    Args:
        query: The search query string.

    Returns:
        JSON string with search results including title, snippet, and url.
    """
    if USE_MOCK:
        results = [
            {
                "title": f"{query} — Latest News and Analysis",
                "snippet": (
                    f"Comprehensive coverage of {query}. The company recently "
                    "announced a Series C funding round of $45M and expanded "
                    "into the European market with a new London office."
                ),
                "url": "https://techcrunch.com/example-article",
                "date": (datetime.now() - timedelta(days=12)).isoformat()[:10],
            },
            {
                "title": f"{query} Reviews, Pricing & Features | G2",
                "snippet": (
                    f"{query} scores 4.6/5 on G2 with 328 reviews. Users praise "
                    "the intuitive UI and strong API integrations. Common "
                    "complaints include limited reporting customisation."
                ),
                "url": "https://www.g2.com/products/example",
                "date": (datetime.now() - timedelta(days=5)).isoformat()[:10],
            },
            {
                "title": f"How {query} is transforming B2B marketing",
                "snippet": (
                    "Industry analysts highlight the shift toward AI-driven "
                    "personalisation in mid-market B2B. Companies adopting "
                    "agentic workflows report 35% higher engagement rates."
                ),
                "url": "https://www.forrester.com/example-report",
                "date": (datetime.now() - timedelta(days=30)).isoformat()[:10],
            },
        ]
        return json.dumps({"query": query, "results": results}, indent=2)

    # Real API: Serper.dev (Google Search API)
    api_key = os.environ["SERPER_API_KEY"]
    data = _http_get(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key},
        params={"q": query, "num": 5},
    )
    results = [
        {"title": r.get("title", ""), "snippet": r.get("snippet", ""), "url": r.get("link", "")}
        for r in data.get("organic", [])
    ]
    return json.dumps({"query": query, "results": results}, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: LinkedIn Company Lookup
# ---------------------------------------------------------------------------
@tool("linkedin_company_lookup")
def linkedin_company_lookup(company_name: str) -> str:
    """Look up a company on LinkedIn to get firmographic data.

    Args:
        company_name: The name of the company to research.

    Returns:
        JSON string with company profile including size, industry, and HQ.
    """
    if USE_MOCK:
        profile = {
            "company_name": company_name,
            "linkedin_url": f"https://linkedin.com/company/{company_name.lower().replace(' ', '-')}",
            "industry": "Computer Software",
            "company_size": "201-500 employees",
            "headquarters": "San Francisco, California",
            "founded": 2018,
            "specialties": [
                "Marketing Automation",
                "Customer Data Platform",
                "B2B Analytics",
                "AI-Powered Personalisation",
            ],
            "description": (
                f"{company_name} is a fast-growing B2B SaaS company that helps "
                "mid-market enterprises unify customer data and automate "
                "personalised marketing campaigns across channels."
            ),
            "follower_count": 12_450,
            "recent_posts_themes": [
                "Product launch: AI copilot for campaign planning",
                "Customer success story with Fortune 500 retailer",
                "Hiring push: 15 open engineering roles",
            ],
        }
        return json.dumps(profile, indent=2)

    # Real API: Proxycurl LinkedIn API
    api_key = os.environ["PROXYCURL_API_KEY"]
    data = _http_get(
        "https://nubela.co/proxycurl/api/linkedin/company/resolve",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"company_name": company_name},
    )
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: Industry Benchmarks
# ---------------------------------------------------------------------------
@tool("get_industry_benchmarks")
def get_industry_benchmarks(industry: str) -> str:
    """Retrieve marketing engagement benchmarks for a specific industry.

    Args:
        industry: The industry vertical (e.g. 'B2B SaaS', 'FinTech').

    Returns:
        JSON string with benchmark metrics for email, ads, and content.
    """
    if USE_MOCK:
        benchmarks = {
            "industry": industry,
            "source": "HubSpot State of Marketing 2026 + Klaviyo Benchmarks",
            "email": {
                "open_rate_pct": 28.5,
                "click_rate_pct": 4.2,
                "unsubscribe_rate_pct": 0.3,
                "best_send_day": "Tuesday",
                "best_send_time": "10:00 AM EST",
            },
            "linkedin": {
                "avg_engagement_rate_pct": 3.8,
                "inmail_response_rate_pct": 18.0,
                "sponsored_content_ctr_pct": 0.45,
            },
            "webinar": {
                "registration_rate_pct": 35.0,
                "attendance_rate_pct": 42.0,
                "post_webinar_meeting_rate_pct": 12.0,
            },
            "content": {
                "avg_content_touches_before_mql": 7,
                "top_performing_formats": [
                    "Case studies",
                    "ROI calculators",
                    "Comparison guides",
                ],
                "avg_time_on_page_seconds": 185,
            },
            "funnel": {
                "mql_to_sql_conversion_pct": 22.0,
                "avg_days_mql_to_sql": 18,
                "avg_deal_cycle_days": 45,
            },
        }
        return json.dumps(benchmarks, indent=2)

    # Real API: custom benchmarks endpoint
    api_url = os.environ.get("BENCHMARKS_API_URL", "https://api.example.com/benchmarks")
    data = _http_get(api_url, params={"industry": industry})
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: Tech Stack Signals
# ---------------------------------------------------------------------------
@tool("get_tech_stack_signals")
def get_tech_stack_signals(domain: str) -> str:
    """Detect the technology stack used by a company from its domain.

    Args:
        domain: The company's website domain (e.g. 'acmecorp.com').

    Returns:
        JSON string with detected technologies grouped by category.
    """
    if USE_MOCK:
        signals = {
            "domain": domain,
            "scan_date": datetime.now().isoformat()[:10],
            "technologies": {
                "analytics": ["Google Analytics 4", "Amplitude", "Hotjar"],
                "marketing_automation": ["HubSpot Marketing Hub"],
                "crm": ["HubSpot CRM"],
                "cdp": ["Segment"],
                "email": ["Klaviyo"],
                "cms": ["WordPress", "Webflow (blog)"],
                "advertising": ["Google Ads", "LinkedIn Campaign Manager"],
                "chat": ["Intercom"],
                "payments": ["Stripe"],
                "cloud_hosting": ["AWS (CloudFront, S3)"],
            },
            "signals": {
                "marketing_maturity": "advanced",
                "likely_budget_range": "$500K-$2M annual marketing spend",
                "integration_complexity": "medium — 8 tools detected",
                "buying_signal": (
                    "Currently using HubSpot free CRM; may be evaluating "
                    "enterprise upgrade or competitive switch."
                ),
            },
        }
        return json.dumps(signals, indent=2)

    # Real API: BuiltWith or Wappalyzer
    api_key = os.environ["BUILTWITH_API_KEY"]
    data = _http_get(
        "https://api.builtwith.com/v21/api.json",
        params={"KEY": api_key, "LOOKUP": domain},
    )
    # Flatten BuiltWith response to our schema
    techs: dict[str, list[str]] = {}
    for group in data.get("Results", [{}])[0].get("Result", {}).get("Paths", []):
        for tech in group.get("Technologies", []):
            cat = tech.get("Tag", "other")
            techs.setdefault(cat, []).append(tech.get("Name", ""))
    return json.dumps({"domain": domain, "technologies": techs}, indent=2)
