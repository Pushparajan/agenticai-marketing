# File      : orchestrator.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Capstone Command Centre Orchestrator.

Builds a LangGraph ``StateGraph`` that fans out to all six customer-journey
stage nodes concurrently (via the Send API), collects proposed actions,
routes them through a MarketingOpsDirector approval gate with
``interrupt_before`` for human-in-the-loop, and generates a full
execution report.

Run:
    python orchestrator.py
"""

from __future__ import annotations

import json
import logging
import operator
import os
import sys
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send
from langgraph.graph import END, START, StateGraph

# ---------------------------------------------------------------------------
# Stage-node imports
# ---------------------------------------------------------------------------

from capstone_command_centre.stage_agents.awareness_node import awareness_node
from capstone_command_centre.stage_agents.consideration_node import (
    consideration_node,
)
from capstone_command_centre.stage_agents.decision_node import decision_node
from capstone_command_centre.stage_agents.onboarding_node import onboarding_node
from capstone_command_centre.stage_agents.retention_node import retention_node
from capstone_command_centre.stage_agents.advocacy_node import advocacy_node
from capstone_command_centre.director_agent import review_actions
from capstone_command_centre.mcp_client import get_call_log

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom reducer for stage_results
# ---------------------------------------------------------------------------

def _merge_stage_results(
    current: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]:
    """Merge stage result dicts — each stage key is written once."""
    merged = dict(current)
    merged.update(update)
    return merged


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------

class CommandCentreState(TypedDict, total=False):
    """Shared state flowing through the Command Centre graph."""
    # Input fields
    contact_email: str
    contact_id: str
    firstname: str
    lastname: str
    company: str
    deal_id: str
    recent_touches: int

    # Populated by stage nodes (custom reducer for concurrent merging)
    stage_results: Annotated[dict[str, Any], _merge_stage_results]

    # Populated by director
    approval_decisions: dict[str, Any]

    # Populated by report generator
    execution_report: str


# ---------------------------------------------------------------------------
# Node wrappers — thin adapters for the StateGraph
# ---------------------------------------------------------------------------

def _awareness(state: CommandCentreState) -> dict[str, Any]:
    return awareness_node(state)

def _consideration(state: CommandCentreState) -> dict[str, Any]:
    return consideration_node(state)

def _decision(state: CommandCentreState) -> dict[str, Any]:
    return decision_node(state)

def _onboarding(state: CommandCentreState) -> dict[str, Any]:
    return onboarding_node(state)

def _retention(state: CommandCentreState) -> dict[str, Any]:
    return retention_node(state)

def _advocacy(state: CommandCentreState) -> dict[str, Any]:
    return advocacy_node(state)


# ---------------------------------------------------------------------------
# Stage list
# ---------------------------------------------------------------------------

STAGE_NODES = [
    "awareness", "consideration", "decision",
    "onboarding", "retention", "advocacy",
]


# ---------------------------------------------------------------------------
# Fan-out routing — returns Send objects via conditional edge
# ---------------------------------------------------------------------------

def _route_to_stages(state: CommandCentreState) -> list[Send]:
    """Dispatch the current state to all six stage nodes via Send API."""
    logger.info("=== Fan-out: dispatching to %d stage nodes ===",
                len(STAGE_NODES))
    return [Send(node, dict(state)) for node in STAGE_NODES]


# ---------------------------------------------------------------------------
# Director review node
# ---------------------------------------------------------------------------

def review_and_approve(state: CommandCentreState) -> dict[str, Any]:
    """MarketingOpsDirector reviews all proposed actions."""
    logger.info("=== Director reviewing proposed actions ===")
    return review_actions(state)


# ---------------------------------------------------------------------------
# Report generation node
# ---------------------------------------------------------------------------

def generate_report(state: CommandCentreState) -> dict[str, Any]:
    """Build a human-readable execution report from state."""
    stage_results = state.get("stage_results", {})
    decisions = state.get("approval_decisions", {})
    call_log = get_call_log()

    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("  CAPSTONE COMMAND CENTRE — EXECUTION REPORT")
    lines.append(f"  Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("=" * 70)
    lines.append("")

    # ---- Per-stage summaries ----
    for stage_name in STAGE_NODES:
        result = stage_results.get(stage_name, {})
        decision = decisions.get(stage_name, {})
        action = result.get("proposed_action", {})

        lines.append(f"--- Stage: {stage_name.upper()} ---")
        lines.append(f"  Contact : {result.get('email', 'N/A')}")

        # Stage-specific highlights
        if stage_name == "awareness":
            lines.append(f"  Intent  : {result.get('intent_score', 'N/A')} "
                         f"({result.get('intent_tier', 'N/A')})")
        elif stage_name == "consideration":
            fp = result.get("flow_performance", {})
            lines.append(f"  Open Rate: {fp.get('open_rate', 0):.0%}  "
                         f"CTR: {fp.get('ctr', 0):.0%}")
        elif stage_name == "decision":
            lines.append(f"  Deal    : {result.get('deal_id', 'N/A')}  "
                         f"Value: £{result.get('deal_value', 0):,.0f}  "
                         f"Prob: {result.get('deal_probability', 0):.0%}")
        elif stage_name == "onboarding":
            lines.append(f"  TTV     : {result.get('days_to_value', 'N/A')}d  "
                         f"Benchmark: {result.get('benchmark_days', 'N/A')}d")
        elif stage_name == "retention":
            lines.append(f"  Risk    : {result.get('churn_risk_score', 0):.0%}  "
                         f"LTV: £{result.get('predicted_ltv', 0):,.0f}")
        elif stage_name == "advocacy":
            lines.append(f"  NPS     : {result.get('nps', 'N/A')}  "
                         f"Eligible: {result.get('is_eligible_advocate', False)}")

        lines.append(f"  Action  : {action.get('action', 'N/A')}")
        lines.append(f"  Urgency : {action.get('urgency', 'N/A')}")
        lines.append(f"  Spend   : £{action.get('suggested_spend', 0):.0f}")
        lines.append(f"  Verdict : {decision.get('verdict', 'pending')}")

        if decision.get("warnings"):
            for w in decision["warnings"]:
                lines.append(f"  WARNING : {w}")
        if decision.get("modifications"):
            for m in decision["modifications"]:
                lines.append(f"  MODIFIED: {m}")

        lines.append("")

    # ---- MCP call summary ----
    lines.append("--- MCP TOOL CALLS ---")
    lines.append(f"  Total calls: {len(call_log)}")
    server_counts: dict[str, int] = {}
    for entry in call_log:
        srv = entry.get("server", "unknown")
        server_counts[srv] = server_counts.get(srv, 0) + 1
    for srv, cnt in sorted(server_counts.items()):
        lines.append(f"  {srv}: {cnt} calls")

    lines.append("")
    lines.append("=" * 70)

    report = "\n".join(lines)
    logger.info("=== Report generated (%d lines) ===", len(lines))
    return {"execution_report": report}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct the Command Centre StateGraph.

    Topology::

        START ──(conditional/Send)──> [awareness, consideration, decision,
                                       onboarding, retention, advocacy]
              ──> review_and_approve  (interrupt_before HITL)
              ──> generate_report
              ──> END
    """
    builder = StateGraph(CommandCentreState)

    # --- Add stage nodes ---
    builder.add_node("awareness", _awareness)
    builder.add_node("consideration", _consideration)
    builder.add_node("decision", _decision)
    builder.add_node("onboarding", _onboarding)
    builder.add_node("retention", _retention)
    builder.add_node("advocacy", _advocacy)

    # --- Approval + report nodes ---
    builder.add_node("review_and_approve", review_and_approve)
    builder.add_node("generate_report", generate_report)

    # --- Fan-out from START to all stage nodes via Send API ---
    builder.add_conditional_edges(START, _route_to_stages, STAGE_NODES)

    # --- Fan-in: each stage node feeds into review_and_approve ---
    for stage in STAGE_NODES:
        builder.add_edge(stage, "review_and_approve")

    # --- Sequential edges ---
    builder.add_edge("review_and_approve", "generate_report")
    builder.add_edge("generate_report", END)

    return builder


def compile_graph(*, interrupt_before_review: bool = True):
    """Compile the graph with MemorySaver checkpointer.

    Parameters
    ----------
    interrupt_before_review : bool
        If True, the graph pauses before ``review_and_approve`` for
        human-in-the-loop confirmation.
    """
    checkpointer = MemorySaver()
    builder = build_graph()

    interrupt = ["review_and_approve"] if interrupt_before_review else []

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt,
    )


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------

def run_demo() -> None:
    """Run a complete demo with a sample contact through all six stages."""
    print("\n" + "=" * 70)
    print("  CAPSTONE COMMAND CENTRE — DEMO RUN")
    print("  Mock mode: all MCP tools return synthetic data")
    print("=" * 70 + "\n")

    # Build graph WITHOUT interrupt for non-interactive demo
    graph = compile_graph(interrupt_before_review=False)

    # Sample input state
    initial_state: CommandCentreState = {
        "contact_email": "alex@acmecorp.com",
        "contact_id": "C-1001",
        "firstname": "Alex",
        "lastname": "Rivera",
        "company": "Acme Corp",
        "deal_id": "D-5001",
        "recent_touches": 1,
        "stage_results": {},
        "approval_decisions": {},
        "execution_report": "",
    }

    config = {"configurable": {"thread_id": "demo-001"}}

    # Stream through the graph and capture final state
    final_state: dict[str, Any] = {}
    for event in graph.stream(initial_state, config=config):
        for node_name, update in event.items():
            if isinstance(update, dict):
                if "stage_results" in update:
                    existing = final_state.get("stage_results", {})
                    existing.update(update["stage_results"])
                    final_state["stage_results"] = existing
                for k, v in update.items():
                    if k != "stage_results":
                        final_state[k] = v

    # Print the execution report
    report = final_state.get("execution_report", "No report generated.")
    print(report)

    # Print approval decisions as JSON
    decisions = final_state.get("approval_decisions", {})
    print("\n--- APPROVAL DECISIONS (JSON) ---")
    print(json.dumps(decisions, indent=2))

    # Summary
    call_log = get_call_log()
    print(f"\nTotal MCP tool calls: {len(call_log)}")
    print("Demo complete.\n")


# ---------------------------------------------------------------------------
# Interactive runner (with HITL interrupt)
# ---------------------------------------------------------------------------

def run_interactive() -> None:
    """Run with human-in-the-loop approval at the director stage."""
    print("\n" + "=" * 70)
    print("  CAPSTONE COMMAND CENTRE — INTERACTIVE MODE")
    print("  Graph will pause before director review for your approval.")
    print("=" * 70 + "\n")

    graph = compile_graph(interrupt_before_review=True)

    initial_state: CommandCentreState = {
        "contact_email": "alex@acmecorp.com",
        "contact_id": "C-1001",
        "firstname": "Alex",
        "lastname": "Rivera",
        "company": "Acme Corp",
        "deal_id": "D-5001",
        "recent_touches": 1,
        "stage_results": {},
        "approval_decisions": {},
        "execution_report": "",
    }

    config = {"configurable": {"thread_id": "interactive-001"}}

    # First run — executes up to the interrupt
    print("Running stage agents...\n")
    for event in graph.stream(initial_state, config=config):
        for node_name, update in event.items():
            if isinstance(update, dict) and "stage_results" in update:
                for stage in update["stage_results"]:
                    print(f"  Completed: {stage}")

    # Show proposed actions
    snapshot = graph.get_state(config)
    stage_results = snapshot.values.get("stage_results", {})
    print("\n--- PROPOSED ACTIONS ---")
    for stage_name, result in stage_results.items():
        action = result.get("proposed_action", {})
        print(f"  {stage_name:15s}  {action.get('action', 'N/A'):30s}  "
              f"spend=£{action.get('suggested_spend', 0):.0f}")

    # HITL approval
    print("\nApprove all actions and continue? [Y/n] ", end="")
    try:
        answer = input().strip().lower()
    except EOFError:
        answer = "y"

    if answer in ("", "y", "yes"):
        print("\nResuming — director review + report generation...\n")
        for event in graph.stream(None, config=config):
            pass

        snapshot = graph.get_state(config)
        report = snapshot.values.get("execution_report", "No report.")
        print(report)
    else:
        print("\nAborted by user.")


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Add parent dir to path so imports work when run directly
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"

    if mode == "interactive":
        run_interactive()
    else:
        run_demo()
