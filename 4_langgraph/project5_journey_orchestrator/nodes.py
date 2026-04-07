# nodes.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: Graph node functions that transform JourneyState
# Author: Pushparajan Ramar

"""Node functions for the customer journey orchestration graph.

Each node accepts the full *JourneyState* and returns a **partial** state
dictionary.  LangGraph merges these partial updates into the shared state
automatically.  Nodes delegate to the underlying tool modules in
``tools/`` for API interaction, keeping orchestration logic cleanly
separated from I/O.
"""

from __future__ import annotations

import logging
from typing import Any

from state import JourneyState
from tools.crm_tools import (
    handoff_to_sales as _crm_handoff,
    update_lifecycle_stage as _crm_update_stage,
)
from tools.email_tools import (
    send_demo_offer as _email_demo,
    send_nurture_email as _email_nurture,
    send_welcome_email as _email_welcome,
)
from tools.engagement_tools import evaluate_engagement as _eval_engagement

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _contact_dict(state: JourneyState) -> dict[str, Any]:
    """Extract the contact subset from state for tool calls."""
    return {
        "contact_id": state["contact_id"],
        "email": state["email"],
        "first_name": state["first_name"],
    }


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def evaluate_engagement(state: JourneyState) -> dict[str, Any]:
    """Fetch engagement signals and update the engagement score.

    Calls the CDP/CRM engagement tool, then sets the composite score and
    marks the contact as *qualified* when the score reaches 80 or above.
    """
    contact_id = state["contact_id"]
    day = state["day"]

    log.info("[Day %d] evaluate_engagement  contact=%s", day, contact_id)
    signals = _eval_engagement(contact_id)
    score = signals.get("engagement_score", 0)

    message = (
        f"Day {day}: Evaluated engagement — score={score}, "
        f"opens={signals.get('email_opens', 0)}, "
        f"page_views={signals.get('page_views', 0)}, "
        f"forms={signals.get('form_fills', 0)}"
    )
    log.info(message)

    return {
        "engagement_score": score,
        "qualified": score >= 80,
        "last_action": "evaluate_engagement",
        "messages": state["messages"] + [message],
    }


def send_welcome_email(state: JourneyState) -> dict[str, Any]:
    """Send a welcome email and record it in channel history.

    Intended for the very first touchpoint with a new contact.
    """
    day = state["day"]
    contact = _contact_dict(state)

    log.info("[Day %d] send_welcome_email  contact=%s", day, state["contact_id"])
    result = _email_welcome(contact)

    message = (
        f"Day {day}: Sent welcome email to {state['email']} — "
        f"status={result.get('status', 'UNKNOWN')}"
    )
    log.info(message)

    return {
        "touchpoints_sent": state["touchpoints_sent"] + 1,
        "last_action": "send_welcome_email",
        "channel_history": state["channel_history"] + ["email_welcome"],
        "messages": state["messages"] + [message],
    }


def send_nurture_email(state: JourneyState) -> dict[str, Any]:
    """Send a nurture email with content type based on engagement score.

    Content type selection:
        - score >= 60 : "roi_report"
        - score >= 40 : "case_study"
        - score >= 20 : "educational"
        - else        : "product_update"
    """
    day = state["day"]
    score = state["engagement_score"]
    contact = _contact_dict(state)

    if score >= 60:
        content_type = "roi_report"
    elif score >= 40:
        content_type = "case_study"
    elif score >= 20:
        content_type = "educational"
    else:
        content_type = "product_update"

    log.info(
        "[Day %d] send_nurture_email  contact=%s  content_type=%s  score=%d",
        day, state["contact_id"], content_type, score,
    )
    result = _email_nurture(contact, content_type)

    message = (
        f"Day {day}: Sent nurture email ({content_type}) to {state['email']} — "
        f"status={result.get('status', 'UNKNOWN')}"
    )
    log.info(message)

    return {
        "touchpoints_sent": state["touchpoints_sent"] + 1,
        "last_action": "send_nurture_email",
        "channel_history": state["channel_history"] + [f"email_nurture_{content_type}"],
        "messages": state["messages"] + [message],
    }


def send_demo_offer(state: JourneyState) -> dict[str, Any]:
    """Send a demo offer to a high-engagement lead.

    This node fires when the engagement score crosses the 80-point
    threshold, indicating strong buying intent.
    """
    day = state["day"]
    contact = _contact_dict(state)

    log.info(
        "[Day %d] send_demo_offer  contact=%s  score=%d",
        day, state["contact_id"], state["engagement_score"],
    )
    result = _email_demo(contact)

    # Also update lifecycle stage to reflect marketing qualification
    _crm_update_stage(state["contact_id"], "marketingqualifiedlead")

    message = (
        f"Day {day}: Sent demo offer to {state['email']} (score={state['engagement_score']}) — "
        f"status={result.get('status', 'UNKNOWN')}"
    )
    log.info(message)

    return {
        "touchpoints_sent": state["touchpoints_sent"] + 1,
        "last_action": "send_demo_offer",
        "channel_history": state["channel_history"] + ["demo_offer"],
        "qualified": True,
        "messages": state["messages"] + [message],
    }


def handoff_to_sales(state: JourneyState) -> dict[str, Any]:
    """Hand off a qualified contact to the sales team.

    This is the human-in-the-loop (HITL) interrupt point.  In production,
    the graph pauses here for human approval before the handoff executes.
    """
    day = state["day"]
    contact_id = state["contact_id"]

    # Build a context summary from the journey so far
    journey_summary = (
        f"Contact: {state['first_name']} ({state['email']})\n"
        f"Engagement score: {state['engagement_score']}\n"
        f"Touchpoints sent: {state['touchpoints_sent']}\n"
        f"Channel history: {', '.join(state['channel_history'])}\n"
        f"Journey day: {day}"
    )

    log.info("[Day %d] handoff_to_sales  contact=%s", day, contact_id)
    result = _crm_handoff(contact_id, journey_summary)

    message = (
        f"Day {day}: Sales handoff for {state['email']} — "
        f"handoff_id={result.get('handoff_id', 'N/A')}, "
        f"status={result.get('status', 'UNKNOWN')}"
    )
    log.info(message)

    return {
        "last_action": "handoff_to_sales",
        "channel_history": state["channel_history"] + ["sales_handoff"],
        "messages": state["messages"] + [message],
    }


def enter_long_nurture(state: JourneyState) -> dict[str, Any]:
    """Move the contact into a low-frequency long-term nurture track.

    This node fires for contacts whose engagement remains low after
    multiple touchpoints, reducing email fatigue while keeping the
    relationship warm.
    """
    day = state["day"]
    contact_id = state["contact_id"]

    log.info(
        "[Day %d] enter_long_nurture  contact=%s  score=%d  touchpoints=%d",
        day, contact_id, state["engagement_score"], state["touchpoints_sent"],
    )

    # Update lifecycle to reflect long-nurture status
    _crm_update_stage(contact_id, "lead")

    message = (
        f"Day {day}: Moved {state['email']} to long-term nurture track "
        f"(score={state['engagement_score']}, touchpoints={state['touchpoints_sent']})"
    )
    log.info(message)

    return {
        "last_action": "enter_long_nurture",
        "channel_history": state["channel_history"] + ["long_nurture"],
        "messages": state["messages"] + [message],
    }
