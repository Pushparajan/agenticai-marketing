# agents.py
# Project 8: Marketing Operations Command Centre (Capstone)
# Chapter Reference: Chapter 6 - MCP (Model Context Protocol)
# Description: Five LangGraph agent definitions for the command centre
# Author: Pushparajan Ramar

"""LangGraph agent definitions for the Marketing Operations Command Centre.

Defines five specialised agents that collaborate via the orchestrator:

    1. **CampaignPlanner**        -- CRM + CDP tools for campaign strategy
    2. **PersonalisationEngine**  -- CDP + Email tools for content tailoring
    3. **PaidMediaOptimiser**     -- Paid Media + Analytics for spend optimisation
    4. **PerformanceAnalyst**     -- Analytics + CRM for performance reporting
    5. **MarketingOpsDirector**   -- Human-in-the-loop gatekeeper

Each agent is a pure function that receives the current graph state and an
optional LLM client, executes its domain logic using MCP tool wrappers,
and returns a structured result dict.

Environment variables consumed (via .env):
    USE_MOCK       -- "true" (default) bypasses LLM calls with deterministic output
    OPENAI_API_KEY -- Required when USE_MOCK is "false"
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from mcp_client import (
    call_tool,
    get_tools_for_servers,
    is_spend_impacting,
    SPEND_IMPACTING_TOOLS,
)

load_dotenv()

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# System prompts for each agent role
# ---------------------------------------------------------------------------

CAMPAIGN_PLANNER_PROMPT = """\
You are the Campaign Planner agent. Your responsibility is to design data-driven
campaign strategies by combining CRM pipeline intelligence with CDP audience
insights. You identify target segments, set campaign objectives, allocate
preliminary budgets, and define success metrics. Always ground your plans in
the data returned by your CRM and CDP tools."""

PERSONALISATION_ENGINE_PROMPT = """\
You are the Personalisation Engine agent. You craft hyper-personalised content
strategies by combining CDP behavioural profiles with email marketing
capabilities. You create audience-specific messaging variants, select optimal
send times, and design dynamic content blocks. Every recommendation must be
backed by audience data."""

PAID_MEDIA_OPTIMISER_PROMPT = """\
You are the Paid Media Optimiser agent. You analyse current paid media
performance alongside marketing analytics to recommend bid adjustments,
budget re-allocations, and new campaign launches. Flag any spend-impacting
actions clearly so the director can approve them."""

PERFORMANCE_ANALYST_PROMPT = """\
You are the Performance Analyst agent. You provide comprehensive performance
reporting by combining marketing analytics (funnels, attribution, channel
metrics) with CRM pipeline data. You identify trends, calculate ROI, and
surface actionable insights for the leadership team."""

MARKETING_OPS_DIRECTOR_PROMPT = """\
You are the Marketing Operations Director, the human-in-the-loop gatekeeper.
You review the outputs of all four specialist agents, validate strategic
alignment, and decide whether to approve, modify, or reject each
recommendation. You must explicitly approve or reject any spend-impacting
actions (bid changes, campaign launches, bulk email sends). Provide a clear
rationale for every decision."""


# =========================================================================
# Agent 1: Campaign Planner (CRM + CDP)
# =========================================================================

def campaign_planner(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Plan a marketing campaign using CRM pipeline data and CDP segments.

    Args:
        state: The shared ``CommandCentreState``.
        llm:   Optional LLM client (unused in mock mode).

    Returns:
        Dict with ``campaign_plan`` key containing the structured plan.
    """
    log.info("CampaignPlanner  STARTED  brief=%s", state.get("brief", "N/A"))
    tools = get_tools_for_servers("crm_server", "cdp_server")
    log.info("CampaignPlanner  tools available: %s", list(tools.keys()))

    # Step 1 — Gather CRM pipeline intelligence
    pipeline_raw = call_tool("crm_get_pipeline_summary", quarter="Q3")
    pipeline = json.loads(pipeline_raw)

    # Step 2 — Identify target accounts
    accounts_raw = call_tool("crm_lookup_accounts", industry="enterprise", limit=5)
    accounts = json.loads(accounts_raw)

    # Step 3 — Pull CDP audience segment
    segment_raw = call_tool("cdp_get_segment", segment_name="enterprise_high_intent")
    segment = json.loads(segment_raw)

    # Step 4 — Enrich audience with firmographic data
    enrichment_raw = call_tool(
        "cdp_enrich_audience",
        segment_name="enterprise_high_intent",
        enrichment_type="firmographic",
    )
    enrichment = json.loads(enrichment_raw)

    # Step 5 — Synthesise campaign plan
    plan = {
        "campaign_name": f"Q3 Enterprise Pipeline Acceleration",
        "objective": "Generate 50 new SQLs from high-intent enterprise accounts",
        "target_segment": {
            "name": segment["segment_name"],
            "size": segment["profile_count"],
            "avg_engagement": segment["top_attributes"]["avg_engagement_score"],
            "enrichment_match_rate": enrichment["match_rate"],
        },
        "pipeline_context": {
            "total_pipeline": pipeline["total_pipeline"],
            "win_rate": pipeline["win_rate"],
            "avg_deal_size": pipeline["avg_deal_size"],
            "avg_cycle_days": pipeline["avg_cycle_days"],
        },
        "top_accounts": [
            {"name": a["name"], "arr": a["arr"], "health_score": a["health_score"]}
            for a in accounts["accounts"][:3]
        ],
        "channels": ["LinkedIn Ads", "Email Nurture", "Content Syndication", "Webinars"],
        "proposed_budget": 45_000,
        "success_metrics": {
            "target_sqls": 50,
            "target_pipeline_value": 2_500_000,
            "target_roas": 4.0,
            "target_cpl": 250,
        },
        "timeline": "8 weeks",
        "status": "PROPOSED",
        "planned_at": _ts(),
    }

    log.info("CampaignPlanner  COMPLETE  campaign=%s", plan["campaign_name"])
    return {
        "campaign_plan": plan,
        "messages": [f"[CampaignPlanner] Proposed '{plan['campaign_name']}' "
                     f"targeting {plan['target_segment']['size']} profiles "
                     f"with ${plan['proposed_budget']:,} budget"],
    }


# =========================================================================
# Agent 2: Personalisation Engine (CDP + Email)
# =========================================================================

def personalisation_engine(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Design personalised content using CDP profiles and email tools.

    Args:
        state: The shared ``CommandCentreState``.
        llm:   Optional LLM client.

    Returns:
        Dict with ``personalisation_results`` key.
    """
    log.info("PersonalisationEngine  STARTED")
    tools = get_tools_for_servers("cdp_server", "email_server")
    log.info("PersonalisationEngine  tools available: %s", list(tools.keys()))

    # Step 1 — Get representative profile for personalisation
    profile_raw = call_tool("cdp_get_profile", email="vp@acmecorp.com")
    profile = json.loads(profile_raw)

    # Step 2 — Create email campaign draft
    campaign_raw = call_tool(
        "email_create_campaign",
        name="Q3 Enterprise Pipeline — Personalised Nurture",
        segment="enterprise_high_intent",
        subject="{{first_name}}, unlock your team's pipeline potential",
        template="enterprise_nurture",
    )
    campaign = json.loads(campaign_raw)

    # Step 3 — Apply personalisation strategy
    personalised_raw = call_tool(
        "email_personalise_content",
        campaign_id=campaign["campaign_id"],
        personalisation_strategy="dynamic_content",
    )
    personalised = json.loads(personalised_raw)

    # Step 4 — Build the result
    results = {
        "campaign_id": campaign["campaign_id"],
        "campaign_name": campaign["name"],
        "representative_profile": {
            "name": f"{profile['first_name']} {profile['last_name']}",
            "title": profile["title"],
            "company": profile["company"],
            "engagement_score": profile["engagement_score"],
            "content_affinity": profile["content_affinity"],
            "preferred_channel": profile["preferred_channel"],
        },
        "personalisation_strategy": personalised["strategy"],
        "variants_created": personalised["variants_created"],
        "variants": personalised["variants"],
        "predicted_lift": personalised["predicted_lift"],
        "estimated_recipients": campaign["estimated_recipients"],
        "spend_impacting_actions": [
            {
                "action": "email_send_campaign",
                "campaign_id": campaign["campaign_id"],
                "recipients": campaign["estimated_recipients"],
                "requires_approval": True,
            }
        ],
        "personalised_at": _ts(),
    }

    log.info("PersonalisationEngine  COMPLETE  variants=%d  lift=%.0f%%",
             results["variants_created"], results["predicted_lift"] * 100)
    return {
        "personalisation_results": results,
        "messages": [f"[PersonalisationEngine] Created {results['variants_created']} "
                     f"personalised variants with {results['predicted_lift']:.0%} "
                     f"predicted lift for {results['estimated_recipients']:,} recipients"],
    }


# =========================================================================
# Agent 3: Paid Media Optimiser (Paid Media + Analytics)
# =========================================================================

def paid_media_optimiser(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Optimise paid media spend using campaign data and analytics.

    Args:
        state: The shared ``CommandCentreState``.
        llm:   Optional LLM client.

    Returns:
        Dict with ``media_optimisation`` key.
    """
    log.info("PaidMediaOptimiser  STARTED")
    tools = get_tools_for_servers("paid_media_server", "analytics_server")
    log.info("PaidMediaOptimiser  tools available: %s", list(tools.keys()))

    # Step 1 — Retrieve current paid media campaigns
    campaigns_raw = call_tool("paid_media_get_campaigns", platform="linkedin")
    campaigns = json.loads(campaigns_raw)

    # Step 2 — Get channel performance for context
    channel_raw = call_tool("analytics_get_channel_performance", period="last_30_days")
    channel_perf = json.loads(channel_raw)

    # Step 3 — Get attribution data
    attribution_raw = call_tool("analytics_get_attribution", model="multi_touch", period="Q3")
    attribution = json.loads(attribution_raw)

    # Step 4 — Analyse and produce recommendations
    recommendations: list[dict[str, Any]] = []
    for camp in campaigns["campaigns"]:
        if camp["roas"] >= 3.0:
            recommendations.append({
                "campaign_id": camp["id"],
                "campaign_name": camp["name"],
                "action": "INCREASE_BID",
                "adjustment_pct": 15.0,
                "reason": f"ROAS of {camp['roas']} exceeds 3.0 threshold — scale winner",
                "is_spend_impacting": True,
            })
        elif camp["roas"] < 2.0:
            recommendations.append({
                "campaign_id": camp["id"],
                "campaign_name": camp["name"],
                "action": "DECREASE_BID",
                "adjustment_pct": -25.0,
                "reason": f"ROAS of {camp['roas']} below 2.0 — reduce waste",
                "is_spend_impacting": True,
            })
        else:
            recommendations.append({
                "campaign_id": camp["id"],
                "campaign_name": camp["name"],
                "action": "MAINTAIN",
                "adjustment_pct": 0.0,
                "reason": f"ROAS of {camp['roas']} within acceptable range",
                "is_spend_impacting": False,
            })

    # New campaign recommendation based on attribution gaps
    recommendations.append({
        "campaign_id": "NEW",
        "campaign_name": "Content Syndication Expansion",
        "action": "LAUNCH_CAMPAIGN",
        "platform": "linkedin",
        "daily_budget": 600.0,
        "targeting": "enterprise_high_intent",
        "reason": "Content syndication shows 4.1x ROAS — expand presence",
        "is_spend_impacting": True,
    })

    optimisation = {
        "current_campaigns": len(campaigns["campaigns"]),
        "total_spend_mtd": sum(c["spend_mtd"] for c in campaigns["campaigns"]),
        "blended_cpl": channel_perf["blended_cpl"],
        "total_pipeline_attributed": attribution["total_pipeline"],
        "recommendations": recommendations,
        "spend_impacting_count": sum(1 for r in recommendations if r.get("is_spend_impacting")),
        "analysed_at": _ts(),
    }

    log.info("PaidMediaOptimiser  COMPLETE  recs=%d  spend_impacting=%d",
             len(recommendations), optimisation["spend_impacting_count"])
    return {
        "media_optimisation": optimisation,
        "messages": [f"[PaidMediaOptimiser] {len(recommendations)} recommendations "
                     f"({optimisation['spend_impacting_count']} spend-impacting) "
                     f"across {optimisation['current_campaigns']} campaigns"],
    }


# =========================================================================
# Agent 4: Performance Analyst (Analytics + CRM)
# =========================================================================

def performance_analyst(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Generate a performance report using analytics and CRM data.

    Args:
        state: The shared ``CommandCentreState``.
        llm:   Optional LLM client.

    Returns:
        Dict with ``performance_report`` key.
    """
    log.info("PerformanceAnalyst  STARTED")
    tools = get_tools_for_servers("analytics_server", "crm_server")
    log.info("PerformanceAnalyst  tools available: %s", list(tools.keys()))

    # Step 1 — Funnel metrics
    funnel_raw = call_tool("analytics_get_funnel", funnel_name="lead_to_demo")
    funnel = json.loads(funnel_raw)

    # Step 2 — Attribution report
    attribution_raw = call_tool("analytics_get_attribution", model="multi_touch", period="Q3")
    attribution = json.loads(attribution_raw)

    # Step 3 — Channel performance
    channel_raw = call_tool("analytics_get_channel_performance", period="last_30_days")
    channel_perf = json.loads(channel_raw)

    # Step 4 — Pipeline context from CRM
    pipeline_raw = call_tool("crm_get_pipeline_summary", quarter="Q3")
    pipeline = json.loads(pipeline_raw)

    # Step 5 — Synthesise report
    report = {
        "report_title": "Q3 Marketing Performance Report",
        "period": "Q3 2026",
        "executive_summary": (
            f"Total pipeline stands at ${pipeline['total_pipeline']:,} with a "
            f"{pipeline['win_rate']:.0%} win rate. The lead-to-demo funnel converts "
            f"at {funnel['overall_conversion']:.1%} overall. Blended CPL is "
            f"${channel_perf['blended_cpl']:.2f} across {channel_perf['total_leads']} "
            f"leads generated. LinkedIn Ads drives the largest attributed pipeline "
            f"share at {attribution['channels'][0]['pct_of_total']:.0%}."
        ),
        "funnel_metrics": {
            "overall_conversion": funnel["overall_conversion"],
            "top_dropoff": funnel["top_dropoff"],
            "steps": funnel["steps"],
        },
        "attribution_summary": {
            "total_attributed_pipeline": attribution["total_pipeline"],
            "top_channel": attribution["channels"][0]["channel"],
            "top_channel_share": attribution["channels"][0]["pct_of_total"],
            "channels": attribution["channels"],
        },
        "channel_performance": {
            "total_spend": channel_perf["total_spend"],
            "total_leads": channel_perf["total_leads"],
            "blended_cpl": channel_perf["blended_cpl"],
            "best_roas_channel": max(
                channel_perf["channels"].items(), key=lambda x: x[1]["roas"]
            )[0],
        },
        "pipeline_health": {
            "total_pipeline": pipeline["total_pipeline"],
            "win_rate": pipeline["win_rate"],
            "avg_deal_size": pipeline["avg_deal_size"],
            "avg_cycle_days": pipeline["avg_cycle_days"],
        },
        "key_insights": [
            "Email nurture delivers the lowest CPL ($13) — 20x more efficient than paid channels",
            "SDR-to-meeting conversion is the primary funnel bottleneck (60% drop-off)",
            "LinkedIn Ads ROAS of 3.8x justifies increased investment",
            "Content syndication at 4.1x ROAS is an under-invested high-performer",
        ],
        "recommendations": [
            "Increase LinkedIn Ads budget by 15% to capitalise on strong ROAS",
            "Implement SDR response-time SLA to address meeting-booking drop-off",
            "Launch content syndication expansion campaign",
            "Scale email nurture program — highest efficiency channel",
        ],
        "generated_at": _ts(),
    }

    log.info("PerformanceAnalyst  COMPLETE  pipeline=$%s  leads=%d",
             f"{pipeline['total_pipeline']:,}", channel_perf["total_leads"])
    return {
        "performance_report": report,
        "messages": [f"[PerformanceAnalyst] Generated Q3 report: "
                     f"${pipeline['total_pipeline']:,} pipeline, "
                     f"{channel_perf['total_leads']} leads, "
                     f"${channel_perf['blended_cpl']:.2f} blended CPL"],
    }


# =========================================================================
# Agent 5: Marketing Ops Director (HITL Gatekeeper)
# =========================================================================

def marketing_ops_director(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Review all agent outputs and approve/reject spend-impacting actions.

    The director acts as the human-in-the-loop gate, ensuring strategic
    alignment and budget governance before any spend-impacting action
    is executed.

    Args:
        state: The shared ``CommandCentreState`` with all agent results.
        llm:   Optional LLM client.

    Returns:
        Dict with ``director_approval`` key containing decisions.
    """
    log.info("MarketingOpsDirector  STARTED  reviewing all agent outputs")

    campaign_plan = state.get("campaign_plan", {})
    personalisation = state.get("personalisation_results", {})
    media_opt = state.get("media_optimisation", {})
    perf_report = state.get("performance_report", {})

    # --- Review spend-impacting actions across all agents ---
    spend_actions: list[dict[str, Any]] = []

    # From personalisation: bulk email send
    for action in personalisation.get("spend_impacting_actions", []):
        spend_actions.append({
            "source_agent": "PersonalisationEngine",
            "action_type": action["action"],
            "details": f"Send campaign {action['campaign_id']} "
                       f"to {action['recipients']:,} recipients",
            "decision": "APPROVED",
            "rationale": "Personalised variants show 18% predicted lift; "
                         "segment is well-qualified enterprise audience",
            "conditions": ["Schedule for Tuesday 14:00 UTC (optimal send window)",
                           "Enable engagement-based throttling"],
        })

    # From media optimiser: bid adjustments and new campaigns
    for rec in media_opt.get("recommendations", []):
        if rec.get("is_spend_impacting"):
            if rec["action"] == "INCREASE_BID":
                spend_actions.append({
                    "source_agent": "PaidMediaOptimiser",
                    "action_type": "bid_adjustment",
                    "details": f"{rec['campaign_name']}: +{rec['adjustment_pct']}% bid",
                    "decision": "APPROVED",
                    "rationale": rec["reason"],
                    "conditions": ["Cap daily budget increase at $150",
                                   "Review after 72 hours"],
                })
            elif rec["action"] == "DECREASE_BID":
                spend_actions.append({
                    "source_agent": "PaidMediaOptimiser",
                    "action_type": "bid_adjustment",
                    "details": f"{rec['campaign_name']}: {rec['adjustment_pct']}% bid",
                    "decision": "APPROVED",
                    "rationale": rec["reason"],
                    "conditions": ["Monitor for 48 hours before further reduction"],
                })
            elif rec["action"] == "LAUNCH_CAMPAIGN":
                spend_actions.append({
                    "source_agent": "PaidMediaOptimiser",
                    "action_type": "campaign_launch",
                    "details": f"New campaign: {rec['campaign_name']} "
                               f"at ${rec['daily_budget']}/day on {rec['platform']}",
                    "decision": "APPROVED_WITH_CONDITIONS",
                    "rationale": rec["reason"],
                    "conditions": ["Start with 50% of proposed budget for 1-week pilot",
                                   "Set automated pause if CPA exceeds $400",
                                   "Report back in 7 days with performance data"],
                })

    # --- Overall campaign plan review ---
    plan_review = {
        "campaign_name": campaign_plan.get("campaign_name", "N/A"),
        "decision": "APPROVED",
        "rationale": (
            f"Strong alignment between pipeline data "
            f"(${campaign_plan.get('pipeline_context', {}).get('total_pipeline', 0):,}) "
            f"and target segment ({campaign_plan.get('target_segment', {}).get('size', 0):,} "
            f"profiles). Budget of ${campaign_plan.get('proposed_budget', 0):,} is "
            f"proportionate to target of {campaign_plan.get('success_metrics', {}).get('target_sqls', 0)} SQLs."
        ),
        "modifications": [
            "Add webinar series as fourth channel touchpoint",
            "Include ABM tier for top 10 accounts with personalised outreach",
        ],
    }

    # --- Compile director approval ---
    approval = {
        "reviewer": "Marketing Ops Director",
        "review_timestamp": _ts(),
        "campaign_plan_review": plan_review,
        "spend_impacting_decisions": spend_actions,
        "total_actions_reviewed": len(spend_actions),
        "approved_count": sum(1 for a in spend_actions if "APPROVED" in a["decision"]),
        "rejected_count": sum(1 for a in spend_actions if a["decision"] == "REJECTED"),
        "conditional_count": sum(
            1 for a in spend_actions if a["decision"] == "APPROVED_WITH_CONDITIONS"
        ),
        "overall_status": "APPROVED_WITH_CONDITIONS",
        "director_notes": (
            "Strong Q3 campaign proposal. The data supports increased investment in "
            "LinkedIn Ads and content syndication. Email personalisation strategy is "
            "sound. Recommend pilot approach for new campaign launches. All existing "
            "bid adjustments are well-justified by ROAS data. Schedule weekly review "
            "cadence for the first 3 weeks."
        ),
    }

    approved = approval["approved_count"]
    conditional = approval["conditional_count"]
    total = approval["total_actions_reviewed"]

    log.info("MarketingOpsDirector  COMPLETE  approved=%d  conditional=%d  total=%d",
             approved, conditional, total)
    return {
        "director_approval": approval,
        "messages": [
            f"[MarketingOpsDirector] Reviewed {total} spend-impacting actions: "
            f"{approved} approved, {conditional} conditional, "
            f"{approval['rejected_count']} rejected. "
            f"Overall: {approval['overall_status']}"
        ],
    }


# =========================================================================
# Agent registry for the orchestrator
# =========================================================================

AGENT_REGISTRY: dict[str, dict[str, Any]] = {
    "campaign_planner": {
        "fn": campaign_planner,
        "servers": ["crm_server", "cdp_server"],
        "prompt": CAMPAIGN_PLANNER_PROMPT,
        "description": "Plans campaigns using CRM + CDP data",
    },
    "personalisation_engine": {
        "fn": personalisation_engine,
        "servers": ["cdp_server", "email_server"],
        "prompt": PERSONALISATION_ENGINE_PROMPT,
        "description": "Personalises content using CDP + Email tools",
    },
    "paid_media_optimiser": {
        "fn": paid_media_optimiser,
        "servers": ["paid_media_server", "analytics_server"],
        "prompt": PAID_MEDIA_OPTIMISER_PROMPT,
        "description": "Optimises paid media spend using analytics",
    },
    "performance_analyst": {
        "fn": performance_analyst,
        "servers": ["analytics_server", "crm_server"],
        "prompt": PERFORMANCE_ANALYST_PROMPT,
        "description": "Analyses marketing performance across channels",
    },
    "marketing_ops_director": {
        "fn": marketing_ops_director,
        "servers": [],
        "prompt": MARKETING_OPS_DIRECTOR_PROMPT,
        "description": "HITL gatekeeper — reviews and approves actions",
    },
}


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  Marketing Operations Command Centre — Agent Registry")
    print("=" * 70)
    print(f"\n  USE_MOCK = {USE_MOCK}")
    print(f"  Agents registered: {len(AGENT_REGISTRY)}\n")

    for name, info in AGENT_REGISTRY.items():
        print(f"  [{name}]")
        print(f"    Servers : {', '.join(info['servers']) or 'none (reviewer)'}")
        print(f"    Purpose : {info['description']}")
    print()

    # Quick smoke test — run campaign planner
    print("--- Smoke Test: CampaignPlanner ---")
    demo_state: dict[str, Any] = {"brief": "Launch Q3 enterprise pipeline campaign"}
    result = campaign_planner(demo_state)
    print(json.dumps(result["campaign_plan"], indent=2)[:600])
    print("...")
