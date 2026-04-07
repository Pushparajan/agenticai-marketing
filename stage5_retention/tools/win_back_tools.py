# File      : win_back_tools.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Win-back sequence and competitive counter-offer tools.

Provides functions to generate multi-touch win-back sequences and
craft competitive counter-offers for at-risk customers.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
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

_MOCK_WIN_BACK_SEQUENCES: dict[str, dict[str, Any]] = {
    "CUST-001|usage_gap": {
        "customer_id": "CUST-001",
        "driver": "usage_gap",
        "sequence_name": "Re-engagement Sprint",
        "total_touches": 5,
        "duration_days": 21,
        "steps": [
            {
                "day": 1,
                "channel": "email",
                "action": "executive_outreach",
                "owner": "VP Customer Success",
                "subject": "We noticed a change — let us help",
                "message_summary": "Acknowledge usage decline. Offer dedicated support session. Express commitment to their success.",
            },
            {
                "day": 3,
                "channel": "phone",
                "action": "csm_call",
                "owner": "CSM",
                "subject": "Personalised check-in call",
                "message_summary": "Discover blockers. Offer tailored training session. Share quick-win use cases.",
            },
            {
                "day": 7,
                "channel": "in_app",
                "action": "product_training",
                "owner": "Solutions Engineer",
                "subject": "Guided product walkthrough",
                "message_summary": "Live session covering top 3 underused features relevant to their use case.",
            },
            {
                "day": 14,
                "channel": "email",
                "action": "success_story_sharing",
                "owner": "CSM",
                "subject": "How TechCorp's peers are succeeding",
                "message_summary": "Share case study from same industry with concrete ROI numbers.",
            },
            {
                "day": 21,
                "channel": "meeting",
                "action": "qbr_reset",
                "owner": "CSM + VP CS",
                "subject": "Quarterly business review — reset",
                "message_summary": "Present new success plan. Review progress from steps 1-4. Discuss renewal terms.",
            },
        ],
    },
    "CUST-002|competitor": {
        "customer_id": "CUST-002",
        "driver": "competitor",
        "sequence_name": "Competitive Defence Sequence",
        "total_touches": 4,
        "duration_days": 14,
        "steps": [
            {
                "day": 1,
                "channel": "phone",
                "action": "executive_outreach",
                "owner": "Account Executive",
                "subject": "Strategic partnership discussion",
                "message_summary": "Acknowledge competitive evaluation. Understand specific gaps. Position roadmap alignment.",
            },
            {
                "day": 3,
                "channel": "email",
                "action": "competitive_repositioning",
                "owner": "Product Marketing",
                "subject": "Side-by-side comparison: what they do not tell you",
                "message_summary": "Objective comparison highlighting switching costs, hidden fees, and our advantages.",
            },
            {
                "day": 7,
                "channel": "meeting",
                "action": "commercial_offer",
                "owner": "Account Executive",
                "subject": "Tailored renewal package",
                "message_summary": "Present commercial offer with competitive pricing and added value.",
            },
            {
                "day": 14,
                "channel": "email",
                "action": "success_story_sharing",
                "owner": "CSM",
                "subject": "Customer who switched back from Competitor X",
                "message_summary": "Share testimonial from customer who tried competitor and returned.",
            },
        ],
    },
    "CUST-003|value_gap": {
        "customer_id": "CUST-003",
        "driver": "value_gap",
        "sequence_name": "Value Realisation Programme",
        "total_touches": 4,
        "duration_days": 28,
        "steps": [
            {
                "day": 1,
                "channel": "email",
                "action": "executive_outreach",
                "owner": "CSM",
                "subject": "Let us maximise your ROI together",
                "message_summary": "Acknowledge ROI concerns. Propose value assessment workshop.",
            },
            {
                "day": 5,
                "channel": "meeting",
                "action": "product_training",
                "owner": "Solutions Engineer",
                "subject": "ROI acceleration workshop",
                "message_summary": "Hands-on session mapping their KPIs to product capabilities.",
            },
            {
                "day": 14,
                "channel": "email",
                "action": "success_story_sharing",
                "owner": "CSM",
                "subject": "How RetailMax peers achieved 3x ROI",
                "message_summary": "Industry-specific case study with step-by-step playbook.",
            },
            {
                "day": 28,
                "channel": "meeting",
                "action": "qbr_reset",
                "owner": "CSM + Manager",
                "subject": "Value checkpoint and forward plan",
                "message_summary": "Review ROI metrics post-workshop. Adjust success plan. Discuss expansion if applicable.",
            },
        ],
    },
}

_MOCK_COMPETITIVE_COUNTERS: dict[str, dict[str, Any]] = {
    "CompetitorX": {
        "competitor": "CompetitorX",
        "positioning": "Feature-rich but complex; hidden implementation costs",
        "their_strengths": ["Broader integrations", "Lower entry price"],
        "their_weaknesses": ["No dedicated CSM", "12-month lock-in", "Per-API-call billing"],
        "our_advantages": ["Dedicated CSM included", "Flat-rate pricing", "Faster time-to-value"],
        "switching_cost_estimate": 45000,
        "migration_time_weeks": 8,
        "counter_talking_points": [
            "Their per-call API pricing often exceeds our flat rate at your volume.",
            "Implementation typically takes 8 weeks — that is 2 months of lost productivity.",
            "Our dedicated CSM model delivers 40% faster issue resolution.",
        ],
        "win_back_case_study": "FinCorp switched to CompetitorX, returned after 6 months citing hidden costs and poor support.",
    },
    "CompetitorY": {
        "competitor": "CompetitorY",
        "positioning": "Low-cost alternative; limited enterprise features",
        "their_strengths": ["Lower price point", "Simple UI"],
        "their_weaknesses": ["No enterprise SSO", "Limited reporting", "No SLA guarantee"],
        "our_advantages": ["Enterprise-grade security", "Advanced analytics", "99.9% SLA"],
        "switching_cost_estimate": 25000,
        "migration_time_weeks": 6,
        "counter_talking_points": [
            "Their lack of SSO creates security compliance risk for your industry.",
            "Our advanced reporting saves teams an average of 10 hours per week.",
            "We guarantee 99.9% uptime — they offer no SLA.",
        ],
        "win_back_case_study": "HealthTech Co. evaluated CompetitorY but stayed after our compliance analysis showed gaps.",
    },
}


# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------


def _generate_sequence_real(customer_id: str, driver: str) -> dict[str, Any]:
    """Generate a win-back sequence via an internal orchestration API."""
    import httpx

    api_url = os.getenv("WINBACK_API_URL", "https://campaigns.internal/api/v1")
    api_key = os.getenv("WINBACK_API_KEY", "")
    try:
        resp = httpx.post(
            f"{api_url}/win-back/generate",
            json={"customer_id": customer_id, "driver": driver},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Win-back API error: %s — using mock", exc)
        key = f"{customer_id}|{driver}"
        return _MOCK_WIN_BACK_SEQUENCES.get(key, _default_sequence(customer_id, driver))


def _fetch_counter_offer_real(competitor: str) -> dict[str, Any]:
    """Fetch competitive intelligence from a battle-card API."""
    import httpx

    api_url = os.getenv("COMPETE_API_URL", "https://compete.internal/api/v1")
    api_key = os.getenv("COMPETE_API_KEY", "")
    try:
        resp = httpx.get(
            f"{api_url}/battle-cards/{competitor}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Compete API error: %s — using mock", exc)
        return _MOCK_COMPETITIVE_COUNTERS.get(competitor, _default_counter(competitor))


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def _default_sequence(customer_id: str, driver: str) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "driver": driver,
        "sequence_name": "Standard Re-engagement",
        "total_touches": 3,
        "duration_days": 14,
        "steps": [
            {"day": 1, "channel": "email", "action": "executive_outreach", "owner": "CSM", "subject": "We value your partnership", "message_summary": "Express concern and offer help."},
            {"day": 5, "channel": "phone", "action": "csm_call", "owner": "CSM", "subject": "Check-in call", "message_summary": "Understand specific issues and propose solutions."},
            {"day": 14, "channel": "meeting", "action": "qbr_reset", "owner": "CSM", "subject": "Strategic review", "message_summary": "Reset expectations and present renewed success plan."},
        ],
    }


def _default_counter(competitor: str) -> dict[str, Any]:
    return {
        "competitor": competitor,
        "positioning": "Unknown competitor — limited intelligence available",
        "their_strengths": ["Unknown"],
        "their_weaknesses": ["Unknown"],
        "our_advantages": ["Proven track record", "Dedicated support", "Enterprise-grade platform"],
        "switching_cost_estimate": 30000,
        "migration_time_weeks": 6,
        "counter_talking_points": [
            "Switching costs and migration time create significant business risk.",
            "Our platform has a proven track record in your industry.",
        ],
        "win_back_case_study": "No specific case study available.",
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------


def generate_win_back_sequence(customer_id: str, driver: str) -> str:
    """Generate a multi-touch win-back sequence tailored to the churn driver.

    Args:
        customer_id: Unique customer identifier.
        driver: Primary churn driver (usage_gap|value_gap|price|competitor|
                support|relationship).

    Returns:
        JSON string with sequence steps including day, channel, action,
        owner, and message summary for each touch.
    """
    logger.info("generate_win_back_sequence(%s, %s) mock=%s", customer_id, driver, USE_MOCK)

    if USE_MOCK:
        key = f"{customer_id}|{driver}"
        result = _MOCK_WIN_BACK_SEQUENCES.get(key, _default_sequence(customer_id, driver))
    else:
        result = _generate_sequence_real(customer_id, driver)

    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["sequence_id"] = str(uuid.uuid4())
    return json.dumps(result, indent=2)


def get_competitive_counter_offer(competitor: str) -> str:
    """Retrieve competitive intelligence and counter-offer strategy.

    Args:
        competitor: Name of the competitor (e.g. 'CompetitorX').

    Returns:
        JSON string with competitor analysis, switching costs,
        counter talking points, and relevant win-back case study.
    """
    logger.info("get_competitive_counter_offer(%s) mock=%s", competitor, USE_MOCK)

    if USE_MOCK:
        result = _MOCK_COMPETITIVE_COUNTERS.get(competitor, _default_counter(competitor))
    else:
        result = _fetch_counter_offer_real(competitor)

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)
