# File      : content_publisher_tools.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Content publishing and retrieval tools for the Campaign Intelligence Crew.

Every tool follows the USE_MOCK pattern:
  - When USE_MOCK=true (default), return realistic mock data.
  - When USE_MOCK=false, call the real external API.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import httpx
from crewai.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


def _http_post(url: str, headers: dict, payload: dict) -> dict:
    """Perform a POST request with sensible defaults."""
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


def _http_get(url: str, headers: dict | None = None, params: dict | None = None) -> dict:
    """Perform a GET request with sensible defaults."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=headers or {}, params=params or {})
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Tool 1: Publish to Notion
# ---------------------------------------------------------------------------
@tool("publish_to_notion")
def publish_to_notion(title: str, content: str) -> str:
    """Publish a content page to Notion for team review and approval.

    Args:
        title: The title of the content page.
        content: The body content in markdown format.

    Returns:
        JSON string with the Notion page URL and status.
    """
    if USE_MOCK:
        page_id = "ntpg_" + datetime.now().strftime("%Y%m%d%H%M%S")
        result = {
            "status": "published",
            "page_id": page_id,
            "title": title,
            "url": f"https://notion.so/{page_id}",
            "workspace": "Marketing Content Hub",
            "database": "Campaign Copy — Consideration Stage",
            "created_at": datetime.now().isoformat(),
            "created_by": "Campaign Intelligence Crew",
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "review_status": "pending_review",
            "assigned_reviewer": "marketing-team@company.com",
        }
        return json.dumps(result, indent=2)

    # Real API: Notion API
    notion_token = os.environ["NOTION_API_KEY"]
    database_id = os.environ["NOTION_CONTENT_DB_ID"]
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    # Build the Notion page payload
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Draft"}},
            "Stage": {"select": {"name": "Consideration"}},
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                },
            }
        ],
    }
    data = _http_post("https://api.notion.com/v1/pages", headers, payload)
    return json.dumps(
        {
            "status": "published",
            "page_id": data.get("id", ""),
            "url": data.get("url", ""),
            "title": title,
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# Tool 2: Get Content Library
# ---------------------------------------------------------------------------
@tool("get_content_library")
def get_content_library(category: str) -> str:
    """Retrieve available content assets from the marketing content library.

    Args:
        category: Content category to filter by (e.g. 'case_study',
            'whitepaper', 'webinar', 'email_template', 'blog').

    Returns:
        JSON string with a list of content assets matching the category.
    """
    if USE_MOCK:
        library = {
            "category": category,
            "total_assets": 5,
            "assets": [
                {
                    "id": "cnt_001",
                    "title": "The Complete Guide to Marketing Automation in 2026",
                    "type": category,
                    "format": "PDF",
                    "word_count": 4500,
                    "target_persona": "VP of Marketing",
                    "funnel_stage": "consideration",
                    "performance": {
                        "total_downloads": 1_230,
                        "avg_time_on_page_sec": 210,
                        "conversion_rate_pct": 8.5,
                    },
                    "url": "https://content.company.com/guides/marketing-automation-2026",
                    "last_updated": "2026-03-01",
                },
                {
                    "id": "cnt_002",
                    "title": "ROI Calculator: Marketing Platform Consolidation",
                    "type": "interactive_tool",
                    "format": "Web App",
                    "target_persona": "Revenue Operations",
                    "funnel_stage": "consideration",
                    "performance": {
                        "total_completions": 856,
                        "avg_engagement_sec": 340,
                        "conversion_rate_pct": 14.2,
                    },
                    "url": "https://content.company.com/tools/roi-calculator",
                    "last_updated": "2026-02-15",
                },
                {
                    "id": "cnt_003",
                    "title": "How TechCorp Increased MQL-to-SQL by 45%",
                    "type": "case_study",
                    "format": "PDF + Video",
                    "word_count": 2200,
                    "target_persona": "CMO",
                    "funnel_stage": "consideration",
                    "performance": {
                        "total_views": 2_100,
                        "avg_time_on_page_sec": 185,
                        "conversion_rate_pct": 11.3,
                    },
                    "url": "https://content.company.com/case-studies/techcorp",
                    "last_updated": "2026-01-20",
                },
                {
                    "id": "cnt_004",
                    "title": "Consideration Stage Email Templates (10-Pack)",
                    "type": "email_template",
                    "format": "HTML",
                    "target_persona": "All",
                    "funnel_stage": "consideration",
                    "performance": {
                        "avg_open_rate_pct": 32.1,
                        "avg_click_rate_pct": 5.8,
                    },
                    "url": "https://content.company.com/templates/consideration-emails",
                    "last_updated": "2026-03-10",
                },
                {
                    "id": "cnt_005",
                    "title": "Webinar: AI-Powered Personalisation at Scale",
                    "type": "webinar",
                    "format": "Recording + Slides",
                    "duration_minutes": 45,
                    "target_persona": "Marketing Manager",
                    "funnel_stage": "consideration",
                    "performance": {
                        "registrations": 980,
                        "attendees": 412,
                        "meetings_booked": 48,
                    },
                    "url": "https://content.company.com/webinars/ai-personalisation",
                    "last_updated": "2026-02-28",
                },
            ],
        }
        return json.dumps(library, indent=2)

    # Real API: CMS/DAM endpoint
    api_url = os.environ.get("CONTENT_API_URL", "https://api.example.com/content")
    api_key = os.environ["CONTENT_API_KEY"]
    data = _http_get(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        params={"category": category, "stage": "consideration"},
    )
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: Get Case Studies
# ---------------------------------------------------------------------------
@tool("get_case_studies")
def get_case_studies(industry: str) -> str:
    """Retrieve published case studies filtered by industry for use in
    nurture content and social proof.

    Args:
        industry: Industry vertical to filter case studies
            (e.g. 'B2B SaaS', 'FinTech', 'HealthTech').

    Returns:
        JSON string with case study summaries including metrics and quotes.
    """
    if USE_MOCK:
        case_studies = {
            "industry": industry,
            "total_results": 3,
            "case_studies": [
                {
                    "id": "cs_001",
                    "title": f"How DataFlow ({industry}) Reduced CAC by 38%",
                    "customer": "DataFlow Inc.",
                    "industry": industry,
                    "company_size": "350 employees",
                    "challenge": (
                        "Fragmented marketing stack leading to inconsistent "
                        "messaging and high customer acquisition costs."
                    ),
                    "solution": (
                        "Consolidated 5 point solutions into a unified platform "
                        "with AI-driven campaign orchestration."
                    ),
                    "results": {
                        "cac_reduction_pct": 38,
                        "mql_increase_pct": 52,
                        "time_to_value_days": 14,
                        "roi_multiple": "4.2x in first year",
                    },
                    "customer_quote": (
                        "We went from guessing to knowing. The platform's AI "
                        "recommendations helped us focus budget on channels "
                        "that actually drive pipeline. — Sarah Chen, VP Marketing"
                    ),
                    "url": "https://company.com/case-studies/dataflow",
                    "published_date": "2026-02-10",
                },
                {
                    "id": "cs_002",
                    "title": f"ScaleUp ({industry}): 3x Pipeline in 90 Days",
                    "customer": "ScaleUp Technologies",
                    "industry": industry,
                    "company_size": "120 employees",
                    "challenge": (
                        "Manual lead scoring and nurture processes could not "
                        "keep pace with rapid growth targets."
                    ),
                    "solution": (
                        "Implemented agentic AI workflow to automate lead "
                        "scoring, nurture sequencing, and sales hand-off."
                    ),
                    "results": {
                        "pipeline_increase_pct": 200,
                        "response_time_reduction_pct": 85,
                        "sql_conversion_lift_pct": 34,
                        "roi_multiple": "6.1x in six months",
                    },
                    "customer_quote": (
                        "The AI agents work 24/7 nurturing prospects while our "
                        "team focuses on closing. It is like adding 5 SDRs "
                        "without the headcount. — Marcus Webb, Head of Growth"
                    ),
                    "url": "https://company.com/case-studies/scaleup",
                    "published_date": "2026-01-05",
                },
                {
                    "id": "cs_003",
                    "title": f"Enterprise Win: GlobalServ ({industry}) Case Study",
                    "customer": "GlobalServ Solutions",
                    "industry": industry,
                    "company_size": "2,500 employees",
                    "challenge": (
                        "Needed to unify marketing efforts across 12 regional "
                        "teams while maintaining local relevance."
                    ),
                    "solution": (
                        "Deployed centralised campaign intelligence crew with "
                        "localisation layer for regional adaptation."
                    ),
                    "results": {
                        "campaign_launch_speed_improvement_pct": 60,
                        "brand_consistency_score_increase": "72 to 94",
                        "regional_engagement_lift_pct": 28,
                        "roi_multiple": "3.8x in first year",
                    },
                    "customer_quote": (
                        "For the first time, all 12 regions are running "
                        "coordinated campaigns without the endless email "
                        "chains. — Priya Sharma, Global CMO"
                    ),
                    "url": "https://company.com/case-studies/globalserv",
                    "published_date": "2025-11-18",
                },
            ],
        }
        return json.dumps(case_studies, indent=2)

    # Real API: CMS case studies endpoint
    api_url = os.environ.get("CONTENT_API_URL", "https://api.example.com/content")
    api_key = os.environ["CONTENT_API_KEY"]
    data = _http_get(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        params={"type": "case_study", "industry": industry},
    )
    return json.dumps(data, indent=2)
