# run.py
# Project 8: Marketing Operations Command Centre (Capstone)
# Chapter Reference: Chapter 6 - MCP (Model Context Protocol)
# Description: Runner that executes the full multi-agent Command Centre demo
# Author: Pushparajan Ramar

"""Capstone runner for the Marketing Operations Command Centre.

Initialises the MCP client (mock wrappers in demo mode), builds the
LangGraph orchestrator, and runs a complete scenario that demonstrates:

    * Parallel execution of four specialist agents
    * Human-in-the-loop interrupt before spend-impacting decisions
    * Director review and approval gate
    * Structured execution report generation

Usage:
    python run.py

Environment variables consumed (via .env):
    USE_MOCK       -- "true" (default) bypasses LLM / server calls
    OPENAI_API_KEY -- Required when USE_MOCK is "false"
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

BORDER = "=" * 74
THIN = "-" * 74


def _header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{BORDER}")
    print(f"  {title}")
    print(BORDER)


def _subheader(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n  {THIN}")
    print(f"  {title}")
    print(f"  {THIN}")


def _kv(key: str, value: Any, indent: int = 4) -> None:
    """Print a key-value pair with consistent formatting."""
    pad = " " * indent
    if isinstance(value, float):
        print(f"{pad}{key:<30} {value:>12.2f}")
    elif isinstance(value, int):
        print(f"{pad}{key:<30} {value:>12,}")
    else:
        print(f"{pad}{key:<30} {value}")


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_execution_report(state: dict[str, Any]) -> None:
    """Print a structured execution report from the final graph state.

    Args:
        state: The final ``CommandCentreState`` after full execution.
    """
    report = state.get("execution_report", {})
    sections = report.get("sections", {})

    _header("MARKETING OPERATIONS COMMAND CENTRE — EXECUTION REPORT")
    print(f"\n  Brief: {report.get('brief', 'N/A')}")
    print(f"  Generated: {report.get('generated_at', 'N/A')}")

    # --- Campaign Strategy ---
    strategy = sections.get("campaign_strategy", {})
    _subheader("1. CAMPAIGN STRATEGY (CampaignPlanner)")
    _kv("Campaign Name", strategy.get("campaign_name", "N/A"))
    _kv("Target Segment Size", strategy.get("target_segment_size", 0))
    _kv("Proposed Budget", f"${strategy.get('proposed_budget', 0):,}")
    _kv("Timeline", strategy.get("timeline", "N/A"))
    _kv("Channels", ", ".join(strategy.get("channels", [])))
    _kv("Director Decision", strategy.get("director_decision", "PENDING"))

    metrics = strategy.get("success_metrics", {})
    if metrics:
        print(f"\n    Success Metrics:")
        for mk, mv in metrics.items():
            label = mk.replace("_", " ").title()
            if isinstance(mv, float):
                _kv(label, f"{mv:.1f}x" if mv < 100 else f"${mv:,.0f}", indent=6)
            elif isinstance(mv, int):
                _kv(label, f"${mv:,}" if mv > 1000 else str(mv), indent=6)
            else:
                _kv(label, mv, indent=6)

    # --- Personalisation ---
    pers = sections.get("personalisation", {})
    _subheader("2. PERSONALISATION (PersonalisationEngine)")
    _kv("Campaign ID", pers.get("campaign_id", "N/A"))
    _kv("Strategy", pers.get("strategy", "N/A"))
    _kv("Variants Created", pers.get("variants_created", 0))
    _kv("Predicted Lift", f"{pers.get('predicted_lift', 0):.0%}")
    _kv("Estimated Recipients", pers.get("estimated_recipients", 0))

    # --- Paid Media ---
    media = sections.get("paid_media", {})
    _subheader("3. PAID MEDIA OPTIMISATION (PaidMediaOptimiser)")
    _kv("Campaigns Analysed", media.get("campaigns_analysed", 0))
    _kv("Total Spend MTD", f"${media.get('total_spend_mtd', 0):,}")
    _kv("Recommendations", media.get("recommendations_count", 0))
    _kv("Spend-Impacting", media.get("spend_impacting_count", 0))

    recs = media.get("recommendations", [])
    if recs:
        print(f"\n    Recommendations:")
        for i, r in enumerate(recs, 1):
            adj = r.get("adjustment", 0)
            adj_str = f"{adj:+.0f}%" if adj != 0 else "N/A"
            print(f"      {i}. [{r.get('action', 'N/A'):>15}] "
                  f"{r.get('campaign', 'N/A'):<40} ({adj_str})")

    # --- Performance ---
    perf = sections.get("performance", {})
    _subheader("4. PERFORMANCE ANALYSIS (PerformanceAnalyst)")
    _kv("Total Pipeline", f"${perf.get('total_pipeline', 0):,}")
    _kv("Win Rate", f"{perf.get('win_rate', 0):.0%}")
    _kv("Blended CPL", f"${perf.get('blended_cpl', 0):.2f}")
    _kv("Total Leads", perf.get("total_leads", 0))

    insights = perf.get("key_insights", [])
    if insights:
        print(f"\n    Key Insights:")
        for i, insight in enumerate(insights, 1):
            print(f"      {i}. {insight}")

    # --- Director Approval ---
    director = sections.get("director_approval", {})
    _subheader("5. DIRECTOR REVIEW (MarketingOpsDirector)")
    _kv("Overall Status", director.get("overall_status", "PENDING"))
    _kv("Actions Reviewed", director.get("total_actions_reviewed", 0))
    _kv("Approved", director.get("approved", 0))
    _kv("Rejected", director.get("rejected", 0))

    notes = director.get("director_notes", "")
    if notes:
        print(f"\n    Director Notes:")
        # Wrap long notes at ~68 chars
        words = notes.split()
        line = "      "
        for word in words:
            if len(line) + len(word) + 1 > 72:
                print(line)
                line = "      " + word
            else:
                line += (" " if line.strip() else "") + word
        if line.strip():
            print(line)

    # --- Execution Log ---
    messages = report.get("execution_log", [])
    if messages:
        _subheader("EXECUTION LOG")
        for i, msg in enumerate(messages, 1):
            print(f"    {i:>2}. {msg}")

    print(f"\n{BORDER}")
    status = director.get("overall_status", "PENDING")
    print(f"  FINAL STATUS: {status}")
    print(BORDER)


# ---------------------------------------------------------------------------
# Spend-impacting action detail report
# ---------------------------------------------------------------------------

def print_spend_decisions(state: dict[str, Any]) -> None:
    """Print detailed spend-impacting action decisions.

    Args:
        state: The final ``CommandCentreState``.
    """
    approval = state.get("director_approval", {})
    decisions = approval.get("spend_impacting_decisions", [])

    if not decisions:
        print("\n  No spend-impacting decisions to display.")
        return

    _subheader("SPEND-IMPACTING ACTION DECISIONS")
    for i, decision in enumerate(decisions, 1):
        status_marker = {
            "APPROVED": "[PASS]",
            "APPROVED_WITH_CONDITIONS": "[COND]",
            "REJECTED": "[DENY]",
        }.get(decision.get("decision", ""), "[????]")

        print(f"\n    {status_marker} Action {i}: {decision.get('action_type', 'N/A')}")
        print(f"           Source:    {decision.get('source_agent', 'N/A')}")
        print(f"           Details:   {decision.get('details', 'N/A')}")
        print(f"           Decision:  {decision.get('decision', 'N/A')}")
        print(f"           Rationale: {decision.get('rationale', 'N/A')}")

        conditions = decision.get("conditions", [])
        if conditions:
            print(f"           Conditions:")
            for cond in conditions:
                print(f"             - {cond}")


# ---------------------------------------------------------------------------
# Main demo scenario
# ---------------------------------------------------------------------------

def run_demo() -> None:
    """Execute the full Command Centre demo scenario.

    Scenario: "Launch Q3 enterprise pipeline campaign"

    This demonstrates:
        1. Parallel agent execution (4 agents run concurrently)
        2. HITL interrupt before director review
        3. Auto-approval and report generation
        4. Structured output from every agent
    """
    # Late import to keep module-level logging clean
    from orchestrator import run_command_centre

    _header("MARKETING OPERATIONS COMMAND CENTRE")
    print("  Project 8 — Capstone Demonstration")
    print("  Multi-Agent + MCP Architecture")
    print(BORDER)

    print(f"\n  Mode:          {'MOCK (deterministic demo)' if USE_MOCK else 'LIVE (API calls)'}")
    print(f"  Agents:        5 (4 parallel specialists + 1 director)")
    print(f"  MCP Servers:   6 (CRM, CDP, Email, Paid Media, Analytics, Content)")
    print(f"  HITL Gate:     Enabled (interrupt before director review)")
    print(f"  Checkpointer:  MemorySaver (in-memory state persistence)")

    brief = "Launch Q3 enterprise pipeline campaign"

    _subheader(f"SCENARIO: {brief}")
    print("""
    Objective: Design and launch a multi-channel enterprise campaign for Q3
    that targets high-intent enterprise buyers, leverages personalised email
    nurture sequences, optimises paid media spend across LinkedIn, and
    generates a comprehensive performance baseline.

    The four specialist agents will work in parallel:
      1. CampaignPlanner        -> Strategy using CRM + CDP data
      2. PersonalisationEngine  -> Content variants via CDP + Email tools
      3. PaidMediaOptimiser     -> Spend recommendations via Media + Analytics
      4. PerformanceAnalyst     -> Baseline report via Analytics + CRM

    The MarketingOpsDirector will then review all outputs and approve
    or reject spend-impacting actions.
    """)

    print("  Executing orchestrator...\n")

    # Run the full pipeline
    final_state = run_command_centre(
        brief=brief,
        thread_id="capstone-demo-001",
        auto_approve=True,
    )

    # Print the full execution report
    print_execution_report(final_state)

    # Print spend-impacting decision details
    print_spend_decisions(final_state)

    # Final summary
    _header("DEMO COMPLETE")
    approval = final_state.get("director_approval", {})
    report = final_state.get("execution_report", {})

    print(f"""
  The Marketing Operations Command Centre successfully:

    1. Executed 4 specialist agents in parallel via LangGraph
    2. Queried 6 MCP server tool registries (14 tools total)
    3. Generated a campaign plan targeting {
        final_state.get('campaign_plan', {}).get('target_segment', {}).get('size', 0):,
    } profiles
    4. Created {
        final_state.get('personalisation_results', {}).get('variants_created', 0)
    } personalised content variants
    5. Produced {len(
        final_state.get('media_optimisation', {}).get('recommendations', [])
    )} paid media optimisation recommendations
    6. Compiled a performance report covering ${
        final_state.get('performance_report', {}).get('pipeline_health', {}).get('total_pipeline', 0):,
    } pipeline
    7. Director reviewed {
        approval.get('total_actions_reviewed', 0)
    } spend-impacting actions
    8. Final status: {approval.get('overall_status', 'N/A')}

  Total execution log entries: {len(final_state.get('messages', []))}
  Checkpointed state available for replay via thread_id: capstone-demo-001
    """)
    print(BORDER)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_demo()
