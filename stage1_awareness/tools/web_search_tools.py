# File      : web_search_tools.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Web search and company enrichment tools.

Provides firmographic and technographic look-ups with mock fallback.
"""

from __future__ import annotations

import logging
import os
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

_MOCK_COMPANIES: dict[str, dict[str, Any]] = {
    "techcorp.com": {
        "name": "TechCorp Inc.",
        "domain": "techcorp.com",
        "industry": "Enterprise Software",
        "employee_count": 1200,
        "annual_revenue": "$150M",
        "headquarters": "San Francisco, CA",
        "description": "Enterprise SaaS platform for workflow automation.",
        "founded_year": 2012,
    },
    "startup.io": {
        "name": "Startup.io",
        "domain": "startup.io",
        "industry": "Developer Tools",
        "employee_count": 45,
        "annual_revenue": "$5M",
        "headquarters": "Austin, TX",
        "description": "Developer productivity tools for small teams.",
        "founded_year": 2020,
    },
    "bigco.org": {
        "name": "BigCo International",
        "domain": "bigco.org",
        "industry": "Manufacturing",
        "employee_count": 15000,
        "annual_revenue": "$2B",
        "headquarters": "Chicago, IL",
        "description": "Global manufacturing and supply chain company.",
        "founded_year": 1985,
    },
}

_MOCK_TECH_STACKS: dict[str, dict[str, Any]] = {
    "techcorp.com": {
        "domain": "techcorp.com",
        "technologies": [
            {"name": "Salesforce", "category": "CRM"},
            {"name": "HubSpot", "category": "Marketing Automation"},
            {"name": "Snowflake", "category": "Data Warehouse"},
            {"name": "AWS", "category": "Cloud"},
            {"name": "Segment", "category": "CDP"},
        ],
    },
    "startup.io": {
        "domain": "startup.io",
        "technologies": [
            {"name": "HubSpot", "category": "CRM"},
            {"name": "Vercel", "category": "Hosting"},
            {"name": "Stripe", "category": "Payments"},
            {"name": "GCP", "category": "Cloud"},
        ],
    },
    "bigco.org": {
        "domain": "bigco.org",
        "technologies": [
            {"name": "SAP", "category": "ERP"},
            {"name": "Microsoft Dynamics", "category": "CRM"},
            {"name": "Azure", "category": "Cloud"},
            {"name": "Tableau", "category": "BI"},
        ],
    },
}


# ---------------------------------------------------------------------------
# search_company_info
# ---------------------------------------------------------------------------

def _search_company_real(domain: str) -> dict[str, Any]:
    """Enrich company information using Clearbit / external APIs."""
    import httpx

    clearbit_key = os.getenv("CLEARBIT_API_KEY", "")
    try:
        resp = httpx.get(
            "https://company.clearbit.com/v2/companies/find",
            params={"domain": domain},
            headers={"Authorization": f"Bearer {clearbit_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "name": data.get("name", ""),
            "domain": domain,
            "industry": data.get("category", {}).get("industry", ""),
            "employee_count": data.get("metrics", {}).get("employees", 0),
            "annual_revenue": data.get("metrics", {}).get("estimatedAnnualRevenue", ""),
            "headquarters": data.get("geo", {}).get("city", ""),
            "description": data.get("description", ""),
            "founded_year": data.get("foundedYear"),
        }
    except Exception as exc:
        logger.error("Clearbit API error for %s: %s", domain, exc)
        return {"domain": domain, "error": str(exc)}


def _search_company_mock(domain: str) -> dict[str, Any]:
    """Return mock company data for a known domain."""
    return _MOCK_COMPANIES.get(domain, {"domain": domain, "error": "Company not found"})


def search_company_info(domain: str) -> dict[str, Any]:
    """Look up firmographic information for a company domain.

    Args:
        domain: The company's web domain (e.g. ``"techcorp.com"``).

    Returns:
        Dict with company name, industry, employee count, revenue, etc.
    """
    logger.info("Searching company info for %s (mock=%s)", domain, USE_MOCK)
    if USE_MOCK:
        return _search_company_mock(domain)
    return _search_company_real(domain)


# ---------------------------------------------------------------------------
# get_tech_stack
# ---------------------------------------------------------------------------

def _get_tech_stack_real(domain: str) -> dict[str, Any]:
    """Fetch technology stack using BuiltWith or similar API."""
    import httpx

    bw_key = os.getenv("BUILTWITH_API_KEY", "")
    try:
        resp = httpx.get(
            "https://api.builtwith.com/free1/api.json",
            params={"KEY": bw_key, "LOOKUP": domain},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        techs = []
        for group in data.get("Results", [{}])[0].get("Result", {}).get("Paths", []):
            for tech in group.get("Technologies", []):
                techs.append({
                    "name": tech.get("Name", ""),
                    "category": tech.get("Categories", [""])[0] if tech.get("Categories") else "",
                })
        return {"domain": domain, "technologies": techs}
    except Exception as exc:
        logger.error("BuiltWith API error for %s: %s", domain, exc)
        return {"domain": domain, "technologies": [], "error": str(exc)}


def _get_tech_stack_mock(domain: str) -> dict[str, Any]:
    """Return mock tech stack data."""
    return _MOCK_TECH_STACKS.get(
        domain,
        {"domain": domain, "technologies": []},
    )


def get_tech_stack(domain: str) -> dict[str, Any]:
    """Retrieve the technology stack for a company domain.

    Args:
        domain: The company's web domain.

    Returns:
        Dict with ``domain`` and ``technologies`` list.
    """
    logger.info("Getting tech stack for %s (mock=%s)", domain, USE_MOCK)
    if USE_MOCK:
        return _get_tech_stack_mock(domain)
    return _get_tech_stack_real(domain)
