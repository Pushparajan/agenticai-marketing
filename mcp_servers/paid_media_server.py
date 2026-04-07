# File      : paid_media_server.py
# Stage     : All Stages
# Chapter   : 13-14
# Framework : MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Google Ads Paid Media MCP Server
Provides tools for campaign management, bid optimisation, audience creation,
budget allocation, and keyword analysis for the Awareness stage.
"""

import json
import os
import logging
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PAID-MEDIA] %(message)s")
logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("MCP_MOCK", "true").lower() == "true"
GOOGLE_ADS_API_KEY = os.getenv("GOOGLE_ADS_API_KEY", "")

mcp = FastMCP("paid-media-google-ads")


@mcp.tool()
def get_campaign_performance(campaign_id: str, date_range: str) -> str:
    """Retrieve performance metrics for a Google Ads campaign over a date range."""
    logger.info("get_campaign_performance called | campaign_id=%s range=%s", campaign_id, date_range)
    if not USE_MOCK:
        # Real API: Google Ads API - GoogleAdsService.SearchStream
        pass
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "SaaS Awareness - Brand Keywords Q2",
        "date_range": date_range,
        "status": "enabled",
        "metrics": {
            "impressions": 284500,
            "clicks": 8535,
            "ctr": 0.030,
            "avg_cpc": 2.84,
            "cost": 24239.40,
            "conversions": 342,
            "conversion_rate": 0.040,
            "cost_per_conversion": 70.88,
            "view_through_conversions": 128
        },
        "quality_score_avg": 7.2,
        "impression_share": 0.68
    })


@mcp.tool()
def adjust_bid(campaign_id: str, ad_group_id: str, bid_amount: float, bid_strategy: str) -> str:
    """Adjust the bid for an ad group within a campaign."""
    logger.info("adjust_bid called | campaign=%s ad_group=%s bid=%.2f", campaign_id, ad_group_id, bid_amount)
    if not USE_MOCK:
        # Real API: Google Ads API - MutateAdGroupBids
        pass
    return json.dumps({
        "campaign_id": campaign_id,
        "ad_group_id": ad_group_id,
        "previous_bid": 2.50,
        "new_bid": bid_amount,
        "bid_strategy": bid_strategy,
        "currency": "USD",
        "estimated_impact": {
            "impression_change_pct": 12.5,
            "click_change_pct": 8.3,
            "cost_change_pct": 15.2
        },
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "status": "success"
    })


@mcp.tool()
def create_audience(audience_name: str, source: str, criteria: str) -> str:
    """Create a custom audience in Google Ads from CRM data or website visitors."""
    logger.info("create_audience called | name=%s source=%s", audience_name, source)
    if not USE_MOCK:
        # Real API: Google Ads API - MutateUserLists
        pass
    return json.dumps({
        "audience_id": "AUD-77432",
        "audience_name": audience_name,
        "source": source,
        "criteria": json.loads(criteria) if criteria else {},
        "estimated_size": 18500,
        "match_rate": 0.72,
        "status": "populating",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "estimated_ready": (datetime.utcnow() + timedelta(hours=6)).isoformat() + "Z"
    })


@mcp.tool()
def pause_campaign(campaign_id: str, reason: str) -> str:
    """Pause an active Google Ads campaign with a documented reason."""
    logger.info("pause_campaign called | campaign_id=%s reason=%s", campaign_id, reason)
    if not USE_MOCK:
        # Real API: Google Ads API - MutateCampaigns (status=PAUSED)
        pass
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "SaaS Awareness - Brand Keywords Q2",
        "previous_status": "enabled",
        "new_status": "paused",
        "reason": reason,
        "daily_spend_saved": 807.98,
        "paused_at": datetime.utcnow().isoformat() + "Z",
        "status": "success"
    })


@mcp.tool()
def get_roas(campaign_id: str, attribution_window: str) -> str:
    """Calculate return on ad spend for a campaign across an attribution window."""
    logger.info("get_roas called | campaign_id=%s window=%s", campaign_id, attribution_window)
    if not USE_MOCK:
        # Real API: Google Ads API - campaign performance with conversion value
        pass
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "SaaS Awareness - Brand Keywords Q2",
        "attribution_window": attribution_window,
        "total_spend": 24239.40,
        "total_revenue": 89600.00,
        "roas": 3.70,
        "roas_trend": [
            {"week": "W13", "roas": 3.2},
            {"week": "W14", "roas": 3.8},
            {"week": "W15", "roas": 4.1}
        ],
        "benchmark_roas": 2.8,
        "performance_vs_benchmark": "above",
        "computed_at": datetime.utcnow().isoformat() + "Z"
    })


@mcp.tool()
def allocate_budget(campaign_ids: str, total_budget: float, strategy: str) -> str:
    """Allocate budget across multiple campaigns based on performance strategy."""
    logger.info("allocate_budget called | total=%.2f strategy=%s", total_budget, strategy)
    if not USE_MOCK:
        # Real API: Google Ads API - MutateCampaignBudgets
        pass
    ids = json.loads(campaign_ids) if campaign_ids else []
    return json.dumps({
        "total_budget": total_budget,
        "strategy": strategy,
        "currency": "USD",
        "allocations": [
            {"campaign_id": "CMP-1001", "campaign_name": "Brand Keywords", "allocation": total_budget * 0.35, "pct": 35, "reason": "Highest ROAS (4.1x)"},
            {"campaign_id": "CMP-1002", "campaign_name": "Competitor Conquesting", "allocation": total_budget * 0.25, "pct": 25, "reason": "Growing impression share"},
            {"campaign_id": "CMP-1003", "campaign_name": "Content Syndication", "allocation": total_budget * 0.22, "pct": 22, "reason": "Strong MQL pipeline"},
            {"campaign_id": "CMP-1004", "campaign_name": "Retargeting", "allocation": total_budget * 0.18, "pct": 18, "reason": "High conversion rate"}
        ],
        "effective_from": datetime.utcnow().isoformat() + "Z",
        "status": "applied"
    })


@mcp.tool()
def get_keyword_intent_data(keywords: str, match_type: str) -> str:
    """Retrieve intent classification and performance data for keywords."""
    logger.info("get_keyword_intent_data called | match_type=%s", match_type)
    if not USE_MOCK:
        # Real API: Google Ads Keyword Planner + custom intent model
        pass
    return json.dumps({
        "match_type": match_type,
        "keywords": [
            {"keyword": "marketing automation software", "intent": "commercial", "search_volume": 14800, "cpc": 12.40, "competition": "high", "trend": "rising"},
            {"keyword": "best crm for saas", "intent": "commercial", "search_volume": 8200, "cpc": 15.80, "competition": "high", "trend": "stable"},
            {"keyword": "customer journey mapping tool", "intent": "informational", "search_volume": 6100, "cpc": 8.20, "competition": "medium", "trend": "rising"},
            {"keyword": "hubspot vs salesforce", "intent": "comparison", "search_volume": 22000, "cpc": 18.50, "competition": "high", "trend": "stable"},
            {"keyword": "how to reduce churn rate", "intent": "informational", "search_volume": 4300, "cpc": 5.60, "competition": "low", "trend": "rising"}
        ],
        "analysed_at": datetime.utcnow().isoformat() + "Z"
    })


@mcp.tool()
def create_retargeting_list(list_name: str, source_url_pattern: str, lookback_days: int) -> str:
    """Create a retargeting audience list based on website visitor URL patterns."""
    logger.info("create_retargeting_list called | name=%s pattern=%s days=%d", list_name, source_url_pattern, lookback_days)
    if not USE_MOCK:
        # Real API: Google Ads API - MutateRemarketingActions + UserLists
        pass
    return json.dumps({
        "list_id": "RTG-44218",
        "list_name": list_name,
        "source_url_pattern": source_url_pattern,
        "lookback_days": lookback_days,
        "estimated_size": 7200,
        "status": "populating",
        "excluded_converters": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "ready_for_targeting": (datetime.utcnow() + timedelta(hours=4)).isoformat() + "Z"
    })


if __name__ == "__main__":
    mcp.run()
