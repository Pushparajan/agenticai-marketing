# graph.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: LangGraph StateGraph assembly with checkpointing and HITL interrupt
# Author: Pushparajan Ramar

"""LangGraph state-graph definition for the adaptive customer journey.

Assembles all nodes and conditional routing edges into a compiled
``StateGraph``.  Key features:

* **MemorySaver checkpointer** — persists state between invocations so
  the journey can resume across multiple simulation days.
* **Interrupt before handoff_to_sales** — implements a human-in-the-loop
  gate so a sales manager can approve (or reject) the handoff before it
  executes.
* Conditional edges that fan out from *evaluate_engagement* and
  *send_demo_offer* via the routing functions in ``routing.py``.

Usage:
    >>> from graph import journey_graph
    >>> result = journey_graph.invoke(initial_state, config={"configurable": {"thread_id": "abc"}})
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from nodes import (
    enter_long_nurture,
    evaluate_engagement,
    handoff_to_sales,
    route_entry,
    send_demo_offer,
    send_nurture_email,
    send_welcome_email,
)
from routing import route_after_demo, route_entry as route_entry_fn, route_next_touch
from state import JourneyState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_journey_graph() -> StateGraph:
    """Construct and compile the adaptive customer journey graph.

    Graph topology::

        START
          |
        route_entry (conditional)
          +---> send_welcome_email ---> evaluate_engagement
          +---> evaluate_engagement (directly, on re-entry)
          |
        evaluate_engagement (conditional)
          +---> send_nurture_email ---> END
          +---> send_demo_offer ------> (conditional)
          |                               +---> handoff_to_sales ---> END
          |                               +---> send_nurture_email -> END
          +---> enter_long_nurture ---> END

    Returns:
        A compiled ``StateGraph`` with a MemorySaver checkpointer and
        interrupt-before on *handoff_to_sales*.
    """
    # -- define the graph --
    builder = StateGraph(JourneyState)

    # -- add nodes --
    builder.add_node("route_entry", route_entry)
    builder.add_node("send_welcome_email", send_welcome_email)
    builder.add_node("evaluate_engagement", evaluate_engagement)
    builder.add_node("send_nurture_email", send_nurture_email)
    builder.add_node("send_demo_offer", send_demo_offer)
    builder.add_node("handoff_to_sales", handoff_to_sales)
    builder.add_node("enter_long_nurture", enter_long_nurture)

    # -- entry point --
    builder.set_entry_point("route_entry")

    # -- edges --
    # Entry router: welcome on first touch, evaluate on re-entry
    builder.add_conditional_edges(
        "route_entry",
        route_entry_fn,
        {
            "send_welcome_email": "send_welcome_email",
            "evaluate_engagement": "evaluate_engagement",
        },
    )

    # After welcome, always evaluate engagement
    builder.add_edge("send_welcome_email", "evaluate_engagement")

    # After evaluation, route based on engagement score
    builder.add_conditional_edges(
        "evaluate_engagement",
        route_next_touch,
        {
            "send_demo_offer": "send_demo_offer",
            "send_nurture_email": "send_nurture_email",
            "enter_long_nurture": "enter_long_nurture",
        },
    )

    # After demo offer, route to handoff or back to nurture
    builder.add_conditional_edges(
        "send_demo_offer",
        route_after_demo,
        {
            "handoff_to_sales": "handoff_to_sales",
            "send_nurture_email": "send_nurture_email",
        },
    )

    # Terminal edges — each of these ends the current invocation
    builder.add_edge("send_nurture_email", END)
    builder.add_edge("handoff_to_sales", END)
    builder.add_edge("enter_long_nurture", END)

    # -- compile with checkpointer and HITL interrupt --
    checkpointer = MemorySaver()
    compiled = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["handoff_to_sales"],
    )

    log.info("Journey graph compiled  nodes=%d  interrupt_before=[handoff_to_sales]", 7)
    return compiled


# ---------------------------------------------------------------------------
# Module-level compiled graph (importable singleton)
# ---------------------------------------------------------------------------

journey_graph = build_journey_graph()


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Journey Graph — Compiled Successfully")
    print("=" * 60)

    # Print graph structure
    print("\nGraph nodes:")
    for node_name in [
        "route_entry",
        "send_welcome_email",
        "evaluate_engagement",
        "send_nurture_email",
        "send_demo_offer",
        "handoff_to_sales",
        "enter_long_nurture",
    ]:
        print(f"  - {node_name}")

    print("\nConditional routing:")
    print("  evaluate_engagement -> route_next_touch")
    print("    score >= 80           : send_demo_offer")
    print("    score >= 50           : send_nurture_email")
    print("    score < 50, tp > 5    : enter_long_nurture")
    print("    else                  : send_nurture_email")
    print("  send_demo_offer -> route_after_demo")
    print("    qualified & score>=80 : handoff_to_sales")
    print("    else                  : send_nurture_email")

    print("\nInterrupt before: handoff_to_sales (HITL gate)")
    print("\nCheckpointer: MemorySaver (in-memory state persistence)")

    # Quick smoke test
    print("\n" + "=" * 60)
    print("Smoke Test — High Engagement Contact")
    print("=" * 60)
    initial_state: JourneyState = {
        "contact_id": "contact-high-001",
        "email": "sarah@acme.com",
        "first_name": "Sarah",
        "engagement_score": 0,
        "touchpoints_sent": 0,
        "last_action": "",
        "channel_history": [],
        "qualified": False,
        "day": 1,
        "messages": [],
    }
    config = {"configurable": {"thread_id": "smoke-test-001"}}
    result = journey_graph.invoke(initial_state, config=config)
    print(f"\nFinal state:")
    print(f"  engagement_score = {result['engagement_score']}")
    print(f"  qualified        = {result['qualified']}")
    print(f"  last_action      = {result['last_action']}")
    print(f"  touchpoints_sent = {result['touchpoints_sent']}")
    print(f"  channel_history  = {result['channel_history']}")
    print(f"\nJourney log:")
    for msg in result["messages"]:
        print(f"  {msg}")
