# File      : nodes.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Async node functions for the Decision-stage LangGraph.

Each function receives the current ``DecisionJourneyState`` and returns a
partial state dict that the graph merges back.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, SystemMessage

from stage3_decision.tools.objection_handler_tools import (
    generate_objection_response,
    get_common_objections,
)
from stage3_decision.tools.competitive_battlecard_tools import (
    get_battlecard,
    get_competitive_comparison,
)
from stage3_decision.tools.close_offer_tools import (
    create_urgency_campaign,
    generate_close_offer,
)
from stage3_decision.tools.deal_crm_tools import (
    get_deal,
    update_deal_stage,
    create_deal_task,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    """Return a compact UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _msg(text: str) -> AIMessage:
    """Wrap text in an AIMessage for the message log."""
    return AIMessage(content=text)


# ---------------------------------------------------------------------------
# Node: evaluate_decision_signals
# ---------------------------------------------------------------------------

async def evaluate_decision_signals(state: dict) -> dict:
    """Pull the latest CRM deal data and refresh signal fields.

    This is typically the *entry node* — it hydrates the state with fresh
    CRM information so downstream routing is accurate.
    """
    deal_id = state.get("deal_id", "")
    raw = get_deal(deal_id)
    deal_data: dict = json.loads(raw) if isinstance(raw, str) else raw

    intent = state.get("intent_score", 50)
    days = state.get("days_in_decision", 0)

    # Derive a simple intent bump when the proposal has been viewed
    if state.get("proposal_viewed") and intent < 85:
        intent = min(intent + 10, 100)

    summary = (
        f"[{_ts()}] Evaluated signals for deal {deal_id} "
        f"(company={state.get('company', 'N/A')}, "
        f"value=${state.get('deal_value', 0):,.0f}, "
        f"intent={intent}, days_in_decision={days})."
    )

    return {
        "intent_score": intent,
        "days_in_decision": days,
        "last_action": "evaluate_decision_signals",
        "messages": [_msg(summary)],
    }


# ---------------------------------------------------------------------------
# Node: generate_objection_response
# ---------------------------------------------------------------------------

async def handle_objections(state: dict) -> dict:
    """Address each objection the prospect has raised.

    Calls the objection-handler tools and appends the responses to the
    message log.
    """
    objections = state.get("objections_raised", [])
    company = state.get("company", "Unknown")
    product = "our platform"  # placeholder

    responses: list[str] = []
    for obj in objections:
        common = get_common_objections(company)
        reply = generate_objection_response(obj, product)
        responses.append(f"Objection: '{obj}' -> Response: {reply}")

    combined = "\n".join(responses) if responses else "No objections to address."
    summary = f"[{_ts()}] Objection handling complete for {company}.\n{combined}"

    update_deal_stage(state.get("deal_id", ""), "objection_addressed")

    return {
        "last_action": "address_objections",
        "next_action": "re_evaluate",
        "messages": [_msg(summary)],
    }


# ---------------------------------------------------------------------------
# Node: send_competitive_battlecard
# ---------------------------------------------------------------------------

async def send_competitive_battlecard(state: dict) -> dict:
    """Retrieve and dispatch competitive battle-cards for every named
    competitor."""
    competitors = state.get("competitors_named", [])
    company = state.get("company", "Unknown")

    cards: list[str] = []
    for comp in competitors:
        card = get_battlecard(comp)
        comparison = get_competitive_comparison(comp, "all")
        cards.append(f"--- {comp} ---\n{card}\n{comparison}")

    combined = "\n\n".join(cards) if cards else "No competitors to compare."
    summary = (
        f"[{_ts()}] Dispatched battle-cards for {company}: "
        f"{', '.join(competitors) if competitors else 'none'}.\n{combined}"
    )

    return {
        "last_action": "send_comparison_content",
        "next_action": "re_evaluate",
        "messages": [_msg(summary)],
    }


# ---------------------------------------------------------------------------
# Node: generate_and_send_close_offer
# ---------------------------------------------------------------------------

async def generate_and_send_close_offer(state: dict) -> dict:
    """Generate a closing offer tailored to deal value and pricing tier."""
    deal_value = state.get("deal_value", 0.0)
    tier = state.get("pricing_tier_viewed", "standard")
    deal_id = state.get("deal_id", "")
    company = state.get("company", "Unknown")

    offer = generate_close_offer(deal_value, tier)

    update_deal_stage(deal_id, "close_offer_sent")
    create_deal_task(
        deal_id,
        title=f"Follow up on close offer for {company}",
        owner="sales-rep",
    )

    summary = (
        f"[{_ts()}] Close offer generated for {company} "
        f"(deal_value=${deal_value:,.0f}, tier={tier}).\n{offer}"
    )

    return {
        "last_action": "send_close_offer",
        "next_action": "await_response",
        "messages": [_msg(summary)],
    }


# ---------------------------------------------------------------------------
# Node: send_urgency_reactivation
# ---------------------------------------------------------------------------

async def send_urgency_reactivation(state: dict) -> dict:
    """Trigger an urgency / reactivation campaign for a stalled deal."""
    contact_id = state.get("contact_id", "")
    days = state.get("days_in_decision", 0)
    company = state.get("company", "Unknown")

    campaign = create_urgency_campaign(contact_id, days)
    update_deal_stage(state.get("deal_id", ""), "reactivation_sent")

    summary = (
        f"[{_ts()}] Urgency reactivation sent for {company} "
        f"(stalled {days} days).\n{campaign}"
    )

    return {
        "last_action": "reactivate_with_urgency",
        "next_action": "re_evaluate",
        "messages": [_msg(summary)],
    }


# ---------------------------------------------------------------------------
# Node: pause_for_human_review (interrupt_before)
# ---------------------------------------------------------------------------

async def pause_for_human_review(state: dict) -> dict:
    """Gate node for high-value deals.

    LangGraph's ``interrupt_before`` on this node pauses execution until
    a human approves the proposed action.
    """
    deal_id = state.get("deal_id", "")
    company = state.get("company", "Unknown")
    deal_value = state.get("deal_value", 0.0)

    create_deal_task(
        deal_id,
        title=f"REVIEW REQUIRED: approve close action for {company} (${deal_value:,.0f})",
        owner="sales-manager",
    )

    summary = (
        f"[{_ts()}] Human review requested for deal {deal_id} "
        f"({company}, ${deal_value:,.0f}). Execution paused."
    )

    return {
        "last_action": "request_human_approval",
        "human_approved": True,  # set after human resumes
        "messages": [_msg(summary)],
    }


# ---------------------------------------------------------------------------
# Node: continue_standard_nurture
# ---------------------------------------------------------------------------

async def continue_standard_nurture(state: dict) -> dict:
    """Default path — send the next piece of decision-stage nurture content."""
    company = state.get("company", "Unknown")
    intent = state.get("intent_score", 0)

    if intent >= 70:
        content_type = "case study + ROI calculator"
    elif intent >= 50:
        content_type = "product comparison guide"
    else:
        content_type = "educational webinar invite"

    summary = (
        f"[{_ts()}] Standard nurture sent to {company}: {content_type} "
        f"(intent={intent})."
    )

    return {
        "last_action": "send_next_nurture",
        "next_action": "re_evaluate",
        "messages": [_msg(summary)],
    }
