# run.py
# Project 8: Marketing Operations Command Centre (Capstone)
# Chapter Reference: Chapter 6 - MCP (Model Context Protocol)
# Description: Runner that executes the full multi-agent Command Centre demo
# Author: Pushparajan Ramar

"""Capstone runner for the Marketing Operations Command Centre.

Initialises the MCP client (mock wrappers in demo mode), builds the
LangGraph orchestrator, and runs a complete scenario demonstrating
parallel agent execution, HITL interrupt, and structured reporting.

Usage:  python run.py
Environment variables: USE_MOCK (default "true"), OPENAI_API_KEY (live mode).
"""

from __future__ import annotations

import json, logging, os, sys
from typing import Any
from dotenv import load_dotenv

load_dotenv()
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
logging.basicConfig(level=logging.WARNING, format="%(asctime)s  [%(levelname)s]  %(message)s")

BORDER = "=" * 74
THIN = "-" * 74


def _header(title: str) -> None:
    print(f"\n{BORDER}\n  {title}\n{BORDER}")

def _sub(title: str) -> None:
    print(f"\n  {THIN}\n  {title}\n  {THIN}")

def _kv(key: str, val: Any, indent: int = 4) -> None:
    pad = " " * indent
    if isinstance(val, float):
        print(f"{pad}{key:<30} {val:>12.2f}")
    elif isinstance(val, int):
        print(f"{pad}{key:<30} {val:>12,}")
    else:
        print(f"{pad}{key:<30} {val}")


def print_execution_report(state: dict[str, Any]) -> None:
    """Print structured execution report from final graph state."""
    report = state.get("execution_report", {})
    sec = report.get("sections", {})

    _header("EXECUTION REPORT")
    print(f"\n  Brief: {report.get('brief', 'N/A')}")
    print(f"  Generated: {report.get('generated_at', 'N/A')}")

    # 1. Campaign Strategy
    s = sec.get("campaign_strategy", {})
    _sub("1. CAMPAIGN STRATEGY (CampaignPlanner)")
    _kv("Campaign Name", s.get("campaign_name", "N/A"))
    _kv("Target Segment Size", s.get("target_segment_size", 0))
    _kv("Proposed Budget", f"${s.get('proposed_budget', 0):,}")
    _kv("Timeline", s.get("timeline", "N/A"))
    _kv("Channels", ", ".join(s.get("channels", [])))
    _kv("Director Decision", s.get("director_decision", "PENDING"))
    metrics = s.get("success_metrics", {})
    if metrics:
        print("    Success Metrics:")
        for mk, mv in metrics.items():
            label = mk.replace("_", " ").title()
            if isinstance(mv, float):
                _kv(label, f"{mv:.1f}x" if mv < 100 else f"${mv:,.0f}", 6)
            else:
                _kv(label, f"${mv:,}" if isinstance(mv, int) and mv > 1000 else str(mv), 6)

    # 2. Personalisation
    p = sec.get("personalisation", {})
    _sub("2. PERSONALISATION (PersonalisationEngine)")
    _kv("Campaign ID", p.get("campaign_id", "N/A"))
    _kv("Strategy", p.get("strategy", "N/A"))
    _kv("Variants Created", p.get("variants_created", 0))
    _kv("Predicted Lift", f"{p.get('predicted_lift', 0):.0%}")
    _kv("Estimated Recipients", p.get("estimated_recipients", 0))

    # 3. Paid Media
    m = sec.get("paid_media", {})
    _sub("3. PAID MEDIA (PaidMediaOptimiser)")
    _kv("Campaigns Analysed", m.get("campaigns_analysed", 0))
    _kv("Total Spend MTD", f"${m.get('total_spend_mtd', 0):,}")
    _kv("Recommendations", m.get("recommendations_count", 0))
    _kv("Spend-Impacting", m.get("spend_impacting_count", 0))
    for i, r in enumerate(m.get("recommendations", []), 1):
        adj = r.get("adjustment", 0)
        adj_s = f"{adj:+.0f}%" if adj else "N/A"
        print(f"      {i}. [{r.get('action','?'):>15}] {r.get('campaign','?'):<35} ({adj_s})")

    # 4. Performance
    pf = sec.get("performance", {})
    _sub("4. PERFORMANCE (PerformanceAnalyst)")
    _kv("Total Pipeline", f"${pf.get('total_pipeline', 0):,}")
    _kv("Win Rate", f"{pf.get('win_rate', 0):.0%}")
    _kv("Blended CPL", f"${pf.get('blended_cpl', 0):.2f}")
    _kv("Total Leads", pf.get("total_leads", 0))
    for i, ins in enumerate(pf.get("key_insights", []), 1):
        print(f"      {i}. {ins}")

    # 5. Director
    d = sec.get("director_approval", {})
    _sub("5. DIRECTOR REVIEW (MarketingOpsDirector)")
    _kv("Overall Status", d.get("overall_status", "PENDING"))
    _kv("Actions Reviewed", d.get("total_actions_reviewed", 0))
    _kv("Approved", d.get("approved", 0))
    _kv("Rejected", d.get("rejected", 0))
    notes = d.get("director_notes", "")
    if notes:
        print(f"    Notes: {notes}")

    # Execution log
    msgs = report.get("execution_log", [])
    if msgs:
        _sub("EXECUTION LOG")
        for i, msg in enumerate(msgs, 1):
            print(f"    {i:>2}. {msg}")

    print(f"\n{BORDER}\n  FINAL STATUS: {d.get('overall_status', 'PENDING')}\n{BORDER}")


def print_spend_decisions(state: dict[str, Any]) -> None:
    """Print detailed spend-impacting action decisions."""
    decisions = state.get("director_approval", {}).get("spend_impacting_decisions", [])
    if not decisions:
        return
    _sub("SPEND-IMPACTING DECISIONS")
    markers = {"APPROVED": "[PASS]", "APPROVED_WITH_CONDITIONS": "[COND]", "REJECTED": "[DENY]"}
    for i, d in enumerate(decisions, 1):
        m = markers.get(d.get("decision", ""), "[????]")
        print(f"\n    {m} #{i}: {d.get('type', d.get('action_type', 'N/A'))}")
        print(f"         Source:    {d.get('source', d.get('source_agent', 'N/A'))}")
        print(f"         Details:   {d.get('details', 'N/A')}")
        print(f"         Decision:  {d.get('decision', 'N/A')}")
        print(f"         Rationale: {d.get('rationale', 'N/A')}")
        for c in d.get("conditions", []):
            print(f"           - {c}")


def run_demo() -> None:
    """Execute the full Command Centre demo scenario."""
    from orchestrator import run_command_centre

    _header("MARKETING OPERATIONS COMMAND CENTRE")
    print("  Project 8 — Capstone Demonstration")
    print("  Multi-Agent + MCP Architecture")
    print(BORDER)
    print(f"\n  Mode:          {'MOCK (deterministic)' if USE_MOCK else 'LIVE (API calls)'}")
    print(f"  Agents:        5 (4 parallel + 1 director)")
    print(f"  MCP Servers:   6 (CRM, CDP, Email, Paid Media, Analytics, Content)")
    print(f"  HITL Gate:     Enabled (interrupt before director review)")
    print(f"  Checkpointer:  MemorySaver")

    brief = "Launch Q3 enterprise pipeline campaign"
    _sub(f"SCENARIO: {brief}")
    print("""
    Four specialist agents work in parallel:
      1. CampaignPlanner        -> CRM + CDP
      2. PersonalisationEngine  -> CDP + Email
      3. PaidMediaOptimiser     -> Paid Media + Analytics
      4. PerformanceAnalyst     -> Analytics + CRM

    MarketingOpsDirector reviews all outputs at the HITL gate.
    """)
    print("  Executing orchestrator...\n")

    final = run_command_centre(brief=brief, thread_id="capstone-demo-001",
                               auto_approve=True)

    print_execution_report(final)
    print_spend_decisions(final)

    _header("DEMO COMPLETE")
    appr = final.get("director_approval", {})
    plan = final.get("campaign_plan", {})
    pers = final.get("personalisation_results", {})
    media = final.get("media_optimisation", {})
    pipe = final.get("performance_report", {}).get("pipeline_health", {})

    print(f"""
  The Command Centre successfully:
    1. Executed 4 agents in parallel via LangGraph fan-out
    2. Queried 6 MCP server tool registries (14 tools)
    3. Campaign plan: {plan.get('target_segment',{}).get('size',0):,} profiles targeted
    4. Personalisation: {pers.get('variants_created',0)} content variants
    5. Media: {len(media.get('recommendations',[]))} optimisation recommendations
    6. Performance: ${pipe.get('total_pipeline',0):,} pipeline analysed
    7. Director reviewed {appr.get('total_actions_reviewed',0)} spend-impacting actions
    8. Status: {appr.get('overall_status','N/A')}

  Log entries: {len(final.get('messages',[]))}
  Thread: capstone-demo-001 (checkpointed for replay)
    """)
    print(BORDER)


if __name__ == "__main__":
    run_demo()
