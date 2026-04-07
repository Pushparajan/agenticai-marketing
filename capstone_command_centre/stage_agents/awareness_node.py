# File      : awareness_node.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Stage 1 — Awareness node for the Capstone Command Centre.

Wraps the discovery + triage logic from the OpenAI Agents SDK stage.
Scores intent signals via the CDP, looks up / creates the CRM contact,
and proposes a routing action (accelerate | nurture | cold-park).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from capstone_command_centre.mcp_client import get_tool

logger = logging.getLogger(__name__)

STAGE = "awareness"


# ---------------------------------------------------------------------------
# Helper — route based on intent tier
# ---------------------------------------------------------------------------

def _decide_route(intent_score: int, tier: str) -> dict[str, Any]:
    """Return the proposed next action based on intent tier."""
    if tier == "high":
        return {
            "action": "accelerate_to_consideration",
            "description": "High-intent lead — fast-track to Stage 2 nurture.",
            "urgency": "high",
            "suggested_spend": 0,
        }
    if tier == "mid":
        return {
            "action": "enrol_nurture_sequence",
            "description": "Mid-intent lead — enrol in awareness drip campaign.",
            "urgency": "medium",
            "suggested_spend": 0,
        }
    return {
        "action": "cold_park",
        "description": "Low-intent — park and monitor for re-engagement signals.",
        "urgency": "low",
        "suggested_spend": 0,
    }


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------

def awareness_node(state: dict[str, Any]) -> dict[str, Any]:
    """Execute Stage 1 awareness logic and return a partial state update.

    Reads ``contact_email`` from state.  Returns keys:
    ``stage_results.awareness`` with contact info, intent score, and
    proposed action.
    """
    email = state.get("contact_email", "unknown@example.com")
    logger.info("[Awareness] Processing %s", email)

    # ---- 1. Score intent via CDP ----
    compute_intent = get_tool("cdp_server", "compute_intent_score", stage=STAGE)
    intent_data = compute_intent(email=email)
    intent_score = intent_data.get("intent_score", 0)
    tier = intent_data.get("tier", "cold")

    # ---- 2. Fetch behavioural events from CDP ----
    get_events = get_tool("cdp_server", "get_contact_events", stage=STAGE)
    events_data = get_events(email=email)

    # ---- 3. Look up or create CRM contact ----
    get_contact = get_tool("crm_server", "get_contact", stage=STAGE)
    contact = get_contact(email=email)

    if not contact.get("found"):
        create_contact = get_tool("crm_server", "create_contact", stage=STAGE)
        contact = create_contact(
            email=email,
            firstname=state.get("firstname", "Unknown"),
            lastname=state.get("lastname", "Lead"),
            company=state.get("company", ""),
            source="capstone_awareness",
        )

    contact_id = contact.get("contact_id", "")

    # ---- 4. Log journey event ----
    log_event = get_tool("crm_server", "log_journey_event", stage=STAGE)
    log_event(contact_id=contact_id, event="awareness_scored")

    # ---- 5. Build proposed action ----
    route = _decide_route(intent_score, tier)

    result = {
        "stage": STAGE,
        "contact_id": contact_id,
        "email": email,
        "intent_score": intent_score,
        "intent_tier": tier,
        "events_count": len(events_data.get("events", [])),
        "proposed_action": route,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("[Awareness] %s  score=%d  tier=%s  action=%s",
                email, intent_score, tier, route["action"])

    # Return partial state update
    existing = dict(state.get("stage_results", {}))
    existing[STAGE] = result
    return {"stage_results": existing}
