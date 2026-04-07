# File      : decision_node.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Stage 3 — Decision node for the Capstone Command Centre.

Wraps the LangGraph conversion-graph logic.  Evaluates deal health,
proposes closing actions (urgency offer, battlecard, objection handling),
and creates follow-up tasks in the CRM.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from capstone_command_centre.mcp_client import get_tool

logger = logging.getLogger(__name__)

STAGE = "decision"


# ---------------------------------------------------------------------------
# Helper — deal health assessment
# ---------------------------------------------------------------------------

def _assess_deal(deal: dict[str, Any], flow_perf: dict[str, Any]) -> dict[str, Any]:
    """Evaluate deal health and propose a closing action."""
    probability = deal.get("probability", 0)
    days_open = deal.get("days_open", 0)
    value = deal.get("value", 0)
    ctr = flow_perf.get("ctr", 0)

    # High probability, engaged — send proposal follow-up
    if probability >= 0.7 and days_open <= 14:
        return {
            "action": "send_proposal_followup",
            "description": (
                f"Deal at {probability:.0%} probability, {days_open}d open. "
                "Send personalised proposal follow-up with case study."
            ),
            "urgency": "high",
            "suggested_spend": 0,
        }

    # Stalling deal — offer time-limited incentive
    if days_open > 14 and probability >= 0.4:
        spend = min(value * 0.05, 500)  # Up to 5% or £500 cap
        return {
            "action": "urgency_incentive",
            "description": (
                f"Deal stalling ({days_open}d). Offer time-limited discount "
                f"or bonus (budget: £{spend:.0f})."
            ),
            "urgency": "high",
            "suggested_spend": spend,
        }

    # Low engagement — deploy battlecard and objection handler
    if ctr < 0.10 or probability < 0.4:
        return {
            "action": "deploy_battlecard",
            "description": (
                "Low engagement / probability. Deploy competitive battlecard "
                "and schedule objection-handling call."
            ),
            "urgency": "medium",
            "suggested_spend": 0,
        }

    return {
        "action": "monitor",
        "description": "Deal progressing normally — continue monitoring.",
        "urgency": "low",
        "suggested_spend": 0,
    }


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------

def decision_node(state: dict[str, Any]) -> dict[str, Any]:
    """Execute Stage 3 decision logic and return a partial state update.

    Reads ``deal_id`` and ``contact_email`` from state.  Returns
    ``stage_results.decision`` with deal assessment and proposed action.
    """
    email = state.get("contact_email", "unknown@example.com")
    contact_id = state.get("contact_id", "C-1001")
    deal_id = state.get("deal_id", "D-5001")
    logger.info("[Decision] Processing deal %s for %s", deal_id, email)

    # ---- 1. Fetch deal from CRM ----
    get_deal = get_tool("crm_server", "get_deal", stage=STAGE)
    deal = get_deal(deal_id=deal_id)

    # ---- 2. Get email engagement for decision-stage flow ----
    get_flow = get_tool("email_server", "get_flow_performance", stage=STAGE)
    flow_perf = get_flow(flow_id="decision_close_v1")

    # ---- 3. Assess deal and build proposed action ----
    proposed = _assess_deal(deal, flow_perf)

    # ---- 4. Create CRM follow-up task ----
    create_task = get_tool("crm_server", "create_task", stage=STAGE)
    task = create_task(
        contact_id=contact_id,
        title=f"[Decision] {proposed['action']} for {email}",
    )

    # ---- 5. Log journey event ----
    log_event = get_tool("crm_server", "log_journey_event", stage=STAGE)
    log_event(contact_id=contact_id, event=f"decision_{proposed['action']}")

    result = {
        "stage": STAGE,
        "contact_id": contact_id,
        "email": email,
        "deal_id": deal_id,
        "deal_value": deal.get("value", 0),
        "deal_probability": deal.get("probability", 0),
        "days_open": deal.get("days_open", 0),
        "task_id": task.get("task_id", ""),
        "proposed_action": proposed,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("[Decision] %s  deal=%s  action=%s",
                email, deal_id, proposed["action"])

    existing = dict(state.get("stage_results", {}))
    existing[STAGE] = result
    return {"stage_results": existing}
