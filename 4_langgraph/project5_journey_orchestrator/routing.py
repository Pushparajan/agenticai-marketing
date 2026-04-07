# routing.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: Conditional edge routing functions for the journey graph
# Author: Pushparajan Ramar

"""Conditional routing logic for the customer journey state graph.

These functions are passed to ``add_conditional_edges`` and return the
**name** of the next node the graph should visit.  Routing decisions are
based on the contact's current engagement score, touchpoint count, and
qualification status.
"""

from __future__ import annotations

import logging

from state import JourneyState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


def route_next_touch(state: JourneyState) -> str:
    """Route from engagement evaluation to the appropriate next touchpoint.

    Decision matrix:
        - engagement_score >= 80           -> "send_demo_offer"
        - engagement_score >= 50           -> "send_nurture_email"
        - engagement_score < 50 AND
          touchpoints_sent > 5             -> "enter_long_nurture"
        - else (score < 50, early journey) -> "send_nurture_email"

    Args:
        state: Current journey state.

    Returns:
        Node name for the next step in the graph.
    """
    score = state["engagement_score"]
    touchpoints = state["touchpoints_sent"]

    if score >= 80:
        decision = "send_demo_offer"
    elif score >= 50:
        decision = "send_nurture_email"
    elif touchpoints > 5:
        decision = "enter_long_nurture"
    else:
        decision = "send_nurture_email"

    log.info(
        "route_next_touch  contact=%s  score=%d  touchpoints=%d  -> %s",
        state["contact_id"], score, touchpoints, decision,
    )
    return decision


def route_after_demo(state: JourneyState) -> str:
    """Route after a demo offer has been sent.

    If the contact is qualified (score >= 80 and marked qualified), proceed
    to a sales handoff.  Otherwise, continue nurturing.

    Args:
        state: Current journey state.

    Returns:
        Node name: "handoff_to_sales" or "send_nurture_email".
    """
    score = state["engagement_score"]
    qualified = state.get("qualified", False)

    if qualified and score >= 80:
        decision = "handoff_to_sales"
    else:
        decision = "send_nurture_email"

    log.info(
        "route_after_demo  contact=%s  score=%d  qualified=%s  -> %s",
        state["contact_id"], score, qualified, decision,
    )
    return decision
