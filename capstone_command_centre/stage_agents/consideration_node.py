# File      : consideration_node.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Stage 2 — Consideration node for the Capstone Command Centre.

Wraps the CrewAI campaign-intelligence crew logic.  Evaluates email-flow
performance, proposes nurture enrolment, and checks A/B test winners
to optimise engagement.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from capstone_command_centre.mcp_client import get_tool

logger = logging.getLogger(__name__)

STAGE = "consideration"


# ---------------------------------------------------------------------------
# Helper — build nurture recommendation
# ---------------------------------------------------------------------------

def _nurture_recommendation(
    flow_perf: dict[str, Any],
    ab_results: dict[str, Any],
    send_time: dict[str, Any],
) -> dict[str, Any]:
    """Synthesise nurture recommendations from email analytics."""
    open_rate = flow_perf.get("open_rate", 0)
    ctr = flow_perf.get("ctr", 0)
    winner = ab_results.get("winner", "variant_a")
    optimal_hour = send_time.get("optimal_hour_utc", 10)

    if open_rate >= 0.30 and ctr >= 0.10:
        strategy = "continue_current_flow"
        description = (
            f"Flow performing well (OR={open_rate:.0%}, CTR={ctr:.0%}). "
            f"Use winning variant '{winner}', send at {optimal_hour}:00 UTC."
        )
    elif open_rate >= 0.20:
        strategy = "optimise_subject_lines"
        description = (
            f"Opens decent (OR={open_rate:.0%}) but clicks low (CTR={ctr:.0%}). "
            f"Deploy winner '{winner}' and refresh CTA copy."
        )
    else:
        strategy = "rebuild_flow"
        description = (
            f"Underperforming flow (OR={open_rate:.0%}, CTR={ctr:.0%}). "
            "Recommend rebuilding nurture sequence with new creative."
        )

    return {
        "action": strategy,
        "description": description,
        "urgency": "medium",
        "suggested_spend": 0,
    }


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------

def consideration_node(state: dict[str, Any]) -> dict[str, Any]:
    """Execute Stage 2 consideration logic and return a partial state update.

    Reads ``contact_email`` from state.  Returns keys:
    ``stage_results.consideration`` with flow performance, A/B test
    results, and proposed nurture action.
    """
    email = state.get("contact_email", "unknown@example.com")
    contact_id = state.get("contact_id", "C-1001")
    logger.info("[Consideration] Processing %s", email)

    # ---- 1. Get current nurture flow performance ----
    get_flow = get_tool("email_server", "get_flow_performance", stage=STAGE)
    flow_perf = get_flow(flow_id="nurture_v2")

    # ---- 2. Check latest A/B test results ----
    get_ab = get_tool("email_server", "get_ab_test_results", stage=STAGE)
    ab_results = get_ab(test_id="ab_subject_consideration")

    # ---- 3. Compute optimal send time ----
    optimise = get_tool("email_server", "optimise_send_time", stage=STAGE)
    send_time = optimise(contact_id=contact_id)

    # ---- 4. Enrol contact in winning flow ----
    enrol = get_tool("email_server", "enrol_contact", stage=STAGE)
    enrol_result = enrol(contact_id=contact_id, flow_id="nurture_v2")

    # ---- 5. Update CRM lifecycle stage ----
    update_stage = get_tool("crm_server", "update_lifecycle_stage", stage=STAGE)
    update_stage(contact_id=contact_id, stage="lead")

    # ---- 6. Log journey event ----
    log_event = get_tool("crm_server", "log_journey_event", stage=STAGE)
    log_event(contact_id=contact_id, event="consideration_nurture_enrolled")

    # ---- 7. Build proposed action ----
    proposed = _nurture_recommendation(flow_perf, ab_results, send_time)

    result = {
        "stage": STAGE,
        "contact_id": contact_id,
        "email": email,
        "flow_performance": {
            "open_rate": flow_perf.get("open_rate", 0),
            "ctr": flow_perf.get("ctr", 0),
            "sent": flow_perf.get("sent", 0),
        },
        "ab_winner": ab_results.get("winner", "unknown"),
        "optimal_send_hour_utc": send_time.get("optimal_hour_utc", 10),
        "enrolled": enrol_result.get("enrolled", False),
        "proposed_action": proposed,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("[Consideration] %s  strategy=%s", email, proposed["action"])

    existing = dict(state.get("stage_results", {}))
    existing[STAGE] = result
    return {"stage_results": existing}
