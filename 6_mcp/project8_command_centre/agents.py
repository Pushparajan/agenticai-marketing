# agents.py
# Project 8: Marketing Operations Command Centre (Capstone)
# Chapter Reference: Chapter 6 - MCP (Model Context Protocol)
# Description: Five LangGraph agent definitions for the command centre
# Author: Pushparajan Ramar

"""Five specialised agents for the Marketing Operations Command Centre.

    1. CampaignPlanner        -- CRM + CDP tools for campaign strategy
    2. PersonalisationEngine  -- CDP + Email tools for content tailoring
    3. PaidMediaOptimiser     -- Paid Media + Analytics for spend optimisation
    4. PerformanceAnalyst     -- Analytics + CRM for performance reporting
    5. MarketingOpsDirector   -- Human-in-the-loop gatekeeper

Environment variables: USE_MOCK (default "true"), OPENAI_API_KEY (live mode).
"""

from __future__ import annotations

import json, logging, os
from datetime import datetime, timezone
from typing import Any
from dotenv import load_dotenv
from mcp_client import call_tool, get_tools_for_servers

load_dotenv()
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
log = logging.getLogger(__name__)
_ts = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")

PROMPTS = {
    "campaign_planner": "Design data-driven campaigns using CRM pipeline + CDP audience data.",
    "personalisation_engine": "Craft personalised content using CDP profiles + email tools.",
    "paid_media_optimiser": "Analyse paid media + analytics to recommend spend changes.",
    "performance_analyst": "Combine analytics + CRM to produce performance reports.",
    "marketing_ops_director": "HITL gatekeeper: approve/reject spend-impacting actions.",
}


# =========================================================================
# Agent 1: Campaign Planner (CRM + CDP)
# =========================================================================

def campaign_planner(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Plan a campaign using CRM pipeline data and CDP segments."""
    log.info("CampaignPlanner  STARTED")
    pipeline = json.loads(call_tool("crm_get_pipeline_summary", quarter="Q3"))
    accounts = json.loads(call_tool("crm_lookup_accounts", industry="enterprise", limit=5))
    segment = json.loads(call_tool("cdp_get_segment", segment_name="enterprise_high_intent"))
    enrichment = json.loads(call_tool(
        "cdp_enrich_audience", segment_name="enterprise_high_intent",
        enrichment_type="firmographic"))

    plan = {
        "campaign_name": "Q3 Enterprise Pipeline Acceleration",
        "objective": "Generate 50 new SQLs from high-intent enterprise accounts",
        "target_segment": {
            "name": segment["segment_name"], "size": segment["profile_count"],
            "avg_engagement": segment["top_attributes"]["avg_engagement_score"],
            "enrichment_match_rate": enrichment["match_rate"],
        },
        "pipeline_context": {
            "total_pipeline": pipeline["total_pipeline"], "win_rate": pipeline["win_rate"],
            "avg_deal_size": pipeline["avg_deal_size"],
        },
        "top_accounts": [
            {"name": a["name"], "arr": a["arr"], "health_score": a["health_score"]}
            for a in accounts["accounts"][:3]],
        "channels": ["LinkedIn Ads", "Email Nurture", "Content Syndication", "Webinars"],
        "proposed_budget": 45_000,
        "success_metrics": {"target_sqls": 50, "target_pipeline_value": 2_500_000,
                            "target_roas": 4.0, "target_cpl": 250},
        "timeline": "8 weeks", "status": "PROPOSED", "planned_at": _ts(),
    }
    log.info("CampaignPlanner  COMPLETE")
    return {"campaign_plan": plan, "messages": [
        f"[CampaignPlanner] '{plan['campaign_name']}' — {plan['target_segment']['size']} "
        f"profiles, ${plan['proposed_budget']:,} budget"]}


# =========================================================================
# Agent 2: Personalisation Engine (CDP + Email)
# =========================================================================

def personalisation_engine(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Design personalised content using CDP profiles and email tools."""
    log.info("PersonalisationEngine  STARTED")
    profile = json.loads(call_tool("cdp_get_profile", email="vp@acmecorp.com"))
    campaign = json.loads(call_tool(
        "email_create_campaign", name="Q3 Enterprise — Personalised Nurture",
        segment="enterprise_high_intent",
        subject="{{first_name}}, unlock your team's pipeline potential",
        template="enterprise_nurture"))
    pers = json.loads(call_tool(
        "email_personalise_content", campaign_id=campaign["campaign_id"],
        personalisation_strategy="dynamic_content"))

    results = {
        "campaign_id": campaign["campaign_id"], "campaign_name": campaign["name"],
        "representative_profile": {
            "name": f"{profile['first_name']} {profile['last_name']}",
            "title": profile["title"], "company": profile["company"],
            "engagement_score": profile["engagement_score"],
            "content_affinity": profile["content_affinity"],
        },
        "personalisation_strategy": pers["strategy"],
        "variants_created": pers["variants_created"], "variants": pers["variants"],
        "predicted_lift": pers["predicted_lift"],
        "estimated_recipients": campaign["estimated_recipients"],
        "spend_impacting_actions": [{"action": "email_send_campaign",
            "campaign_id": campaign["campaign_id"],
            "recipients": campaign["estimated_recipients"], "requires_approval": True}],
        "personalised_at": _ts(),
    }
    log.info("PersonalisationEngine  COMPLETE  variants=%d", results["variants_created"])
    return {"personalisation_results": results, "messages": [
        f"[PersonalisationEngine] {results['variants_created']} variants, "
        f"{results['predicted_lift']:.0%} lift, {results['estimated_recipients']:,} recipients"]}


# =========================================================================
# Agent 3: Paid Media Optimiser (Paid Media + Analytics)
# =========================================================================

def paid_media_optimiser(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Optimise paid media spend using campaign data and analytics."""
    log.info("PaidMediaOptimiser  STARTED")
    campaigns = json.loads(call_tool("paid_media_get_campaigns", platform="linkedin"))
    ch = json.loads(call_tool("analytics_get_channel_performance", period="last_30_days"))
    attr = json.loads(call_tool("analytics_get_attribution", model="multi_touch", period="Q3"))

    recs: list[dict[str, Any]] = []
    for c in campaigns["campaigns"]:
        if c["roas"] >= 3.0:
            recs.append({"campaign_id": c["id"], "campaign_name": c["name"],
                "action": "INCREASE_BID", "adjustment_pct": 15.0,
                "reason": f"ROAS {c['roas']} > 3.0 — scale", "is_spend_impacting": True})
        elif c["roas"] < 2.0:
            recs.append({"campaign_id": c["id"], "campaign_name": c["name"],
                "action": "DECREASE_BID", "adjustment_pct": -25.0,
                "reason": f"ROAS {c['roas']} < 2.0 — reduce", "is_spend_impacting": True})
        else:
            recs.append({"campaign_id": c["id"], "campaign_name": c["name"],
                "action": "MAINTAIN", "adjustment_pct": 0.0,
                "reason": f"ROAS {c['roas']} in range", "is_spend_impacting": False})
    recs.append({"campaign_id": "NEW", "campaign_name": "Content Syndication Expansion",
        "action": "LAUNCH_CAMPAIGN", "platform": "linkedin", "daily_budget": 600.0,
        "targeting": "enterprise_high_intent",
        "reason": "Content syndication 4.1x ROAS — expand", "is_spend_impacting": True})

    spend_ct = sum(1 for r in recs if r.get("is_spend_impacting"))
    opt = {
        "current_campaigns": len(campaigns["campaigns"]),
        "total_spend_mtd": sum(c["spend_mtd"] for c in campaigns["campaigns"]),
        "blended_cpl": ch["blended_cpl"],
        "total_pipeline_attributed": attr["total_pipeline"],
        "recommendations": recs, "spend_impacting_count": spend_ct,
        "analysed_at": _ts(),
    }
    log.info("PaidMediaOptimiser  COMPLETE  recs=%d", len(recs))
    return {"media_optimisation": opt, "messages": [
        f"[PaidMediaOptimiser] {len(recs)} recs ({spend_ct} spend-impacting)"]}


# =========================================================================
# Agent 4: Performance Analyst (Analytics + CRM)
# =========================================================================

def performance_analyst(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Generate a performance report using analytics and CRM data."""
    log.info("PerformanceAnalyst  STARTED")
    funnel = json.loads(call_tool("analytics_get_funnel", funnel_name="lead_to_demo"))
    attr = json.loads(call_tool("analytics_get_attribution", model="multi_touch", period="Q3"))
    ch = json.loads(call_tool("analytics_get_channel_performance", period="last_30_days"))
    pipe = json.loads(call_tool("crm_get_pipeline_summary", quarter="Q3"))

    report = {
        "report_title": "Q3 Marketing Performance Report", "period": "Q3 2026",
        "executive_summary": (
            f"Pipeline ${pipe['total_pipeline']:,} | win rate {pipe['win_rate']:.0%} | "
            f"funnel {funnel['overall_conversion']:.1%} | CPL ${ch['blended_cpl']:.2f} "
            f"| {ch['total_leads']} leads | top channel {attr['channels'][0]['channel']}"),
        "funnel_metrics": {"overall_conversion": funnel["overall_conversion"],
            "top_dropoff": funnel["top_dropoff"], "steps": funnel["steps"]},
        "attribution_summary": {"total_pipeline": attr["total_pipeline"],
            "top_channel": attr["channels"][0]["channel"], "channels": attr["channels"]},
        "channel_performance": {"total_spend": ch["total_spend"],
            "total_leads": ch["total_leads"], "blended_cpl": ch["blended_cpl"],
            "best_roas_channel": max(ch["channels"].items(), key=lambda x: x[1]["roas"])[0]},
        "pipeline_health": {"total_pipeline": pipe["total_pipeline"],
            "win_rate": pipe["win_rate"], "avg_deal_size": pipe["avg_deal_size"],
            "avg_cycle_days": pipe["avg_cycle_days"]},
        "key_insights": [
            "Email nurture CPL $13 — 20x more efficient than paid",
            "SDR-to-meeting primary bottleneck (60% drop-off)",
            "LinkedIn Ads 3.8x ROAS justifies increased investment",
            "Content syndication 4.1x ROAS — under-invested"],
        "generated_at": _ts(),
    }
    log.info("PerformanceAnalyst  COMPLETE")
    return {"performance_report": report, "messages": [
        f"[PerformanceAnalyst] Q3: ${pipe['total_pipeline']:,} pipeline, "
        f"{ch['total_leads']} leads, ${ch['blended_cpl']:.2f} CPL"]}


# =========================================================================
# Agent 5: Marketing Ops Director (HITL Gatekeeper)
# =========================================================================

def marketing_ops_director(state: dict[str, Any], llm: Any = None) -> dict[str, Any]:
    """Review all agent outputs and approve/reject spend-impacting actions."""
    log.info("MarketingOpsDirector  STARTED")
    plan = state.get("campaign_plan", {})
    pers = state.get("personalisation_results", {})
    media = state.get("media_optimisation", {})
    actions: list[dict[str, Any]] = []

    for act in pers.get("spend_impacting_actions", []):
        actions.append({"source": "PersonalisationEngine", "type": act["action"],
            "details": f"Send {act['campaign_id']} to {act['recipients']:,} recipients",
            "decision": "APPROVED",
            "rationale": "18% lift; well-qualified enterprise segment",
            "conditions": ["Schedule Tuesday 14:00 UTC", "Enable throttling"]})

    for rec in media.get("recommendations", []):
        if not rec.get("is_spend_impacting"):
            continue
        if rec["action"] in ("INCREASE_BID", "DECREASE_BID"):
            actions.append({"source": "PaidMediaOptimiser", "type": "bid_adjustment",
                "details": f"{rec['campaign_name']}: {rec['adjustment_pct']:+.0f}%",
                "decision": "APPROVED", "rationale": rec["reason"],
                "conditions": ["Review after 72 hours"]})
        elif rec["action"] == "LAUNCH_CAMPAIGN":
            actions.append({"source": "PaidMediaOptimiser", "type": "campaign_launch",
                "details": f"New: {rec['campaign_name']} ${rec['daily_budget']}/day",
                "decision": "APPROVED_WITH_CONDITIONS", "rationale": rec["reason"],
                "conditions": ["50% budget 1-week pilot", "Auto-pause if CPA > $400"]})

    plan_review = {
        "campaign_name": plan.get("campaign_name", "N/A"), "decision": "APPROVED",
        "rationale": f"Pipeline ${plan.get('pipeline_context',{}).get('total_pipeline',0):,} "
                     f"aligns with {plan.get('target_segment',{}).get('size',0):,} profiles",
        "modifications": ["Add webinar touchpoint", "ABM tier for top 10 accounts"],
    }
    a_ct = sum(1 for a in actions if "APPROVED" in a["decision"])
    c_ct = sum(1 for a in actions if a["decision"] == "APPROVED_WITH_CONDITIONS")
    r_ct = sum(1 for a in actions if a["decision"] == "REJECTED")

    approval = {
        "reviewer": "Marketing Ops Director", "review_timestamp": _ts(),
        "campaign_plan_review": plan_review,
        "spend_impacting_decisions": actions,
        "total_actions_reviewed": len(actions),
        "approved_count": a_ct, "rejected_count": r_ct, "conditional_count": c_ct,
        "overall_status": "APPROVED_WITH_CONDITIONS",
        "director_notes": "Strong Q3 proposal. LinkedIn Ads and content syndication "
            "investment justified. Email personalisation sound. Pilot new launches. "
            "Weekly review cadence for first 3 weeks.",
    }
    log.info("MarketingOpsDirector  COMPLETE  approved=%d conditional=%d", a_ct, c_ct)
    return {"director_approval": approval, "messages": [
        f"[MarketingOpsDirector] {len(actions)} actions: {a_ct} approved, "
        f"{c_ct} conditional, {r_ct} rejected — {approval['overall_status']}"]}


# =========================================================================
# Agent registry
# =========================================================================

AGENT_REGISTRY: dict[str, dict[str, Any]] = {
    "campaign_planner": {"fn": campaign_planner,
        "servers": ["crm_server", "cdp_server"], "prompt": PROMPTS["campaign_planner"]},
    "personalisation_engine": {"fn": personalisation_engine,
        "servers": ["cdp_server", "email_server"], "prompt": PROMPTS["personalisation_engine"]},
    "paid_media_optimiser": {"fn": paid_media_optimiser,
        "servers": ["paid_media_server", "analytics_server"], "prompt": PROMPTS["paid_media_optimiser"]},
    "performance_analyst": {"fn": performance_analyst,
        "servers": ["analytics_server", "crm_server"], "prompt": PROMPTS["performance_analyst"]},
    "marketing_ops_director": {"fn": marketing_ops_director,
        "servers": [], "prompt": PROMPTS["marketing_ops_director"]},
}

if __name__ == "__main__":
    print("=" * 70)
    print("  Command Centre — Agent Registry")
    print("=" * 70)
    for name, info in AGENT_REGISTRY.items():
        print(f"  [{name}]  servers={info['servers'] or ['(reviewer)']}")
    print("\n--- Smoke Test: CampaignPlanner ---")
    r = campaign_planner({"brief": "Launch Q3 enterprise pipeline campaign"})
    print(json.dumps(r["campaign_plan"], indent=2)[:500], "\n...")
