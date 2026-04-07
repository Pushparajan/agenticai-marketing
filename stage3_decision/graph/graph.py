# File      : graph.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Assembles the Decision-stage LangGraph ``StateGraph``.

Topology
--------
    START
      |
    evaluate_decision_signals
      |
    route_decision_action  (conditional edge)
      |--- request_human_approval  (interrupt_before)
      |--- send_close_offer
      |--- address_objections
      |--- send_comparison_content
      |--- reactivate_with_urgency
      |--- send_next_nurture
      |
    END

All action nodes terminate at END so the caller can inspect state and
optionally re-invoke the graph for the next cycle.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from stage3_decision.graph.state import DecisionJourneyState
from stage3_decision.graph.nodes import (
    continue_standard_nurture,
    evaluate_decision_signals,
    generate_and_send_close_offer,
    handle_objections,
    pause_for_human_review,
    send_competitive_battlecard,
    send_urgency_reactivation,
)
from stage3_decision.graph.routing import route_decision_action


def build_decision_graph() -> StateGraph:
    """Construct and return the compiled Decision-stage graph.

    Returns
    -------
    CompiledGraph
        A compiled LangGraph ready for ``.ainvoke()`` / ``.astream()``.
    """
    builder = StateGraph(DecisionJourneyState)

    # -- Register nodes ------------------------------------------------
    builder.add_node("evaluate_decision_signals", evaluate_decision_signals)
    builder.add_node("request_human_approval", pause_for_human_review)
    builder.add_node("send_close_offer", generate_and_send_close_offer)
    builder.add_node("address_objections", handle_objections)
    builder.add_node("send_comparison_content", send_competitive_battlecard)
    builder.add_node("reactivate_with_urgency", send_urgency_reactivation)
    builder.add_node("send_next_nurture", continue_standard_nurture)

    # -- Entry ---------------------------------------------------------
    builder.set_entry_point("evaluate_decision_signals")

    # -- Conditional routing after signal evaluation -------------------
    builder.add_conditional_edges(
        "evaluate_decision_signals",
        route_decision_action,
        {
            "request_human_approval": "request_human_approval",
            "send_close_offer": "send_close_offer",
            "address_objections": "address_objections",
            "send_comparison_content": "send_comparison_content",
            "reactivate_with_urgency": "reactivate_with_urgency",
            "send_next_nurture": "send_next_nurture",
        },
    )

    # -- Terminal edges ------------------------------------------------
    builder.add_edge("request_human_approval", END)
    builder.add_edge("send_close_offer", END)
    builder.add_edge("address_objections", END)
    builder.add_edge("send_comparison_content", END)
    builder.add_edge("reactivate_with_urgency", END)
    builder.add_edge("send_next_nurture", END)

    # -- Compile with checkpointer & interrupt -------------------------
    memory = MemorySaver()
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=["request_human_approval"],
    )
    return graph
