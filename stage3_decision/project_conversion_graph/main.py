# File      : main.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Entry point for the Decision-stage conversion graph.

Usage
-----
    # Mock mode (default — no API keys needed)
    python -m stage3_decision.project_conversion_graph.main

    # Real APIs
    USE_MOCK=false OPENAI_API_KEY=sk-... python -m stage3_decision.project_conversion_graph.main
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

# Ensure the repo root is on the path so ``stage3_decision`` resolves.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from stage3_decision.graph.graph import build_decision_graph
from stage3_decision.graph.state import DecisionJourneyState


# ---------------------------------------------------------------------------
# Demo scenarios
# ---------------------------------------------------------------------------

SCENARIOS: list[dict] = [
    {
        "label": "1) Clean close — high intent, proposal viewed",
        "state": {
            "contact_id": "contact-101",
            "company": "Acme Corp",
            "deal_id": "deal-001",
            "deal_value": 45000.0,
            "intent_score": 90,
            "days_in_decision": 5,
            "objections_raised": [],
            "competitors_named": [],
            "stakeholders": ["VP Engineering", "CTO"],
            "proposal_viewed": True,
            "pricing_tier_viewed": "professional",
            "last_action": "",
            "next_action": "",
            "human_approved": False,
            "messages": [],
        },
    },
    {
        "label": "2) Competitive — competitor named, battlecard needed",
        "state": {
            "contact_id": "contact-202",
            "company": "Beta Industries",
            "deal_id": "deal-002",
            "deal_value": 32000.0,
            "intent_score": 65,
            "days_in_decision": 8,
            "objections_raised": [],
            "competitors_named": ["CompetitorX"],
            "stakeholders": ["Head of Product"],
            "proposal_viewed": False,
            "pricing_tier_viewed": "standard",
            "last_action": "",
            "next_action": "",
            "human_approved": False,
            "messages": [],
        },
    },
    {
        "label": "3) Stalled deal — cold after 14+ days, urgency reactivation",
        "state": {
            "contact_id": "contact-303",
            "company": "Gamma Health",
            "deal_id": "deal-003",
            "deal_value": 28000.0,
            "intent_score": 40,
            "days_in_decision": 18,
            "objections_raised": [],
            "competitors_named": [],
            "stakeholders": ["Director of Ops"],
            "proposal_viewed": False,
            "pricing_tier_viewed": "enterprise",
            "last_action": "",
            "next_action": "",
            "human_approved": False,
            "messages": [],
        },
    },
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def run_scenario(graph, scenario: dict) -> None:
    """Execute a single scenario and print the results."""
    label = scenario["label"]
    state = scenario["state"]

    print(f"\n{'=' * 70}")
    print(f"  SCENARIO: {label}")
    print(f"{'=' * 70}")
    print(f"  Company      : {state['company']}")
    print(f"  Deal value   : ${state['deal_value']:,.0f}")
    print(f"  Intent score : {state['intent_score']}")
    print(f"  Days in dec. : {state['days_in_decision']}")
    print(f"  Objections   : {state['objections_raised']}")
    print(f"  Competitors  : {state['competitors_named']}")
    print(f"  Proposal view: {state['proposal_viewed']}")
    print("-" * 70)

    thread_id = uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(state, config=config)

    print(f"\n  >> Last action : {result.get('last_action', 'N/A')}")
    print(f"  >> Next action : {result.get('next_action', 'N/A')}")
    print(f"  >> Human appr. : {result.get('human_approved', False)}")

    msgs = result.get("messages", [])
    if msgs:
        print(f"\n  Messages ({len(msgs)}):")
        for m in msgs:
            content = m.content if hasattr(m, "content") else str(m)
            # Indent message content
            for line in content.split("\n"):
                print(f"    | {line}")
    print(f"{'=' * 70}\n")


async def main() -> None:
    """Build the graph and run all demo scenarios."""
    print("\n" + "#" * 70)
    print("#  Stage 3 — Decision  |  LangGraph Conversion Graph Demo")
    print("#" * 70)

    use_mock = os.getenv("USE_MOCK", "true").lower()
    print(f"\n  USE_MOCK = {use_mock}")
    if use_mock == "true":
        print("  (Running with mock data — set USE_MOCK=false for real APIs)\n")

    graph = build_decision_graph()

    for scenario in SCENARIOS:
        await run_scenario(graph, scenario)

    print("\nAll scenarios complete.")


if __name__ == "__main__":
    asyncio.run(main())
