# run.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: Simulated 30-day journey runner demonstrating adaptive paths
# Author: Pushparajan Ramar

"""Thirty-day journey simulation runner.

Creates sample contacts with varying engagement patterns and runs each
through the LangGraph journey orchestrator day-by-day.  Demonstrates
how different engagement levels drive contacts along distinct paths:

* **High-engagement** contacts receive a welcome, quickly qualify, get a
  demo offer, and are handed off to sales.
* **Medium-engagement** contacts receive multiple nurture emails that
  gradually escalate in content sophistication.
* **Low-engagement** contacts eventually move into a long-term nurture
  track after several unproductive touchpoints.

The runner uses a fresh ``StateGraph`` per simulation (with its own
MemorySaver) so thread IDs remain unique across runs.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from nodes import (
    enter_long_nurture,
    evaluate_engagement,
    handoff_to_sales,
    send_demo_offer,
    send_nurture_email,
    send_welcome_email,
)
from routing import route_after_demo, route_next_touch
from state import JourneyState

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph builder (fresh per simulation for clean checkpointer)
# ---------------------------------------------------------------------------

def _build_graph() -> tuple[Any, MemorySaver]:
    """Build and compile a fresh journey graph with its own checkpointer."""
    builder = StateGraph(JourneyState)

    builder.add_node("send_welcome_email", send_welcome_email)
    builder.add_node("evaluate_engagement", evaluate_engagement)
    builder.add_node("send_nurture_email", send_nurture_email)
    builder.add_node("send_demo_offer", send_demo_offer)
    builder.add_node("handoff_to_sales", handoff_to_sales)
    builder.add_node("enter_long_nurture", enter_long_nurture)

    builder.set_entry_point("send_welcome_email")

    builder.add_edge("send_welcome_email", "evaluate_engagement")

    builder.add_conditional_edges(
        "evaluate_engagement",
        route_next_touch,
        {
            "send_demo_offer": "send_demo_offer",
            "send_nurture_email": "send_nurture_email",
            "enter_long_nurture": "enter_long_nurture",
        },
    )

    builder.add_conditional_edges(
        "send_demo_offer",
        route_after_demo,
        {
            "handoff_to_sales": "handoff_to_sales",
            "send_nurture_email": "send_nurture_email",
        },
    )

    builder.add_edge("send_nurture_email", END)
    builder.add_edge("handoff_to_sales", END)
    builder.add_edge("enter_long_nurture", END)

    checkpointer = MemorySaver()
    compiled = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["handoff_to_sales"],
    )
    return compiled, checkpointer


# ---------------------------------------------------------------------------
# Sample contacts with engagement archetypes
# ---------------------------------------------------------------------------

SAMPLE_CONTACTS: list[dict[str, Any]] = [
    {
        "contact_id": "contact-high-001",
        "email": "sarah.chen@acmesaas.com",
        "first_name": "Sarah",
        "description": "High-engagement VP of Marketing — opens every email, "
                       "visits pricing page, attends webinars.",
    },
    {
        "contact_id": "contact-mid-002",
        "email": "james.wilson@mediaco.io",
        "first_name": "James",
        "description": "Medium-engagement Marketing Manager — opens some emails, "
                       "downloaded one whitepaper.",
    },
    {
        "contact_id": "contact-low-003",
        "email": "pat.davis@bigcorp.com",
        "first_name": "Pat",
        "description": "Low-engagement subscriber — opened one email, minimal "
                       "site activity.",
    },
]


# ---------------------------------------------------------------------------
# Day-by-day simulation
# ---------------------------------------------------------------------------

def _should_run_on_day(day: int, last_action: str) -> bool:
    """Determine whether to invoke the graph on a given simulation day.

    We space touchpoints out to avoid overwhelming contacts:
        - Day 1  : always (welcome email)
        - Day 3  : first evaluation + nurture
        - Days 5, 8, 12, 16, 20, 25 : subsequent touchpoints
        - After handoff or long_nurture : stop
    """
    touchpoint_days = {1, 3, 5, 8, 12, 16, 20, 25}

    if last_action in ("handoff_to_sales", "enter_long_nurture"):
        return False

    return day in touchpoint_days


def simulate_contact_journey(
    contact: dict[str, Any],
    total_days: int = 30,
) -> dict[str, Any]:
    """Run a single contact through a simulated multi-day journey.

    Args:
        contact:    Contact info dict (contact_id, email, first_name, description).
        total_days: Number of days to simulate.

    Returns:
        Final ``JourneyState`` after the simulation completes.
    """
    graph, checkpointer = _build_graph()
    thread_id = f"sim-{contact['contact_id']}"
    config = {"configurable": {"thread_id": thread_id}}

    state: JourneyState = {
        "contact_id": contact["contact_id"],
        "email": contact["email"],
        "first_name": contact["first_name"],
        "engagement_score": 0,
        "touchpoints_sent": 0,
        "last_action": "",
        "channel_history": [],
        "qualified": False,
        "day": 1,
        "messages": [],
    }

    for day in range(1, total_days + 1):
        if not _should_run_on_day(day, state["last_action"]):
            continue

        state["day"] = day

        # Invoke the graph — it may be interrupted before handoff_to_sales
        result = graph.invoke(state, config=config)

        # Check for interrupt (HITL gate before handoff_to_sales)
        snapshot = graph.get_state(config)
        if snapshot.next and "handoff_to_sales" in snapshot.next:
            # Simulate human approval: resume the graph past the interrupt
            print(f"    [HITL] Day {day}: Sales handoff pending approval "
                  f"for {contact['first_name']}... APPROVED")
            result = graph.invoke(None, config=config)

        # Merge the result back into our running state
        state = {**state, **result}

    return state


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_journey_report(contact: dict[str, Any], final_state: dict[str, Any]) -> None:
    """Print a formatted timeline report for one contact's journey."""
    border = "=" * 70
    print(f"\n{border}")
    print(f"  JOURNEY REPORT: {contact['first_name']} ({contact['email']})")
    print(f"  Profile: {contact['description']}")
    print(border)
    print(f"  Contact ID       : {final_state['contact_id']}")
    print(f"  Engagement Score : {final_state['engagement_score']}")
    print(f"  Qualified        : {final_state['qualified']}")
    print(f"  Touchpoints Sent : {final_state['touchpoints_sent']}")
    print(f"  Last Action      : {final_state['last_action']}")
    print(f"  Channel History  : {', '.join(final_state['channel_history'])}")
    print(f"\n  Journey Timeline:")
    print(f"  {'-' * 62}")
    for i, msg in enumerate(final_state["messages"], 1):
        print(f"  {i:>3}. {msg}")
    print(f"  {'-' * 62}")

    # Outcome summary
    last = final_state["last_action"]
    if last == "handoff_to_sales":
        outcome = "SALES HANDOFF — contact handed off for direct outreach"
    elif last == "enter_long_nurture":
        outcome = "LONG NURTURE — contact moved to low-frequency track"
    elif last == "send_demo_offer":
        outcome = "DEMO OFFERED — awaiting response"
    else:
        outcome = "ACTIVE NURTURE — continuing email journey"
    print(f"\n  Outcome: {outcome}")
    print(border)


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

def run_full_simulation() -> None:
    """Execute the 30-day journey simulation for all sample contacts."""
    header = "=" * 70
    print(f"\n{header}")
    print("  ADAPTIVE CUSTOMER JOURNEY ORCHESTRATOR")
    print("  Project 5 — 30-Day Simulation")
    print(header)
    print(f"\n  Simulating {len(SAMPLE_CONTACTS)} contacts over 30 days...")
    print(f"  Touchpoint days: 1, 3, 5, 8, 12, 16, 20, 25")
    print(f"  HITL gate: handoff_to_sales requires approval")
    print()

    results: list[dict[str, Any]] = []

    for contact in SAMPLE_CONTACTS:
        print(f"\n  >>> Starting journey for {contact['first_name']} "
              f"({contact['contact_id']})")
        final_state = simulate_contact_journey(contact, total_days=30)
        results.append({"contact": contact, "final_state": final_state})
        print_journey_report(contact, final_state)

    # Summary table
    print(f"\n{header}")
    print("  SIMULATION SUMMARY")
    print(header)
    print(f"  {'Contact':<20} {'Score':>6} {'TPs':>4} {'Qualified':>10} {'Outcome':<25}")
    print(f"  {'-' * 67}")
    for r in results:
        c = r["contact"]
        s = r["final_state"]
        outcome = s["last_action"].replace("_", " ").title()
        print(
            f"  {c['first_name']:<20} "
            f"{s['engagement_score']:>6} "
            f"{s['touchpoints_sent']:>4} "
            f"{str(s['qualified']):>10} "
            f"{outcome:<25}"
        )
    print(f"  {'-' * 67}")
    print(f"\n  Simulation complete.\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_full_simulation()
