# File      : competitive_battlecard_tools.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Tools for retrieving competitive intelligence during the Decision stage.

Every function follows the **USE_MOCK** pattern:
- ``USE_MOCK=true`` (default)  -> deterministic mock data
- ``USE_MOCK=false``           -> calls the real OpenAI API
"""

from __future__ import annotations

import json
import os

from langchain_core.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_BATTLECARDS: dict[str, dict] = {
    "competitorx": {
        "competitor": "CompetitorX",
        "strengths": [
            "Lower entry price point",
            "Established brand in SMB segment",
            "Large partner ecosystem",
        ],
        "weaknesses": [
            "Limited enterprise scalability",
            "No native AI/ML capabilities",
            "Manual reporting only — no real-time dashboards",
            "12-month lock-in contracts with steep exit fees",
        ],
        "our_advantages": [
            "AI-powered automation saves 15 hrs/week per rep",
            "Real-time analytics and predictive scoring",
            "Flexible month-to-month billing",
            "Dedicated customer success manager from day one",
        ],
        "landmines": [
            "Ask about their API rate limits under load.",
            "Request a live demo of their reporting — it is pre-rendered.",
            "Inquire about multi-region data residency.",
        ],
        "win_rate_vs": "68%",
    },
    "rivaly": {
        "competitor": "RivalY",
        "strengths": [
            "Strong product-led growth motion",
            "Generous free tier attracts developers",
            "Good documentation and community forums",
        ],
        "weaknesses": [
            "Weak enterprise SSO and RBAC controls",
            "No phone or chat support — email only",
            "Limited compliance certifications",
            "Poor uptime SLA (99.5% vs our 99.99%)",
        ],
        "our_advantages": [
            "Enterprise-grade security (SOC-2 II, ISO 27001)",
            "24/7 live support with < 15 min response SLA",
            "99.99% uptime SLA with financial credits",
            "Built-in GDPR and CCPA compliance tooling",
        ],
        "landmines": [
            "Ask for their incident post-mortems from last quarter.",
            "Request evidence of SOC-2 certification.",
            "Probe their GDPR data-subject-request workflow.",
        ],
        "win_rate_vs": "72%",
    },
}

_COMPARISONS: dict[str, dict[str, dict]] = {
    "competitorx": {
        "pricing": {
            "us": "$99/user/mo (all features included)",
            "them": "$59/user/mo (core) + $40/user add-on for analytics",
            "verdict": "Comparable total cost; we include analytics by default.",
        },
        "integration": {
            "us": "200+ native integrations, open API, webhook builder",
            "them": "85 integrations, limited API documentation",
            "verdict": "We integrate 2x more tools out of the box.",
        },
        "support": {
            "us": "24/7 live chat, dedicated CSM, 15-min SLA",
            "them": "Business-hours email, shared CSM pool",
            "verdict": "Faster, more personal support from us.",
        },
        "all": {
            "summary": (
                "We outperform CompetitorX on analytics, integrations, and "
                "support.  Their headline price is lower but total cost with "
                "add-ons is comparable.  Our 68% win rate reflects consistent "
                "value delivery."
            ),
        },
    },
    "rivaly": {
        "security": {
            "us": "SOC-2 II, ISO 27001, GDPR/CCPA built-in, SSO + RBAC",
            "them": "SOC-2 I (pending II), basic GDPR, no RBAC",
            "verdict": "We lead significantly on enterprise security.",
        },
        "reliability": {
            "us": "99.99% SLA, multi-AZ, auto-failover",
            "them": "99.5% SLA, single-region, manual failover",
            "verdict": "10x fewer expected downtime minutes per year.",
        },
        "all": {
            "summary": (
                "RivalY appeals to developer-first teams, but lacks the "
                "enterprise controls that procurement and security teams "
                "require.  Our 72% win rate in head-to-head evaluations "
                "confirms our enterprise positioning."
            ),
        },
    },
}


# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------

def _real_get_battlecard(competitor: str) -> str:
    """Call OpenAI to generate a battlecard for *competitor*."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a competitive intelligence analyst.  Return a JSON "
                    "battlecard with keys: competitor, strengths, weaknesses, "
                    "our_advantages, landmines, win_rate_vs."
                ),
            },
            {
                "role": "user",
                "content": f"Create a competitive battlecard against {competitor}.",
            },
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content or "{}"


def _real_get_comparison(competitor: str, feature_area: str) -> str:
    """Call OpenAI to generate a feature comparison."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a competitive intelligence analyst.  Return a JSON "
                    "comparison for the given feature area.  Keys: us, them, verdict."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Compare us vs {competitor} on: {feature_area}."
                ),
            },
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content or "{}"


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

@tool
def get_battlecard(competitor: str) -> str:
    """Retrieve a competitive battlecard for the named competitor.

    Args:
        competitor: Name of the competitor (e.g. 'CompetitorX').

    Returns:
        JSON string with the full battlecard.
    """
    if USE_MOCK:
        key = competitor.lower().strip().replace(" ", "")
        data = _BATTLECARDS.get(key)
        if data:
            return json.dumps(data, indent=2)
        # Fallback for unknown competitor
        return json.dumps(
            {
                "competitor": competitor,
                "strengths": ["Unknown — research needed"],
                "weaknesses": ["Unknown — research needed"],
                "our_advantages": ["Request a custom analysis from the CI team"],
                "landmines": [],
                "win_rate_vs": "N/A",
            },
            indent=2,
        )
    return _real_get_battlecard(competitor)


@tool
def get_competitive_comparison(competitor: str, feature_area: str) -> str:
    """Get a feature-by-feature comparison against a competitor.

    Args:
        competitor: Name of the competitor.
        feature_area: Specific area to compare (e.g. 'pricing', 'security')
                      or 'all' for a summary.

    Returns:
        JSON string with the comparison data.
    """
    if USE_MOCK:
        key = competitor.lower().strip().replace(" ", "")
        comp_data = _COMPARISONS.get(key, {})
        area = feature_area.lower().strip()
        if area in comp_data:
            return json.dumps(comp_data[area], indent=2)
        if "all" in comp_data:
            return json.dumps(comp_data["all"], indent=2)
        return json.dumps(
            {"summary": f"No comparison data for {competitor} on {feature_area}."},
            indent=2,
        )
    return _real_get_comparison(competitor, feature_area)
