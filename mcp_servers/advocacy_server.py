# File      : advocacy_server.py
# Stage     : All Stages
# Chapter   : 13-14
# Framework : MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
G2/Capterra Advocacy MCP Server
Provides tools for advocate identification, review requests, referral programmes,
community management, and NPS analysis for the Advocacy stage.
"""

import json
import os
import logging
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ADVOCACY] %(message)s")
logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("MCP_MOCK", "true").lower() == "true"
G2_API_KEY = os.getenv("G2_API_KEY", "")
CAPTERRA_API_KEY = os.getenv("CAPTERRA_API_KEY", "")

mcp = FastMCP("advocacy-g2-capterra")


@mcp.tool()
def identify_advocates(min_nps: int, min_usage_days: int, min_tenure_months: int) -> str:
    """Identify potential advocates based on NPS score, product usage, and tenure criteria."""
    logger.info("identify_advocates called | min_nps=%d min_usage_days=%d min_tenure=%d", min_nps, min_usage_days, min_tenure_months)
    if not USE_MOCK:
        # Real API: Internal CRM + product analytics query
        pass
    return json.dumps({
        "criteria": {
            "min_nps": min_nps,
            "min_usage_days_per_month": min_usage_days,
            "min_tenure_months": min_tenure_months
        },
        "total_advocates_found": 124,
        "advocates": [
            {"user_id": "USR-3001", "name": "Emily Chen", "company": "DataPulse Inc", "nps": 10, "usage_days": 26, "tenure_months": 14, "tier": "platinum"},
            {"user_id": "USR-3002", "name": "Marcus Johnson", "company": "CloudForge", "nps": 9, "usage_days": 24, "tenure_months": 11, "tier": "gold"},
            {"user_id": "USR-3003", "name": "Priya Sharma", "company": "NexGen Analytics", "nps": 10, "usage_days": 28, "tenure_months": 18, "tier": "platinum"},
            {"user_id": "USR-3004", "name": "Tom Wilson", "company": "ScaleOps", "nps": 9, "usage_days": 22, "tenure_months": 9, "tier": "gold"},
            {"user_id": "USR-3005", "name": "Aisha Rahman", "company": "BrightMetrics", "nps": 10, "usage_days": 25, "tenure_months": 16, "tier": "platinum"}
        ],
        "identified_at": datetime.utcnow().isoformat() + "Z"
    })


@mcp.tool()
def request_g2_review(user_id: str, incentive_type: str, personalised_message: str) -> str:
    """Send a personalised G2 review request to a customer with optional incentive."""
    logger.info("request_g2_review called | user_id=%s incentive=%s", user_id, incentive_type)
    if not USE_MOCK:
        # Real API: G2 Review Generation API
        pass
    return json.dumps({
        "request_id": "G2R-8812",
        "user_id": user_id,
        "platform": "G2",
        "review_link": "https://www.g2.com/products/acme-platform/take_survey",
        "incentive_type": incentive_type,
        "incentive_value": "$25 Amazon gift card",
        "personalised_message": personalised_message,
        "sent_via": "email",
        "sent_at": datetime.utcnow().isoformat() + "Z",
        "expected_completion_rate": 0.34,
        "status": "sent"
    })


@mcp.tool()
def request_capterra_review(user_id: str, incentive_type: str, personalised_message: str) -> str:
    """Send a personalised Capterra review request to a customer with optional incentive."""
    logger.info("request_capterra_review called | user_id=%s incentive=%s", user_id, incentive_type)
    if not USE_MOCK:
        # Real API: Capterra Review Management API
        pass
    return json.dumps({
        "request_id": "CAP-6641",
        "user_id": user_id,
        "platform": "Capterra",
        "review_link": "https://reviews.capterra.com/new/acme-platform",
        "incentive_type": incentive_type,
        "incentive_value": "$25 Amazon gift card",
        "personalised_message": personalised_message,
        "sent_via": "email",
        "sent_at": datetime.utcnow().isoformat() + "Z",
        "expected_completion_rate": 0.29,
        "status": "sent"
    })


@mcp.tool()
def trigger_referral_programme(user_id: str, programme_tier: str, reward_type: str) -> str:
    """Enrol a customer in the referral programme with a specific tier and reward structure."""
    logger.info("trigger_referral_programme called | user_id=%s tier=%s", user_id, programme_tier)
    if not USE_MOCK:
        # Real API: Referral programme platform API
        pass
    return json.dumps({
        "referral_id": "REF-4421",
        "user_id": user_id,
        "programme_tier": programme_tier,
        "reward_type": reward_type,
        "referral_link": f"https://acme.io/refer/{user_id[:8]}",
        "reward_per_referral": "$100 account credit",
        "referee_discount": "20% first year",
        "max_referrals": 10,
        "enrolled_at": datetime.utcnow().isoformat() + "Z",
        "status": "active"
    })


@mcp.tool()
def invite_to_community(user_id: str, community_type: str, role: str) -> str:
    """Invite a customer to join a brand community (slack, forum, advisory_board)."""
    logger.info("invite_to_community called | user_id=%s type=%s role=%s", user_id, community_type, role)
    if not USE_MOCK:
        # Real API: Community platform integration
        pass
    return json.dumps({
        "invitation_id": "INV-7782",
        "user_id": user_id,
        "community_type": community_type,
        "role": role,
        "community_name": "Acme Customer Champions",
        "member_count": 842,
        "benefits": [
            "Early access to beta features",
            "Direct feedback channel to product team",
            "Quarterly virtual meetups",
            "Exclusive content and training"
        ],
        "invitation_link": f"https://community.acme.io/invite/{user_id[:8]}",
        "sent_at": datetime.utcnow().isoformat() + "Z",
        "status": "invited"
    })


@mcp.tool()
def request_case_study(user_id: str, topic: str, format_type: str) -> str:
    """Request a customer to participate in a case study with a specific topic and format."""
    logger.info("request_case_study called | user_id=%s topic=%s format=%s", user_id, topic, format_type)
    if not USE_MOCK:
        # Real API: Internal case study management
        pass
    return json.dumps({
        "case_study_id": "CS-1124",
        "user_id": user_id,
        "topic": topic,
        "format": format_type,
        "incentive": "Featured in annual customer report + $500 donation to charity of choice",
        "estimated_time_commitment": "2 hours (interview + review)",
        "timeline": {
            "interview_by": (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "draft_review_by": (datetime.utcnow() + timedelta(days=28)).strftime("%Y-%m-%d"),
            "publish_by": (datetime.utcnow() + timedelta(days=42)).strftime("%Y-%m-%d")
        },
        "requested_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending_approval"
    })


@mcp.tool()
def get_nps_distribution(period: str, segment: str) -> str:
    """Get NPS score distribution and trend for a period, optionally filtered by segment."""
    logger.info("get_nps_distribution called | period=%s segment=%s", period, segment)
    if not USE_MOCK:
        # Real API: NPS survey platform API
        pass
    return json.dumps({
        "period": period,
        "segment": segment,
        "responses": 1840,
        "nps_score": 62,
        "distribution": {
            "promoters": {"count": 1104, "pct": 0.60, "scores": {"9": 480, "10": 624}},
            "passives": {"count": 478, "pct": 0.26, "scores": {"7": 220, "8": 258}},
            "detractors": {"count": 258, "pct": 0.14, "scores": {"0-6": 258}}
        },
        "trend": [
            {"month": "2026-01", "nps": 55, "responses": 420},
            {"month": "2026-02", "nps": 58, "responses": 465},
            {"month": "2026-03", "nps": 60, "responses": 490},
            {"month": "2026-04", "nps": 62, "responses": 465}
        ],
        "top_themes_promoters": ["ease_of_use", "customer_support", "roi_impact"],
        "top_themes_detractors": ["onboarding_complexity", "pricing", "missing_integrations"],
        "computed_at": datetime.utcnow().isoformat() + "Z"
    })


@mcp.tool()
def get_referral_pipeline(programme_id: str, period: str) -> str:
    """Get the referral programme pipeline showing referrals by stage and conversion data."""
    logger.info("get_referral_pipeline called | programme_id=%s period=%s", programme_id, period)
    if not USE_MOCK:
        # Real API: Referral programme analytics
        pass
    return json.dumps({
        "programme_id": programme_id,
        "period": period,
        "total_referrers": 312,
        "pipeline": {
            "referrals_sent": 842,
            "links_clicked": 614,
            "signups": 287,
            "qualified_leads": 164,
            "converted_customers": 78,
            "overall_conversion_rate": 0.093
        },
        "revenue_generated": 186400.00,
        "rewards_paid": 7800.00,
        "roi": 23.9,
        "top_referrers": [
            {"user_id": "USR-3001", "name": "Emily Chen", "referrals": 14, "converted": 8, "revenue": 24000.00},
            {"user_id": "USR-3003", "name": "Priya Sharma", "referrals": 11, "converted": 6, "revenue": 18600.00},
            {"user_id": "USR-3005", "name": "Aisha Rahman", "referrals": 9, "converted": 5, "revenue": 15200.00}
        ],
        "computed_at": datetime.utcnow().isoformat() + "Z"
    })


if __name__ == "__main__":
    mcp.run()
