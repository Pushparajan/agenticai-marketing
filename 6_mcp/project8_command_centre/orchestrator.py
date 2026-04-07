# orchestrator.py
# Project 8: Marketing Operations Command Centre (Capstone)
# Chapter Reference: Chapter 6 - MCP (Model Context Protocol)
# Description: LangGraph parallel multi-agent orchestrator with HITL gate
# Author: Pushparajan Ramar

"""LangGraph orchestrator for the Marketing Operations Command Centre.

Builds a ``StateGraph`` that executes four specialist agents in parallel,
then funnels their combined outputs through a Marketing Ops Director for
human-in-the-loop review and approval.

Graph topology::

    START
      |
      +----> campaign_planner --------+
      +----> personalisation_engine --+---> merge_results ---> director_review ---> generate_report ---> END
      +----> paid_media_optimiser ----+            ^
      +----> performance_analyst -----+            |
                                           (interrupt_before)

Key features:
    * **Parallel fan-out** — the four specialist agents run concurrently
      via a single parallel super-step.
    * **Merge node** — collects all parallel outputs into unified state.
    * **HITL interrupt** — ``interrupt_before=["director_review"]`` halts
      execution so a human can inspect before spend-impacting decisions.
    * **MemorySaver checkpointer** — enables resume-after-interrupt and
      full state replay.

Environment variables consumed (via .env):
    USE_MOCK -- "true" (default) bypasses LLM calls with deterministic output
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Annotated, Any

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from agents import (
    campaign_planner,
    marketing_ops_director,
    paid_media_optimiser,
    performance_analyst,
    personalisation_engine,
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
# State definition
# ---------------------------------------------------------------------------

def _merge_messages(left: list[str], right: list[str]) -> list[str]:
    """Reducer that appends new messages to the existing list."""
    return left + right


class CommandCentreState(TypedDict, total=False):
    """Shared state for the Marketing Operations Command Centre graph.

    Attributes:
        brief:                   Campaign brief / mission statement.
        campaign_plan:           Output from the CampaignPlanner agent.
        personalisation_results: Output from the PersonalisationEngine agent.
        media_optimisation:      Output from the PaidMediaOptimiser agent.
        performance_report:      Output from the PerformanceAnalyst agent.
        director_approval:       Output from the MarketingOpsDirector agent.
        execution_report:        Final consolidated report.
        messages:                Chronological log of agent actions.
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
# Graph node wrappers
# ---------------------------------------------------------------------------

def _node_campaign_planner(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for the CampaignPlanner agent."""
    return campaign_planner(state)


def _node_personalisation_engine(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for the PersonalisationEngine agent."""
    return personalisation_engine(state)


def _node_paid_media_optimiser(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for the PaidMediaOptimiser agent."""
    return paid_media_optimiser(state)


def _node_performance_analyst(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for the PerformanceAnalyst agent."""
    return performance_analyst(state)


def _node_merge_results(state: CommandCentreState) -> dict[str, Any]:
    """Merge node — collects parallel outputs and prepares for review.

    This node does not transform data; it acts as a synchronisation
    barrier between the parallel agents and the director.
    """
    log.info("MergeResults  syncing outputs from 4 parallel agents")

    plan = state.get("campaign_plan", {})
    pers = state.get("personalisation_results", {})
    media = state.get("media_optimisation", {})
    perf = state.get("performance_report", {})

    summary_parts = []
    if plan:
        summary_parts.append(f"Campaign: {plan.get('campaign_name', 'N/A')}")
    if pers:
        summary_parts.append(f"Variants: {pers.get('variants_created', 0)}")
    if media:
        summary_parts.append(f"Media recs: {len(media.get('recommendations', []))}")
    if perf:
        summary_parts.append(f"Report: {perf.get('report_title', 'N/A')}")

    return {
        "messages": [f"[MergeResults] Synced: {' | '.join(summary_parts)}"],
    }


def _node_director_review(state: CommandCentreState) -> dict[str, Any]:
    """Node wrapper for the MarketingOpsDirector (HITL gatekeeper)."""
    return marketing_ops_director(state)


def _node_generate_report(state: CommandCentreState) -> dict[str, Any]:
    """Generate the final consolidated execution report.

    Compiles all agent outputs and director decisions into a single
    structured report suitable for executive review.
    """
    log.info("GenerateReport  compiling final execution report")

    plan = state.get("campaign_plan", {})
    pers = state.get("personalisation_results", {})
    media = state.get("media_optimisation", {})
    perf = state.get("performance_report", {})
    approval = state.get("director_approval", {})

    # Count spend-impacting decisions
    spend_decisions = approval.get("spend_impacting_decisions", [])
    approved = sum(1 for d in spend_decisions if "APPROVED" in d.get("decision", ""))
    rejected = sum(1 for d in spend_decisions if d.get("decision") == "REJECTED")

    report = {
        "title": "Marketing Operations Command Centre — Execution Report",
        "generated_at": _ts(),
        "brief": state.get("brief", "N/A"),
        "sections": {
            "campaign_strategy": {
                "campaign_name": plan.get("campaign_name", "N/A"),
                "target_segment_size": plan.get("target_segment", {}).get("size", 0),
                "proposed_budget": plan.get("proposed_budget", 0),
                "channels": plan.get("channels", []),
                "timeline": plan.get("timeline", "N/A"),
                "success_metrics": plan.get("success_metrics", {}),
                "director_decision": approval.get("campaign_plan_review", {}).get(
                    "decision", "PENDING"
                ),
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
                "recommendations": [
                    {
                        "campaign": r.get("campaign_name", "N/A"),
                        "action": r.get("action", "N/A"),
                        "adjustment": r.get("adjustment_pct", 0),
                    }
                    for r in media.get("recommendations", [])
                ],
            },
            "performance": {
                "total_pipeline": perf.get("pipeline_health", {}).get(
                    "total_pipeline", 0
                ),
                "win_rate": perf.get("pipeline_health", {}).get("win_rate", 0),
                "blended_cpl": perf.get("channel_performance", {}).get(
                    "blended_cpl", 0
                ),
                "total_leads": perf.get("channel_performance", {}).get(
                    "total_leads", 0
                ),
                "key_insights": perf.get("key_insights", []),
            },
            "director_approval": {
                "overall_status": approval.get("overall_status", "PENDING"),
                "total_actions_reviewed": approval.get("total_actions_reviewed", 0),
                "approved": approved,
                "rejected": rejected,
                "director_notes": approval.get("director_notes", ""),
            },
        },
        "execution_log": state.get("messages", []),
    }

    log.info("GenerateReport  COMPLETE  status=%s",
             approval.get("overall_status", "PENDING"))
    return {
        "execution_report": report,
        "messages": [f"[GenerateReport] Final report compiled — "
                     f"status: {approval.get('overall_status', 'PENDING')}"],
    }


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_command_centre_graph(
    enable_hitl: bool = True,
) -> Any:
    """Construct and compile the Command Centre orchestrator graph.

    Args:
        enable_hitl: If True (default), insert an interrupt before the
                     director_review node to enable human approval.

    Returns:
        A compiled LangGraph ``StateGraph`` with MemorySaver checkpointer.
    """
    builder = StateGraph(CommandCentreState)

    # --- Add nodes ---
    builder.add_node("campaign_planner", _node_campaign_planner)
    builder.add_node("personalisation_engine", _node_personalisation_engine)
    builder.add_node("paid_media_optimiser", _node_paid_media_optimiser)
    builder.add_node("performance_analyst", _node_performance_analyst)
    builder.add_node("merge_results", _node_merge_results)
    builder.add_node("director_review", _node_director_review)
    builder.add_node("generate_report", _node_generate_report)

    # --- Parallel fan-out from START ---
    builder.add_edge(START, "campaign_planner")
    builder.add_edge(START, "personalisation_engine")
    builder.add_edge(START, "paid_media_optimiser")
    builder.add_edge(START, "performance_analyst")

    # --- Fan-in to merge ---
    builder.add_edge("campaign_planner", "merge_results")
    builder.add_edge("personalisation_engine", "merge_results")
    builder.add_edge("paid_media_optimiser", "merge_results")
    builder.add_edge("performance_analyst", "merge_results")

    # --- Sequential: merge -> director -> report -> END ---
    builder.add_edge("merge_results", "director_review")
    builder.add_edge("director_review", "generate_report")
    builder.add_edge("generate_report", END)

    # --- Compile with checkpointer and optional HITL interrupt ---
    checkpointer = MemorySaver()
    interrupt = ["director_review"] if enable_hitl else []

    compiled = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt,
    )

    node_count = 7
    log.info(
        "Command Centre graph compiled  nodes=%d  hitl=%s  "
        "interrupt_before=%s",
        node_count,
        enable_hitl,
        interrupt,
    )
    return compiled


# ---------------------------------------------------------------------------
# Module-level compiled graph
# ---------------------------------------------------------------------------

command_centre_graph = build_command_centre_graph(enable_hitl=True)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def run_command_centre(
    brief: str,
    thread_id: str = "default",
    auto_approve: bool = True,
) -> dict[str, Any]:
    """Execute the full Command Centre pipeline for a campaign brief.

    Args:
        brief:        The campaign brief / mission statement.
        thread_id:    Unique thread identifier for checkpointing.
        auto_approve: If True, automatically resume past the HITL interrupt.

    Returns:
        The final ``CommandCentreState`` dict.
    """
    graph = build_command_centre_graph(enable_hitl=True)
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: CommandCentreState = {
        "brief": brief,
        "messages": [f"[CommandCentre] Executing brief: {brief}"],
    }

    # First invocation — runs parallel agents + merge, then pauses at HITL
    result = graph.invoke(initial_state, config=config)

    # Check if we hit the HITL interrupt
    snapshot = graph.get_state(config)
    if snapshot.next and "director_review" in snapshot.next:
        log.info("HITL interrupt reached — director_review pending")
        if auto_approve:
            log.info("Auto-approving: resuming past HITL gate")
            result = graph.invoke(None, config=config)
        else:
            log.info("Waiting for manual approval (return current state)")

    return result


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  Marketing Operations Command Centre — Orchestrator")
    print("=" * 70)
    print(f"\n  USE_MOCK = {USE_MOCK}")
    print("  Graph topology:")
    print("    START -> [campaign_planner, personalisation_engine,")
    print("              paid_media_optimiser, performance_analyst] (parallel)")
    print("    -> merge_results")
    print("    -> director_review (HITL interrupt)")
    print("    -> generate_report")
    print("    -> END")
    print()

    # Quick smoke test
    print("--- Smoke Test ---")
    final = run_command_centre(
        brief="Launch Q3 enterprise pipeline campaign",
        thread_id="smoke-test-001",
        auto_approve=True,
    )
    print(f"\nExecution complete. Messages logged: {len(final.get('messages', []))}")
    print(f"Director status: "
          f"{final.get('director_approval', {}).get('overall_status', 'N/A')}")
