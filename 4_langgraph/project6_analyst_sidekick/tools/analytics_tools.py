# tools/analytics_tools.py
# Project 6: MarTech Analyst Sidekick
# Chapter Reference: Chapter 4 - LangGraph
# Description: Amplitude and Google Analytics query tools with mock fallbacks
# Author: Pushparajan Ramar

"""Marketing analytics query tools for Amplitude and Google Analytics.

Provides funnel metric retrieval from Amplitude and dimension-based
reporting from Google Analytics.  Each function attempts the real API
first, falling back to deterministic mock data when USE_MOCK is true or
the API key is absent.

Environment variables consumed (via .env):
    USE_MOCK              - "true" (default) or "false"
    AMPLITUDE_API_KEY     - Amplitude API key
    AMPLITUDE_SECRET_KEY  - Amplitude secret key
    GA4_PROPERTY_ID       - Google Analytics 4 property ID
    GOOGLE_APPLICATION_CREDENTIALS - path to GCP service-account JSON
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
AMPLITUDE_API_KEY: str = os.getenv("AMPLITUDE_API_KEY", "")
AMPLITUDE_SECRET_KEY: str = os.getenv("AMPLITUDE_SECRET_KEY", "")
GA4_PROPERTY_ID: str = os.getenv("GA4_PROPERTY_ID", "")

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
# Mock data
# ---------------------------------------------------------------------------

_MOCK_FUNNELS: dict[str, dict[str, Any]] = {
    "signup_to_purchase": {
        "funnel_name": "Signup to Purchase",
        "date_range": "last_quarter",
        "steps": [
            {"step": 1, "name": "Visited Signup Page", "users": 24_530, "conversion_rate": 1.0},
            {"step": 2, "name": "Completed Signup", "users": 9_812, "conversion_rate": 0.40},
            {"step": 3, "name": "Activated Account", "users": 6_368, "conversion_rate": 0.649},
            {"step": 4, "name": "Added to Cart", "users": 3_184, "conversion_rate": 0.500},
            {"step": 5, "name": "Completed Purchase", "users": 1_752, "conversion_rate": 0.550},
        ],
        "overall_conversion": 0.0714,
        "median_time_to_convert_hours": 72.5,
        "top_dropoff_step": "Visited Signup Page -> Completed Signup (60% drop-off)",
    },
    "trial_to_paid": {
        "funnel_name": "Free Trial to Paid",
        "date_range": "last_quarter",
        "steps": [
            {"step": 1, "name": "Started Free Trial", "users": 8_420, "conversion_rate": 1.0},
            {"step": 2, "name": "Completed Onboarding", "users": 5_894, "conversion_rate": 0.70},
            {"step": 3, "name": "Used Core Feature 3+ Times", "users": 3_536, "conversion_rate": 0.60},
            {"step": 4, "name": "Viewed Pricing Page", "users": 2_475, "conversion_rate": 0.70},
            {"step": 5, "name": "Upgraded to Paid Plan", "users": 1_485, "conversion_rate": 0.60},
        ],
        "overall_conversion": 0.1764,
        "median_time_to_convert_hours": 168.0,
        "top_dropoff_step": "Completed Onboarding -> Used Core Feature 3+ Times (40% drop-off)",
    },
    "lead_to_demo": {
        "funnel_name": "Lead to Demo Booked",
        "date_range": "last_quarter",
        "steps": [
            {"step": 1, "name": "Form Submitted (MQL)", "users": 3_210, "conversion_rate": 1.0},
            {"step": 2, "name": "SDR Contacted", "users": 2_568, "conversion_rate": 0.80},
            {"step": 3, "name": "Responded to Outreach", "users": 1_027, "conversion_rate": 0.40},
            {"step": 4, "name": "Demo Booked", "users": 719, "conversion_rate": 0.70},
        ],
        "overall_conversion": 0.224,
        "median_time_to_convert_hours": 48.0,
        "top_dropoff_step": "SDR Contacted -> Responded to Outreach (60% drop-off)",
    },
}

_MOCK_GA_DATA: dict[str, dict[str, Any]] = {
    "sessions": {
        "metric": "sessions",
        "total": 185_420,
        "by_source": {
            "google / organic": 68_405,
            "direct / (none)": 37_084,
            "facebook / cpc": 22_250,
            "linkedin / cpc": 18_542,
            "email / newsletter": 14_834,
            "google / cpc": 12_978,
            "referral / partner-blog": 7_417,
            "twitter / social": 3_910,
        },
        "period": "2026-01-01 to 2026-03-31",
    },
    "conversion_rate": {
        "metric": "conversion_rate",
        "overall": 0.034,
        "by_channel": {
            "email / newsletter": 0.062,
            "google / organic": 0.041,
            "linkedin / cpc": 0.038,
            "referral / partner-blog": 0.035,
            "google / cpc": 0.029,
            "direct / (none)": 0.025,
            "facebook / cpc": 0.018,
            "twitter / social": 0.012,
        },
        "period": "2026-01-01 to 2026-03-31",
    },
    "revenue": {
        "metric": "revenue",
        "total_pipeline": 4_275_000,
        "by_channel": {
            "google / organic": 1_412_000,
            "linkedin / cpc": 983_000,
            "email / newsletter": 745_000,
            "direct / (none)": 512_000,
            "google / cpc": 328_000,
            "referral / partner-blog": 185_000,
            "facebook / cpc": 78_000,
            "twitter / social": 32_000,
        },
        "currency": "USD",
        "period": "2026-01-01 to 2026-03-31",
    },
    "bounce_rate": {
        "metric": "bounce_rate",
        "overall": 0.42,
        "by_landing_page": {
            "/": 0.35,
            "/pricing": 0.28,
            "/blog": 0.55,
            "/product/features": 0.32,
            "/case-studies": 0.30,
            "/demo-request": 0.18,
            "/resources/whitepapers": 0.48,
        },
        "period": "2026-01-01 to 2026-03-31",
    },
    "email_open_rate": {
        "metric": "email_open_rate",
        "overall": 0.287,
        "by_segment": {
            "Enterprise (10k+ employees)": 0.312,
            "Mid-Market (500-10k)": 0.295,
            "SMB (50-500)": 0.268,
            "Startup (<50)": 0.241,
            "Churned Re-engagement": 0.185,
            "Newsletter Subscribers": 0.342,
            "Product Updates": 0.398,
            "Event Invites": 0.265,
        },
        "period": "2026-01-01 to 2026-03-31",
    },
    "cac": {
        "metric": "customer_acquisition_cost",
        "current_quarter": 347,
        "trend": [
            {"quarter": "Q1 2025", "cac": 412},
            {"quarter": "Q2 2025", "cac": 389},
            {"quarter": "Q3 2025", "cac": 371},
            {"quarter": "Q4 2025", "cac": 358},
            {"quarter": "Q1 2026", "cac": 347},
        ],
        "by_channel": {
            "google / organic": 128,
            "email / newsletter": 95,
            "linkedin / cpc": 285,
            "google / cpc": 310,
            "referral / partner-blog": 175,
            "facebook / cpc": 420,
            "twitter / social": 580,
        },
        "currency": "USD",
        "period": "2026-01-01 to 2026-03-31",
    },
}


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def query_amplitude_funnel(funnel_name: str, date_range: str = "last_quarter") -> str:
    """Query Amplitude for funnel conversion metrics.

    Retrieves step-by-step conversion data, overall conversion rate,
    median conversion time, and identifies the highest drop-off step.

    Args:
        funnel_name: The funnel identifier, e.g. "signup_to_purchase",
                     "trial_to_paid", or "lead_to_demo".
        date_range:  Human-readable date range such as "last_quarter",
                     "last_30_days", or "2026-01-01 to 2026-03-31".

    Returns:
        JSON string with funnel steps, conversion rates, and drop-off data.
    """
    log.info(
        "query_amplitude_funnel  funnel=%s  range=%s  mock=%s  ts=%s",
        funnel_name, date_range, USE_MOCK, _ts(),
    )

    if not USE_MOCK and AMPLITUDE_API_KEY and AMPLITUDE_SECRET_KEY:
        try:
            import requests

            resp = requests.get(
                "https://amplitude.com/api/2/funnels",
                params={"e": funnel_name, "start": date_range},
                auth=(AMPLITUDE_API_KEY, AMPLITUDE_SECRET_KEY),
                timeout=15,
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), indent=2)
        except Exception as exc:
            log.warning("Amplitude API call failed, using mock data: %s", exc)

    # ----- mock fallback -----
    normalized = funnel_name.lower().replace(" ", "_").replace("-", "_")
    data = _MOCK_FUNNELS.get(normalized)
    if data is None:
        # Return a generic funnel if the name is unrecognized
        data = {
            "funnel_name": funnel_name,
            "date_range": date_range,
            "steps": [
                {"step": 1, "name": "Awareness", "users": 15_000, "conversion_rate": 1.0},
                {"step": 2, "name": "Interest", "users": 6_000, "conversion_rate": 0.40},
                {"step": 3, "name": "Consideration", "users": 2_400, "conversion_rate": 0.40},
                {"step": 4, "name": "Conversion", "users": 960, "conversion_rate": 0.40},
            ],
            "overall_conversion": 0.064,
            "median_time_to_convert_hours": 96.0,
            "top_dropoff_step": "Awareness -> Interest (60% drop-off)",
        }
    else:
        data = {**data, "date_range": date_range}

    data["queried_at"] = _ts()
    log.info("Returning mock Amplitude funnel data for '%s'", funnel_name)
    return json.dumps(data, indent=2)


def query_google_analytics(
    metric: str,
    dimension: str = "source_medium",
    date_range: str = "last_quarter",
) -> str:
    """Query Google Analytics 4 for a specific metric broken down by dimension.

    Supports metrics such as sessions, conversion_rate, revenue,
    bounce_rate, email_open_rate, and cac (customer acquisition cost).

    Args:
        metric:     The metric to retrieve, e.g. "sessions", "revenue",
                    "conversion_rate", "bounce_rate", "email_open_rate", "cac".
        dimension:  The dimension to break down by, e.g. "source_medium",
                    "landing_page", "segment", "channel".
        date_range: Human-readable date range such as "last_quarter" or
                    "2026-01-01 to 2026-03-31".

    Returns:
        JSON string with the requested metric and dimensional breakdown.
    """
    log.info(
        "query_google_analytics  metric=%s  dimension=%s  range=%s  mock=%s  ts=%s",
        metric, dimension, date_range, USE_MOCK, _ts(),
    )

    if not USE_MOCK and GA4_PROPERTY_ID:
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import (
                DateRange,
                Dimension,
                Metric,
                RunReportRequest,
            )

            client = BetaAnalyticsDataClient()
            request = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                date_ranges=[DateRange(start_date="90daysAgo", end_date="today")],
                dimensions=[Dimension(name=dimension)],
                metrics=[Metric(name=metric)],
            )
            response = client.run_report(request)
            rows = [
                {
                    dimension: row.dimension_values[0].value,
                    metric: row.metric_values[0].value,
                }
                for row in response.rows
            ]
            return json.dumps({"metric": metric, "dimension": dimension, "rows": rows}, indent=2)
        except Exception as exc:
            log.warning("GA4 API call failed, using mock data: %s", exc)

    # ----- mock fallback -----
    normalized = metric.lower().replace(" ", "_").replace("-", "_")
    # Handle common aliases
    alias_map = {
        "customer_acquisition_cost": "cac",
        "open_rate": "email_open_rate",
        "email_opens": "email_open_rate",
        "pipeline": "revenue",
        "traffic": "sessions",
    }
    normalized = alias_map.get(normalized, normalized)

    data = _MOCK_GA_DATA.get(normalized)
    if data is None:
        data = {
            "metric": metric,
            "note": f"No mock data found for metric '{metric}'. "
                    "Available metrics: sessions, conversion_rate, revenue, "
                    "bounce_rate, email_open_rate, cac.",
        }
    else:
        data = {**data, "dimension": dimension, "date_range": date_range}

    data["queried_at"] = _ts()
    log.info("Returning mock GA data for metric='%s'", metric)
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MarTech Analyst Sidekick — Analytics Tools Demo")
    print("=" * 60)
    print(f"\nUSE_MOCK = {USE_MOCK}\n")

    print("--- Amplitude: signup_to_purchase ---")
    print(query_amplitude_funnel("signup_to_purchase"))

    print("\n--- GA: sessions by source ---")
    print(query_google_analytics("sessions"))

    print("\n--- GA: email_open_rate by segment ---")
    print(query_google_analytics("email_open_rate", dimension="segment"))

    print("\n--- GA: CAC trend ---")
    print(query_google_analytics("cac", dimension="channel"))
