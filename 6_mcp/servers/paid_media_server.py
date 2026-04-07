"""
File: paid_media_server.py
Project: Marketing Operations Command Centre — Chapter 8
Description: MCP server for Google Ads paid media management
Author: Pushparajan Ramar
"""
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
logger = logging.getLogger(__name__)
USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

mcp = FastMCP("google-ads-media")


@mcp.tool()
def get_campaign_performance(campaign_id: str, date_range: str = "LAST_30_DAYS") -> str:
    """Retrieve performance metrics for a Google Ads campaign.

    Args:
        campaign_id: The Google Ads campaign identifier.
        date_range: Reporting period (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS).

    Returns:
        JSON string with impressions, clicks, conversions, cost,
        and ROAS for the campaign.
    """
    logger.info("[%s] get_campaign_performance: %s (%s)",
                datetime.now().isoformat(), campaign_id, date_range)
    if not USE_MOCK:
        # Real API: google-ads-python client
        # from google.ads.googleads.client import GoogleAdsClient
        # client = GoogleAdsClient.load_from_storage()
        pass
    # MOCK MODE
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "Brand — Enterprise SaaS — Search",
        "status": "enabled",
        "date_range": date_range,
        "impressions": 284310,
        "clicks": 9842,
        "ctr": 0.0346,
        "conversions": 312,
        "conversion_rate": 0.0317,
        "cost": 18420.50,
        "cpc": 1.87,
        "cpa": 59.04,
        "roas": 4.62,
        "revenue_attributed": 85102.00,
        "quality_score_avg": 7.8,
        "impression_share": 0.72,
    })


@mcp.tool()
def adjust_bid(campaign_id: str, ad_group_id: str, bid_modifier: float) -> str:
    """Adjust the bid modifier for an ad group within a campaign.

    Args:
        campaign_id: The Google Ads campaign identifier.
        ad_group_id: The ad group to modify.
        bid_modifier: Multiplier to apply (e.g. 1.2 for +20%).
    """
    logger.info("[%s] adjust_bid: campaign=%s, ad_group=%s, modifier=%.2f",
                datetime.now().isoformat(), campaign_id, ad_group_id, bid_modifier)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "campaign_id": campaign_id,
        "ad_group_id": ad_group_id,
        "ad_group_name": "Enterprise — Demo Request",
        "previous_bid": 2.40,
        "new_bid": round(2.40 * bid_modifier, 2),
        "bid_modifier": bid_modifier,
        "estimated_impact": {
            "impressions_change_pct": round((bid_modifier - 1.0) * 0.6 * 100, 1),
            "clicks_change_pct": round((bid_modifier - 1.0) * 0.5 * 100, 1),
            "cost_change_pct": round((bid_modifier - 1.0) * 100, 1),
        },
        "applied_at": datetime.now().isoformat(),
        "applied_by": "marketing-ops-agent",
        "status": "success",
    })


@mcp.tool()
def create_audience(name: str, source: str, description: str = "") -> str:
    """Create a custom audience in Google Ads for targeting.

    Args:
        name: Display name for the audience.
        source: Data source (crm_list, website_visitors, lookalike, segment_sync).
        description: Optional description of the audience criteria.
    """
    logger.info("[%s] create_audience: %s (source=%s)",
                datetime.now().isoformat(), name, source)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "audience_id": "AUD-449821",
        "name": name,
        "source": source,
        "description": description or "Custom audience synced from CDP",
        "estimated_size": 14200,
        "match_rate": 0.82,
        "status": "processing",
        "availability_eta": "2026-04-08T06:00:00Z",
        "created_at": datetime.now().isoformat(),
        "created_by": "marketing-ops-agent",
    })


@mcp.tool()
def pause_campaign(campaign_id: str, reason: str = "manual pause") -> str:
    """Pause an active Google Ads campaign.

    Args:
        campaign_id: The campaign to pause.
        reason: Reason for pausing the campaign.
    """
    logger.info("[%s] pause_campaign: %s (reason=%s)",
                datetime.now().isoformat(), campaign_id, reason)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "Brand — Enterprise SaaS — Search",
        "previous_status": "enabled",
        "new_status": "paused",
        "reason": reason,
        "daily_budget_freed": 620.00,
        "active_ad_groups_paused": 4,
        "paused_at": datetime.now().isoformat(),
        "paused_by": "marketing-ops-agent",
    })


@mcp.tool()
def get_roas(campaign_id: str, attribution_model: str = "data_driven") -> str:
    """Calculate return on ad spend for a campaign with attribution.

    Args:
        campaign_id: The Google Ads campaign identifier.
        attribution_model: Attribution model (last_click, first_click,
                           linear, data_driven).

    Returns:
        JSON string with ROAS breakdown by attribution model and channel.
    """
    logger.info("[%s] get_roas: %s (model=%s)",
                datetime.now().isoformat(), campaign_id, attribution_model)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "Brand — Enterprise SaaS — Search",
        "attribution_model": attribution_model,
        "period": "last_30_days",
        "total_spend": 18420.50,
        "total_revenue": 85102.00,
        "roas": 4.62,
        "by_conversion_action": [
            {"action": "demo_request", "conversions": 142, "revenue": 52400.00, "roas": 5.84},
            {"action": "trial_signup", "conversions": 98, "revenue": 21200.00, "roas": 3.41},
            {"action": "content_download", "conversions": 72, "revenue": 11502.00, "roas": 2.18},
        ],
        "model_comparison": {
            "last_click_roas": 3.91,
            "first_click_roas": 4.12,
            "linear_roas": 4.38,
            "data_driven_roas": 4.62,
        },
        "computed_at": datetime.now().isoformat(),
    })


@mcp.tool()
def allocate_budget(total_budget: float, strategy: str = "maximize_conversions") -> str:
    """Recommend budget allocation across active campaigns.

    Args:
        total_budget: Total daily budget in USD to allocate.
        strategy: Optimisation strategy (maximize_conversions,
                  maximize_roas, balanced).

    Returns:
        JSON string with per-campaign budget recommendations.
    """
    logger.info("[%s] allocate_budget: $%.2f (strategy=%s)",
                datetime.now().isoformat(), total_budget, strategy)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "total_daily_budget": total_budget,
        "strategy": strategy,
        "allocation": [
            {"campaign": "Brand — Enterprise SaaS — Search", "current_budget": 620.00,
             "recommended_budget": round(total_budget * 0.35, 2), "expected_roas": 4.62},
            {"campaign": "Non-Brand — Marketing Automation", "current_budget": 480.00,
             "recommended_budget": round(total_budget * 0.25, 2), "expected_roas": 3.18},
            {"campaign": "Retargeting — Website Visitors", "current_budget": 340.00,
             "recommended_budget": round(total_budget * 0.20, 2), "expected_roas": 5.41},
            {"campaign": "Display — Lookalike Audiences", "current_budget": 280.00,
             "recommended_budget": round(total_budget * 0.12, 2), "expected_roas": 2.04},
            {"campaign": "YouTube — Brand Awareness", "current_budget": 180.00,
             "recommended_budget": round(total_budget * 0.08, 2), "expected_roas": 1.62},
        ],
        "estimated_total_roas": 3.87,
        "computed_at": datetime.now().isoformat(),
    })


@mcp.tool()
def get_keyword_data(campaign_id: str, min_impressions: int = 100) -> str:
    """Retrieve keyword performance data for a search campaign.

    Args:
        campaign_id: The Google Ads campaign identifier.
        min_impressions: Minimum impressions threshold to include a keyword.

    Returns:
        JSON string with keyword-level metrics.
    """
    logger.info("[%s] get_keyword_data: %s (min_impr=%d)",
                datetime.now().isoformat(), campaign_id, min_impressions)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "campaign_id": campaign_id,
        "period": "last_30_days",
        "min_impressions": min_impressions,
        "total_keywords": 48,
        "keywords": [
            {"keyword": "marketing automation platform", "match_type": "phrase",
             "impressions": 18420, "clicks": 812, "ctr": 0.0441, "cpc": 3.12, "conversions": 34, "qs": 9},
            {"keyword": "enterprise email marketing", "match_type": "broad",
             "impressions": 12840, "clicks": 494, "ctr": 0.0385, "cpc": 2.78, "conversions": 21, "qs": 8},
            {"keyword": "crm marketing integration", "match_type": "exact",
             "impressions": 8210, "clicks": 389, "ctr": 0.0474, "cpc": 2.44, "conversions": 18, "qs": 8},
            {"keyword": "martech stack consolidation", "match_type": "phrase",
             "impressions": 4120, "clicks": 178, "ctr": 0.0432, "cpc": 4.21, "conversions": 9, "qs": 7},
            {"keyword": "b2b marketing software", "match_type": "broad",
             "impressions": 22100, "clicks": 642, "ctr": 0.0290, "cpc": 3.58, "conversions": 14, "qs": 6},
        ],
    })


@mcp.tool()
def create_ad_group(campaign_id: str, name: str, keywords: str, default_bid: float = 2.50) -> str:
    """Create a new ad group within a Google Ads campaign.

    Args:
        campaign_id: The parent campaign identifier.
        name: Name for the new ad group.
        keywords: Comma-separated list of target keywords.
        default_bid: Default CPC bid in USD.

    Returns:
        JSON string with the created ad group details.
    """
    logger.info("[%s] create_ad_group: %s in campaign %s",
                datetime.now().isoformat(), name, campaign_id)
    if not USE_MOCK:
        pass
    # MOCK MODE
    keyword_list = [kw.strip() for kw in keywords.split(",")]
    return json.dumps({
        "ad_group_id": "AG-882041",
        "campaign_id": campaign_id,
        "name": name,
        "status": "enabled",
        "default_bid": default_bid,
        "keywords_added": len(keyword_list),
        "keywords": [
            {"keyword": kw, "match_type": "phrase", "bid": default_bid}
            for kw in keyword_list
        ],
        "ads_required": True,
        "created_at": datetime.now().isoformat(),
        "created_by": "marketing-ops-agent",
    })


if __name__ == "__main__":
    mcp.run()
