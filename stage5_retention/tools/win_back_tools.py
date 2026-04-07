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

import json, logging, os, uuid
from datetime import datetime, timezone
from typing import Any

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper to build a step dict compactly
# ---------------------------------------------------------------------------

def _step(day: int, ch: str, act: str, owner: str, subj: str, msg: str) -> dict:
    return dict(day=day, channel=ch, action=act, owner=owner,
                subject=subj, message_summary=msg)

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_SEQUENCES: dict[str, dict[str, Any]] = {
    "CUST-001|usage_gap": dict(
        customer_id="CUST-001", driver="usage_gap",
        sequence_name="Re-engagement Sprint", total_touches=5, duration_days=21,
        steps=[
            _step(1, "email", "executive_outreach", "VP Customer Success",
                  "We noticed a change — let us help",
                  "Acknowledge usage decline. Offer dedicated support session."),
            _step(3, "phone", "csm_call", "CSM",
                  "Personalised check-in call",
                  "Discover blockers. Offer tailored training. Share quick-win use cases."),
            _step(7, "in_app", "product_training", "Solutions Engineer",
                  "Guided product walkthrough",
                  "Live session covering top 3 underused features for their use case."),
            _step(14, "email", "success_story_sharing", "CSM",
                  "How TechCorp peers are succeeding",
                  "Industry case study with concrete ROI numbers."),
            _step(21, "meeting", "qbr_reset", "CSM + VP CS",
                  "Quarterly business review — reset",
                  "Present new success plan. Review progress. Discuss renewal terms."),
        ]),
    "CUST-002|competitor": dict(
        customer_id="CUST-002", driver="competitor",
        sequence_name="Competitive Defence Sequence", total_touches=4, duration_days=14,
        steps=[
            _step(1, "phone", "executive_outreach", "Account Executive",
                  "Strategic partnership discussion",
                  "Acknowledge evaluation. Understand gaps. Position roadmap alignment."),
            _step(3, "email", "competitive_repositioning", "Product Marketing",
                  "Side-by-side comparison: what they do not tell you",
                  "Objective comparison highlighting switching costs and our advantages."),
            _step(7, "meeting", "commercial_offer", "Account Executive",
                  "Tailored renewal package",
                  "Present commercial offer with competitive pricing and added value."),
            _step(14, "email", "success_story_sharing", "CSM",
                  "Customer who switched back from Competitor X",
                  "Testimonial from customer who tried competitor and returned."),
        ]),
    "CUST-003|value_gap": dict(
        customer_id="CUST-003", driver="value_gap",
        sequence_name="Value Realisation Programme", total_touches=4, duration_days=28,
        steps=[
            _step(1, "email", "executive_outreach", "CSM",
                  "Let us maximise your ROI together",
                  "Acknowledge ROI concerns. Propose value assessment workshop."),
            _step(5, "meeting", "product_training", "Solutions Engineer",
                  "ROI acceleration workshop",
                  "Hands-on session mapping their KPIs to product capabilities."),
            _step(14, "email", "success_story_sharing", "CSM",
                  "How RetailMax peers achieved 3x ROI",
                  "Industry-specific case study with step-by-step playbook."),
            _step(28, "meeting", "qbr_reset", "CSM + Manager",
                  "Value checkpoint and forward plan",
                  "Review ROI metrics post-workshop. Adjust success plan."),
        ]),
}

_COUNTERS: dict[str, dict[str, Any]] = {
    "CompetitorX": dict(competitor="CompetitorX",
        positioning="Feature-rich but complex; hidden implementation costs",
        their_strengths=["Broader integrations", "Lower entry price"],
        their_weaknesses=["No dedicated CSM", "12-month lock-in", "Per-API-call billing"],
        our_advantages=["Dedicated CSM included", "Flat-rate pricing", "Faster time-to-value"],
        switching_cost_estimate=45000, migration_time_weeks=8,
        counter_talking_points=[
            "Their per-call API pricing often exceeds our flat rate at your volume.",
            "Implementation typically takes 8 weeks — 2 months of lost productivity.",
            "Our dedicated CSM model delivers 40% faster issue resolution.",
        ],
        win_back_case_study="FinCorp switched to CompetitorX, returned after 6 months citing hidden costs."),
    "CompetitorY": dict(competitor="CompetitorY",
        positioning="Low-cost alternative; limited enterprise features",
        their_strengths=["Lower price point", "Simple UI"],
        their_weaknesses=["No enterprise SSO", "Limited reporting", "No SLA guarantee"],
        our_advantages=["Enterprise-grade security", "Advanced analytics", "99.9% SLA"],
        switching_cost_estimate=25000, migration_time_weeks=6,
        counter_talking_points=[
            "Their lack of SSO creates security compliance risk for your industry.",
            "Our advanced reporting saves teams an average of 10 hours per week.",
            "We guarantee 99.9% uptime — they offer no SLA.",
        ],
        win_back_case_study="HealthTech Co. evaluated CompetitorY but stayed after our compliance analysis."),
}

# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------

def _api_call(method: str, url_env: str, default_url: str, path: str,
              key_env: str, body: dict | None = None) -> dict[str, Any]:
    import httpx
    url = os.getenv(url_env, default_url)
    key = os.getenv(key_env, "")
    headers = {"Authorization": f"Bearer {key}"}
    if method == "POST":
        resp = httpx.post(f"{url}{path}", json=body, headers=headers, timeout=15)
    else:
        resp = httpx.get(f"{url}{path}", headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def _def_sequence(cid: str, driver: str) -> dict[str, Any]:
    return dict(customer_id=cid, driver=driver,
        sequence_name="Standard Re-engagement", total_touches=3, duration_days=14,
        steps=[
            _step(1, "email", "executive_outreach", "CSM",
                  "We value your partnership", "Express concern and offer help."),
            _step(5, "phone", "csm_call", "CSM",
                  "Check-in call", "Understand issues and propose solutions."),
            _step(14, "meeting", "qbr_reset", "CSM",
                  "Strategic review", "Reset expectations and present success plan."),
        ])

def _def_counter(comp: str) -> dict[str, Any]:
    return dict(competitor=comp,
        positioning="Unknown competitor — limited intelligence available",
        their_strengths=["Unknown"], their_weaknesses=["Unknown"],
        our_advantages=["Proven track record", "Dedicated support", "Enterprise platform"],
        switching_cost_estimate=30000, migration_time_weeks=6,
        counter_talking_points=[
            "Switching costs and migration time create significant business risk.",
            "Our platform has a proven track record in your industry.",
        ],
        win_back_case_study="No specific case study available.")

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
        JSON with sequence steps including day, channel, action, owner,
        and message summary for each touch.
    """
    logger.info("generate_win_back_sequence(%s, %s) mock=%s", customer_id, driver, USE_MOCK)
    key = f"{customer_id}|{driver}"
    if USE_MOCK:
        result = _SEQUENCES.get(key, _def_sequence(customer_id, driver))
    else:
        try:
            result = _api_call("POST", "WINBACK_API_URL",
                               "https://campaigns.internal/api/v1",
                               "/win-back/generate", "WINBACK_API_KEY",
                               {"customer_id": customer_id, "driver": driver})
        except Exception as exc:
            logger.warning("Win-back API error: %s — mock", exc)
            result = _SEQUENCES.get(key, _def_sequence(customer_id, driver))

    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["sequence_id"] = str(uuid.uuid4())
    return json.dumps(result, indent=2)


def get_competitive_counter_offer(competitor: str) -> str:
    """Retrieve competitive intelligence and counter-offer strategy.

    Args:
        competitor: Name of the competitor (e.g. 'CompetitorX').

    Returns:
        JSON with competitor analysis, switching costs, counter talking
        points, and relevant win-back case study.
    """
    logger.info("get_competitive_counter_offer(%s) mock=%s", competitor, USE_MOCK)
    if USE_MOCK:
        result = _COUNTERS.get(competitor, _def_counter(competitor))
    else:
        try:
            result = _api_call("GET", "COMPETE_API_URL",
                               "https://compete.internal/api/v1",
                               f"/battle-cards/{competitor}", "COMPETE_API_KEY")
        except Exception as exc:
            logger.warning("Compete API error: %s — mock", exc)
            result = _COUNTERS.get(competitor, _def_counter(competitor))

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)
