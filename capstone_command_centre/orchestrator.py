# File      : orchestrator.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Capstone Command Centre Orchestrator.

LangGraph StateGraph that fans out to all six customer-journey stage nodes
concurrently (Send API), routes proposed actions through a
MarketingOpsDirector approval gate (interrupt_before for HITL), and
generates a full execution report.

Run:  python orchestrator.py            # demo (non-interactive)
      python orchestrator.py interactive # with HITL pause
"""
from __future__ import annotations

import json, logging, os, sys
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send
from langgraph.graph import END, START, StateGraph

from capstone_command_centre.stage_agents.awareness_node import awareness_node
from capstone_command_centre.stage_agents.consideration_node import consideration_node
from capstone_command_centre.stage_agents.decision_node import decision_node
from capstone_command_centre.stage_agents.onboarding_node import onboarding_node
from capstone_command_centre.stage_agents.retention_node import retention_node
from capstone_command_centre.stage_agents.advocacy_node import advocacy_node
from capstone_command_centre.director_agent import review_actions
from capstone_command_centre.mcp_client import get_call_log

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom reducer — merges stage_results dicts from concurrent nodes
# ---------------------------------------------------------------------------
def _merge(current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(current); merged.update(update); return merged

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class CommandCentreState(TypedDict, total=False):
    contact_email: str
    contact_id: str
    firstname: str
    lastname: str
    company: str
    deal_id: str
    recent_touches: int
    stage_results: Annotated[dict[str, Any], _merge]
    approval_decisions: dict[str, Any]
    execution_report: str

STAGE_NODES = ["awareness", "consideration", "decision",
               "onboarding", "retention", "advocacy"]

# ---------------------------------------------------------------------------
# Node wrappers
# ---------------------------------------------------------------------------
def _awareness(s: CommandCentreState) -> dict: return awareness_node(s)
def _consideration(s: CommandCentreState) -> dict: return consideration_node(s)
def _decision(s: CommandCentreState) -> dict: return decision_node(s)
def _onboarding(s: CommandCentreState) -> dict: return onboarding_node(s)
def _retention(s: CommandCentreState) -> dict: return retention_node(s)
def _advocacy(s: CommandCentreState) -> dict: return advocacy_node(s)

# ---------------------------------------------------------------------------
# Fan-out via conditional edge
# ---------------------------------------------------------------------------
def _route_to_stages(state: CommandCentreState) -> list[Send]:
    logger.info("=== Fan-out: dispatching to %d stage nodes ===", len(STAGE_NODES))
    return [Send(node, dict(state)) for node in STAGE_NODES]

# ---------------------------------------------------------------------------
# Director review
# ---------------------------------------------------------------------------
def review_and_approve(state: CommandCentreState) -> dict[str, Any]:
    logger.info("=== Director reviewing proposed actions ===")
    return review_actions(state)

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
_STAGE_DETAIL = {
    "awareness":     lambda r: f"Intent  : {r.get('intent_score','N/A')} ({r.get('intent_tier','N/A')})",
    "consideration": lambda r: f"Open Rate: {r.get('flow_performance',{}).get('open_rate',0):.0%}  CTR: {r.get('flow_performance',{}).get('ctr',0):.0%}",
    "decision":      lambda r: f"Deal    : {r.get('deal_id','N/A')}  Value: £{r.get('deal_value',0):,.0f}  Prob: {r.get('deal_probability',0):.0%}",
    "onboarding":    lambda r: f"TTV     : {r.get('days_to_value','N/A')}d  Benchmark: {r.get('benchmark_days','N/A')}d",
    "retention":     lambda r: f"Risk    : {r.get('churn_risk_score',0):.0%}  LTV: £{r.get('predicted_ltv',0):,.0f}",
    "advocacy":      lambda r: f"NPS     : {r.get('nps','N/A')}  Eligible: {r.get('is_eligible_advocate',False)}",
}

def generate_report(state: CommandCentreState) -> dict[str, Any]:
    stage_results = state.get("stage_results", {})
    decisions = state.get("approval_decisions", {})
    call_log = get_call_log()
    ln: list[str] = ["=" * 70,
        "  CAPSTONE COMMAND CENTRE — EXECUTION REPORT",
        f"  Generated: {datetime.now(timezone.utc).isoformat()}", "=" * 70, ""]
    for name in STAGE_NODES:
        r = stage_results.get(name, {}); d = decisions.get(name, {})
        a = r.get("proposed_action", {})
        ln.append(f"--- Stage: {name.upper()} ---")
        ln.append(f"  Contact : {r.get('email','N/A')}")
        ln.append(f"  {_STAGE_DETAIL.get(name, lambda r: '')(r)}")
        ln.append(f"  Action  : {a.get('action','N/A')}")
        ln.append(f"  Urgency : {a.get('urgency','N/A')}  Spend: £{a.get('suggested_spend',0):.0f}")
        ln.append(f"  Verdict : {d.get('verdict','pending')}")
        for w in d.get("warnings", []):  ln.append(f"  WARNING : {w}")
        for m in d.get("modifications", []): ln.append(f"  MODIFIED: {m}")
        ln.append("")
    ln.append("--- MCP TOOL CALLS ---")
    ln.append(f"  Total calls: {len(call_log)}")
    srv: dict[str, int] = {}
    for e in call_log: srv[e["server"]] = srv.get(e["server"], 0) + 1
    for s, c in sorted(srv.items()): ln.append(f"  {s}: {c} calls")
    ln += ["", "=" * 70]
    report = "\n".join(ln)
    logger.info("=== Report generated (%d lines) ===", len(ln))
    return {"execution_report": report}

# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------
def build_graph() -> StateGraph:
    b = StateGraph(CommandCentreState)
    for name, fn in [("awareness", _awareness), ("consideration", _consideration),
                     ("decision", _decision), ("onboarding", _onboarding),
                     ("retention", _retention), ("advocacy", _advocacy)]:
        b.add_node(name, fn)
    b.add_node("review_and_approve", review_and_approve)
    b.add_node("generate_report", generate_report)
    b.add_conditional_edges(START, _route_to_stages, STAGE_NODES)
    for stage in STAGE_NODES:
        b.add_edge(stage, "review_and_approve")
    b.add_edge("review_and_approve", "generate_report")
    b.add_edge("generate_report", END)
    return b

def compile_graph(*, interrupt_before_review: bool = True):
    checkpointer = MemorySaver()
    return build_graph().compile(
        checkpointer=checkpointer,
        interrupt_before=["review_and_approve"] if interrupt_before_review else [],
    )

# ---------------------------------------------------------------------------
# Default initial state
# ---------------------------------------------------------------------------
def _default_state() -> CommandCentreState:
    return {
        "contact_email": "alex@acmecorp.com", "contact_id": "C-1001",
        "firstname": "Alex", "lastname": "Rivera", "company": "Acme Corp",
        "deal_id": "D-5001", "recent_touches": 1,
        "stage_results": {}, "approval_decisions": {}, "execution_report": "",
    }

# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------
def run_demo() -> None:
    print("\n" + "=" * 70)
    print("  CAPSTONE COMMAND CENTRE — DEMO RUN")
    print("  Mock mode: all MCP tools return synthetic data")
    print("=" * 70 + "\n")
    graph = compile_graph(interrupt_before_review=False)
    config = {"configurable": {"thread_id": "demo-001"}}
    final: dict[str, Any] = {}
    for event in graph.stream(_default_state(), config=config):
        for _, update in event.items():
            if isinstance(update, dict):
                if "stage_results" in update:
                    existing = final.get("stage_results", {})
                    existing.update(update["stage_results"])
                    final["stage_results"] = existing
                for k, v in update.items():
                    if k != "stage_results": final[k] = v
    print(final.get("execution_report", "No report generated."))
    print("\n--- APPROVAL DECISIONS (JSON) ---")
    print(json.dumps(final.get("approval_decisions", {}), indent=2))
    print(f"\nTotal MCP tool calls: {len(get_call_log())}")
    print("Demo complete.\n")

# ---------------------------------------------------------------------------
# Interactive runner (HITL)
# ---------------------------------------------------------------------------
def run_interactive() -> None:
    print("\n" + "=" * 70)
    print("  CAPSTONE COMMAND CENTRE — INTERACTIVE MODE")
    print("  Graph pauses before director review for your approval.")
    print("=" * 70 + "\n")
    graph = compile_graph(interrupt_before_review=True)
    config = {"configurable": {"thread_id": "interactive-001"}}
    print("Running stage agents...\n")
    for event in graph.stream(_default_state(), config=config):
        for _, update in event.items():
            if isinstance(update, dict) and "stage_results" in update:
                for stage in update["stage_results"]:
                    print(f"  Completed: {stage}")
    snap = graph.get_state(config)
    sr = snap.values.get("stage_results", {})
    print("\n--- PROPOSED ACTIONS ---")
    for name, result in sr.items():
        a = result.get("proposed_action", {})
        print(f"  {name:15s}  {a.get('action','N/A'):30s}  "
              f"spend=£{a.get('suggested_spend',0):.0f}")
    print("\nApprove all actions and continue? [Y/n] ", end="")
    try:
        answer = input().strip().lower()
    except EOFError:
        answer = "y"
    if answer in ("", "y", "yes"):
        print("\nResuming — director review + report generation...\n")
        for _ in graph.stream(None, config=config): pass
        snap = graph.get_state(config)
        print(snap.values.get("execution_report", "No report."))
    else:
        print("\nAborted by user.")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    run_interactive() if mode == "interactive" else run_demo()
