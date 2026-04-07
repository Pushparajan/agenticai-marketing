# tools/budget_model.py
# Project 7: Campaign Intelligence Room
# Chapter Reference: Chapter 5 - AutoGen
# Description: Budget forecasting and ROI projection tools with mock fallbacks
# Author: Pushparajan Ramar

"""Budget modelling and ROI projection tools.

Provides campaign budget forecasting with channel-level breakdowns and
ROI projections based on spend, cost-per-lead, and conversion
assumptions.  Each function returns deterministic mock data when
USE_MOCK is true (the default) or when no external API is configured.

Environment variables consumed (via .env):
    USE_MOCK  - "true" (default) or "false"
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
# Mock data — budget templates by campaign type
# ---------------------------------------------------------------------------

_BUDGET_TEMPLATES: dict[str, dict[str, Any]] = {
    "pipeline": {
        "campaign_type": "Pipeline Generation",
        "recommended_channels": {
            "linkedin_ads": {
                "pct_of_budget": 30,
                "rationale": "High-intent targeting via matched audiences and InMail",
                "expected_cpl_usd": 185,
                "expected_ctr_pct": 0.45,
            },
            "google_search": {
                "pct_of_budget": 25,
                "rationale": "Capture bottom-funnel demand with branded + category keywords",
                "expected_cpl_usd": 120,
                "expected_ctr_pct": 3.2,
            },
            "content_syndication": {
                "pct_of_budget": 20,
                "rationale": "Gated asset distribution to ICP-matched audiences",
                "expected_cpl_usd": 95,
                "expected_ctr_pct": 1.1,
            },
            "webinars_events": {
                "pct_of_budget": 15,
                "rationale": "Thought-leadership events for mid-funnel engagement",
                "expected_cpl_usd": 250,
                "expected_ctr_pct": None,
            },
            "abm_direct_mail": {
                "pct_of_budget": 10,
                "rationale": "Personalized gifting for target account decision-makers",
                "expected_cpl_usd": 400,
                "expected_ctr_pct": None,
            },
        },
        "benchmarks": {
            "avg_deal_size_usd": 48_000,
            "avg_sales_cycle_days": 90,
            "lead_to_opportunity_pct": 12,
            "opportunity_to_close_pct": 22,
        },
    },
    "brand_awareness": {
        "campaign_type": "Brand Awareness",
        "recommended_channels": {
            "programmatic_display": {
                "pct_of_budget": 40,
                "rationale": "Broad reach across industry publications",
                "expected_cpl_usd": None, "expected_cpm_usd": 8.50,
            },
            "podcast_sponsorship": {
                "pct_of_budget": 30,
                "rationale": "Targeted audio sponsorships on industry shows",
                "expected_cpl_usd": None, "expected_cpm_usd": 25.00,
            },
            "youtube_video": {
                "pct_of_budget": 30,
                "rationale": "Pre-roll on technology and business channels",
                "expected_cpl_usd": None, "expected_cpm_usd": 12.00,
            },
        },
        "benchmarks": {
            "avg_brand_lift_pct": 14,
            "avg_aided_awareness_lift_pct": 8,
            "avg_search_volume_lift_pct": 22,
        },
    },
    "product_launch": {
        "campaign_type": "Product Launch",
        "recommended_channels": {
            "email_nurture": {
                "pct_of_budget": 30,
                "rationale": "Drip sequence to existing database and waitlist",
                "expected_cpl_usd": 15, "expected_ctr_pct": 4.8,
            },
            "linkedin_ads": {
                "pct_of_budget": 35,
                "rationale": "Sponsored content and conversation ads for launch",
                "expected_cpl_usd": 165, "expected_ctr_pct": 0.52,
            },
            "virtual_launch_event": {
                "pct_of_budget": 35,
                "rationale": "Live demo with analyst panel and customer speakers",
                "expected_cpl_usd": 200, "expected_ctr_pct": None,
            },
        },
        "benchmarks": {
            "avg_launch_signups": 2_500,
            "avg_trial_starts": 800,
            "avg_press_mentions": 35,
        },
    },
}


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def forecast_budget(
    campaign_type: str,
    channels: str,
    duration_days: int = 90,
) -> str:
    """Forecast a campaign budget with channel-level breakdowns.

    Generates a budget model based on the campaign type, desired channels,
    and campaign duration.  Returns per-channel spend allocations,
    expected cost-per-lead, and performance benchmarks.

    Args:
        campaign_type: Type of campaign, e.g. "pipeline", "brand_awareness",
                       "product_launch".
        channels:      Comma-separated list of preferred channels,
                       e.g. "linkedin_ads,google_search,content_syndication".
        duration_days: Campaign duration in days (default 90).

    Returns:
        JSON string with budget forecast model.
    """
    log.info(
        "forecast_budget  type=%s  channels=%s  days=%d  mock=%s  ts=%s",
        campaign_type, channels, duration_days, USE_MOCK, _ts(),
    )

    # Normalise campaign type key
    normalized_type = campaign_type.lower().replace(" ", "_").replace("-", "_")
    alias_map: dict[str, str] = {
        "pipeline": "pipeline",
        "pipeline_generation": "pipeline",
        "demand_gen": "pipeline",
        "demand_generation": "pipeline",
        "brand": "brand_awareness",
        "brand_awareness": "brand_awareness",
        "awareness": "brand_awareness",
        "launch": "product_launch",
        "product_launch": "product_launch",
        "product": "product_launch",
    }
    type_key = alias_map.get(normalized_type, "pipeline")
    template = _BUDGET_TEMPLATES.get(type_key, _BUDGET_TEMPLATES["pipeline"])

    # Parse requested channels
    requested_channels = [
        ch.strip().lower().replace(" ", "_").replace("-", "_")
        for ch in channels.split(",")
        if ch.strip()
    ]

    # Build budget model
    base_daily_spend_usd = 550  # baseline for pipeline
    if type_key == "brand_awareness":
        base_daily_spend_usd = 400
    elif type_key == "product_launch":
        base_daily_spend_usd = 750

    total_budget_usd = base_daily_spend_usd * duration_days
    channel_data = template["recommended_channels"]

    # If requested channels match template, use those; otherwise use all
    active_channels: dict[str, Any] = {}
    for ch_name, ch_detail in channel_data.items():
        if not requested_channels or ch_name in requested_channels:
            allocated = round(total_budget_usd * ch_detail["pct_of_budget"] / 100, 2)
            active_channels[ch_name] = {
                **ch_detail,
                "allocated_usd": allocated,
            }

    # Rebalance if only a subset of channels selected
    if active_channels and len(active_channels) < len(channel_data):
        total_pct = sum(ch["pct_of_budget"] for ch in active_channels.values())
        for ch in active_channels.values():
            ch["pct_of_budget"] = round(ch["pct_of_budget"] / total_pct * 100, 1)
            ch["allocated_usd"] = round(
                total_budget_usd * ch["pct_of_budget"] / 100, 2
            )

    result: dict[str, Any] = {
        "campaign_type": template["campaign_type"],
        "duration_days": duration_days,
        "total_budget_usd": total_budget_usd,
        "daily_spend_usd": base_daily_spend_usd,
        "channel_allocations": active_channels,
        "benchmarks": template.get("benchmarks", {}),
        "assumptions": {
            "currency": "USD",
            "pricing_model": "blended CPL / CPM estimates",
            "seasonality_adjustment": "none applied — adjust for Q4 surcharges",
            "note": (
                "Forecasts are based on industry median benchmarks. "
                "Actual performance will vary based on targeting quality, "
                "creative effectiveness, and competitive intensity."
            ),
        },
        "forecasted_at": _ts(),
    }

    log.info(
        "Returning budget forecast: type=%s  total=$%s  channels=%d",
        type_key, total_budget_usd, len(active_channels),
    )
    return json.dumps(result, indent=2)


def calculate_roi_projection(
    spend: float,
    expected_cpl: float,
    conversion_rate: float,
) -> str:
    """Project return-on-investment for a campaign spend scenario.

    Calculates leads generated, expected conversions, projected revenue,
    and ROI ratio based on spend, cost-per-lead, and conversion rate
    assumptions.

    Args:
        spend:           Total campaign spend in USD.
        expected_cpl:    Expected cost per lead in USD.
        conversion_rate: Lead-to-customer conversion rate as a percentage
                         (e.g. 2.5 for 2.5%).

    Returns:
        JSON string with ROI projection model.
    """
    log.info(
        "calculate_roi_projection  spend=%.2f  cpl=%.2f  conv=%.2f%%  ts=%s",
        spend, expected_cpl, conversion_rate, _ts(),
    )

    # Avoid division by zero
    if expected_cpl <= 0:
        expected_cpl = 100.0
    if conversion_rate <= 0:
        conversion_rate = 2.0

    leads_generated = int(spend / expected_cpl)
    customers_acquired = int(leads_generated * (conversion_rate / 100))

    # Use realistic enterprise SaaS assumptions
    avg_deal_size_usd = 48_000.0
    projected_revenue = customers_acquired * avg_deal_size_usd
    roi_ratio = (projected_revenue - spend) / spend if spend > 0 else 0.0

    # Build scenario table with sensitivity ranges
    scenarios: list[dict[str, Any]] = []
    for label, cpl_mult, conv_mult in [
        ("pessimistic", 1.35, 0.65),
        ("base", 1.0, 1.0),
        ("optimistic", 0.75, 1.40),
    ]:
        s_cpl = expected_cpl * cpl_mult
        s_conv = conversion_rate * conv_mult
        s_leads = int(spend / s_cpl)
        s_customers = int(s_leads * (s_conv / 100))
        s_revenue = s_customers * avg_deal_size_usd
        s_roi = (s_revenue - spend) / spend if spend > 0 else 0.0
        scenarios.append({
            "scenario": label,
            "adjusted_cpl_usd": round(s_cpl, 2),
            "adjusted_conversion_pct": round(s_conv, 2),
            "leads": s_leads,
            "customers": s_customers,
            "projected_revenue_usd": round(s_revenue, 2),
            "roi_ratio": round(s_roi, 2),
        })

    result: dict[str, Any] = {
        "inputs": {
            "spend_usd": round(spend, 2),
            "expected_cpl_usd": round(expected_cpl, 2),
            "conversion_rate_pct": round(conversion_rate, 2),
        },
        "base_projection": {
            "leads_generated": leads_generated,
            "customers_acquired": customers_acquired,
            "avg_deal_size_usd": avg_deal_size_usd,
            "projected_revenue_usd": round(projected_revenue, 2),
            "roi_ratio": round(roi_ratio, 2),
            "roi_pct": round(roi_ratio * 100, 1),
            "payback_period_months": (
                round(spend / (projected_revenue / 12), 1)
                if projected_revenue > 0
                else None
            ),
        },
        "sensitivity_analysis": scenarios,
        "assumptions": {
            "avg_deal_size_source": "Company median ACV (last 4 quarters)",
            "note": (
                "ROI projection does not account for sales team costs, "
                "opportunity-stage discounting, or multi-touch attribution. "
                "Use as a directional planning estimate."
            ),
        },
        "projected_at": _ts(),
    }

    log.info(
        "ROI projection: leads=%d  customers=%d  revenue=$%.0f  ROI=%.1f%%",
        leads_generated, customers_acquired, projected_revenue, roi_ratio * 100,
    )
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Campaign Intelligence Room — Budget Model Tools Demo")
    print("=" * 60)
    print(f"\nUSE_MOCK = {USE_MOCK}\n")

    print("--- Budget Forecast: Pipeline Campaign ---")
    print(forecast_budget("pipeline", "linkedin_ads,google_search", 90))

    print("\n--- ROI Projection: $50k spend ---")
    print(calculate_roi_projection(50_000, 150.0, 2.5))
