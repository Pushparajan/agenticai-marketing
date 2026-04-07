# orchestrator.py
# Project 8: Marketing Operations Command Centre (Capstone)
# Chapter Reference: Chapter 6 - MCP (Model Context Protocol)
# Description: LangGraph parallel multi-agent orchestrator with HITL gate
# Author: Pushparajan Ramar

"""LangGraph orchestrator for the Marketing Operations Command Centre.

Graph topology::

    START
      +----> campaign_planner --------+
      +----> personalisation_engine --+-> merge_results -> director_review -> generate_report -> END
      +----> paid_media_optimiser ----+          ^
      +----> performance_analyst -----+    (interrupt_before)

Features: parallel fan-out, merge barrier, HITL interrupt, MemorySaver.
Environment variables: USE_MOCK (default "true").
"""

from __future__ import annotations

import json, logging, os
from datetime import datetime, timezone
from typing import Annotated, Any
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict
from agents import (campaign_planner, marketing_ops_director,
    paid_media_optimiser, performance_analyst, personalisation_engine)

load_dotenv()
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
log = logging.getLogger(__name__)
_ts = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _merge_messages(left: list[str], right: list[str]) -> list[str]:
    """Reducer: append new messages to existing list."""
    return left + right


class CommandCentreState(TypedDict, total=False):
    """Shared state for the Command Centre graph.

    Attributes:
        brief:                   Campaign brief / mission statement.
        campaign_plan:           CampaignPlanner output.
        personalisation_results: PersonalisationEngine output.
        media_optimisation:      PaidMediaOptimiser output.
        performance_report:      PerformanceAnalyst output.
        director_approval:       MarketingOpsDirector output.
        execution_report:        Final consolidated report.
        messages:                Chronological agent action log.
    """
    brief: str
    campaign_plan: dict[str, Any]
    personalisation_results: dict[str, Any]
    media_optimisation: dict[str, Any]
    performance_report: dict[str, Any]
    director_approval: dict[str, Any]
    execution_report: dict[str, Any]
    messages: Annotated[list[str], _merge_messages]


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def _node_campaign_planner(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for CampaignPlanner."""
    return campaign_planner(state)

def _node_personalisation_engine(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for PersonalisationEngine."""
    return personalisation_engine(state)

def _node_paid_media_optimiser(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for PaidMediaOptimiser."""
    return paid_media_optimiser(state)

def _node_performance_analyst(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for PerformanceAnalyst."""
    return performance_analyst(state)

def _node_merge_results(state: CommandCentreState) -> dict[str, Any]:
    """Synchronisation barrier — collects parallel outputs for review."""
    log.info("MergeResults  syncing 4 parallel agents")
    parts = []
    if state.get("campaign_plan"):
        parts.append(f"Campaign: {state['campaign_plan'].get('campaign_name','?')}")
    if state.get("personalisation_results"):
        parts.append(f"Variants: {state['personalisation_results'].get('variants_created',0)}")
    if state.get("media_optimisation"):
        parts.append(f"Media recs: {len(state['media_optimisation'].get('recommendations',[]))}")
    if state.get("performance_report"):
        parts.append(f"Report: {state['performance_report'].get('report_title','?')}")
    return {"messages": [f"[MergeResults] Synced: {' | '.join(parts)}"]}

def _node_director_review(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for MarketingOpsDirector (HITL gatekeeper)."""
    return marketing_ops_director(state)

def _node_generate_report(state: CommandCentreState) -> dict[str, Any]:
    """Generate the final consolidated execution report."""
    log.info("GenerateReport  compiling")
    plan = state.get("campaign_plan", {})
    pers = state.get("personalisation_results", {})
    media = state.get("media_optimisation", {})
    perf = state.get("performance_report", {})
    appr = state.get("director_approval", {})
    decisions = appr.get("spend_impacting_decisions", [])

    report = {
        "title": "Marketing Operations Command Centre — Execution Report",
        "generated_at": _ts(), "brief": state.get("brief", "N/A"),
        "sections": {
            "campaign_strategy": {
                "campaign_name": plan.get("campaign_name", "N/A"),
                "target_segment_size": plan.get("target_segment", {}).get("size", 0),
                "proposed_budget": plan.get("proposed_budget", 0),
                "channels": plan.get("channels", []),
                "timeline": plan.get("timeline", "N/A"),
                "success_metrics": plan.get("success_metrics", {}),
                "director_decision": appr.get("campaign_plan_review", {}).get("decision", "PENDING"),
            },
            "personalisation": {
                "campaign_id": pers.get("campaign_id", "N/A"),
                "variants_created": pers.get("variants_created", 0),
                "predicted_lift": pers.get("predicted_lift", 0),
                "estimated_recipients": pers.get("estimated_recipients", 0),
                "strategy": pers.get("personalisation_strategy", "N/A"),
            },
            "paid_media": {
                "campaigns_analysed": media.get("current_campaigns", 0),
                "total_spend_mtd": media.get("total_spend_mtd", 0),
                "recommendations_count": len(media.get("recommendations", [])),
                "spend_impacting_count": media.get("spend_impacting_count", 0),
                "recommendations": [{"campaign": r.get("campaign_name", "N/A"),
                    "action": r.get("action", "N/A"), "adjustment": r.get("adjustment_pct", 0)}
                    for r in media.get("recommendations", [])],
            },
            "performance": {
                "total_pipeline": perf.get("pipeline_health", {}).get("total_pipeline", 0),
                "win_rate": perf.get("pipeline_health", {}).get("win_rate", 0),
                "blended_cpl": perf.get("channel_performance", {}).get("blended_cpl", 0),
                "total_leads": perf.get("channel_performance", {}).get("total_leads", 0),
                "key_insights": perf.get("key_insights", []),
            },
            "director_approval": {
                "overall_status": appr.get("overall_status", "PENDING"),
                "total_actions_reviewed": appr.get("total_actions_reviewed", 0),
                "approved": sum(1 for d in decisions if "APPROVED" in d.get("decision", "")),
                "rejected": sum(1 for d in decisions if d.get("decision") == "REJECTED"),
                "director_notes": appr.get("director_notes", ""),
            },
        },
        "execution_log": state.get("messages", []),
    }
    log.info("GenerateReport  COMPLETE  status=%s", appr.get("overall_status", "PENDING"))
    return {"execution_report": report, "messages": [
        f"[GenerateReport] Report compiled — {appr.get('overall_status','PENDING')}"]}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_command_centre_graph(enable_hitl: bool = True) -> Any:
    """Construct and compile the Command Centre orchestrator graph.

    Args:
        enable_hitl: Insert interrupt before director_review if True.

    Returns:
        Compiled LangGraph StateGraph with MemorySaver checkpointer.
    """
    b = StateGraph(CommandCentreState)
    b.add_node("campaign_planner", _node_campaign_planner)
    b.add_node("personalisation_engine", _node_personalisation_engine)
    b.add_node("paid_media_optimiser", _node_paid_media_optimiser)
    b.add_node("performance_analyst", _node_performance_analyst)
    b.add_node("merge_results", _node_merge_results)
    b.add_node("director_review", _node_director_review)
    b.add_node("generate_report", _node_generate_report)

    # Parallel fan-out
    for agent in ("campaign_planner", "personalisation_engine",
                  "paid_media_optimiser", "performance_analyst"):
        b.add_edge(START, agent)
        b.add_edge(agent, "merge_results")

    # Sequential tail
    b.add_edge("merge_results", "director_review")
    b.add_edge("director_review", "generate_report")
    b.add_edge("generate_report", END)

    interrupt = ["director_review"] if enable_hitl else []
    compiled = b.compile(checkpointer=MemorySaver(), interrupt_before=interrupt)
    log.info("Graph compiled  nodes=7  hitl=%s", enable_hitl)
    return compiled


command_centre_graph = build_command_centre_graph(enable_hitl=True)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

def run_command_centre(brief: str, thread_id: str = "default",
                       auto_approve: bool = True) -> dict[str, Any]:
    """Execute the full Command Centre pipeline for a campaign brief.

    Args:
        brief:        Campaign brief / mission statement.
        thread_id:    Unique thread ID for checkpointing.
        auto_approve: Automatically resume past the HITL interrupt.

    Returns:
        Final CommandCentreState dict.
    """
    graph = build_command_centre_graph(enable_hitl=True)
    config = {"configurable": {"thread_id": thread_id}}
    initial: CommandCentreState = {
        "brief": brief, "messages": [f"[CommandCentre] Brief: {brief}"]}

    result = graph.invoke(initial, config=config)
    snapshot = graph.get_state(config)
    if snapshot.next and "director_review" in snapshot.next:
        log.info("HITL interrupt — director_review pending")
        if auto_approve:
            log.info("Auto-approving: resuming past HITL gate")
            result = graph.invoke(None, config=config)
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("  Command Centre Orchestrator — Smoke Test")
    print("=" * 70)
    final = run_command_centre("Launch Q3 enterprise pipeline campaign",
                               thread_id="smoke-001", auto_approve=True)
    print(f"Messages: {len(final.get('messages', []))}")
    print(f"Status: {final.get('director_approval', {}).get('overall_status', 'N/A')}")
