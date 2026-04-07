# File      : onboarding_node.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Stage 4 — Onboarding node for the Capstone Command Centre.

Wraps the AutoGen onboarding-room logic.  Measures time-to-value,
checks activation milestones, and proposes intervention if the new
customer is falling behind the benchmark.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from capstone_command_centre.mcp_client import get_tool

logger = logging.getLogger(__name__)

STAGE = "onboarding"


# ---------------------------------------------------------------------------
# Helper — activation assessment
# ---------------------------------------------------------------------------

def _assess_activation(
    ttv: dict[str, Any],
    conversion_rates: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate onboarding progress and propose next steps."""
    days = ttv.get("days_to_value", 0)
    benchmark = ttv.get("benchmark", 14)
    onboarding_rate = conversion_rates.get("onboarding", 0.88)

    if days <= benchmark * 0.5:
        return {
            "action": "celebrate_fast_activation",
            "description": (
                f"Customer achieved value in {days}d (benchmark {benchmark}d). "
                "Send congratulations and upsell introduction."
            ),
            "urgency": "low",
            "suggested_spend": 0,
        }

    if days <= benchmark:
        return {
            "action": "continue_onboarding_plan",
            "description": (
                f"On track — {days}d vs {benchmark}d benchmark. "
                "Continue scheduled onboarding touchpoints."
            ),
            "urgency": "low",
            "suggested_spend": 0,
        }

    # Behind benchmark
    return {
        "action": "escalate_onboarding_support",
        "description": (
            f"Behind schedule — {days}d vs {benchmark}d benchmark. "
            "Assign dedicated CSM and schedule hands-on session."
        ),
        "urgency": "high",
        "suggested_spend": 0,
    }


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------

def onboarding_node(state: dict[str, Any]) -> dict[str, Any]:
    """Execute Stage 4 onboarding logic and return a partial state update.

    Reads ``contact_email`` from state.  Returns
    ``stage_results.onboarding`` with activation metrics and proposed
    action.
    """
    email = state.get("contact_email", "unknown@example.com")
    contact_id = state.get("contact_id", "C-1001")
    logger.info("[Onboarding] Processing %s", email)

    # ---- 1. Check time-to-value via Analytics ----
    get_ttv = get_tool("analytics_server", "get_time_to_value", stage=STAGE)
    ttv = get_ttv(contact_id=contact_id)

    # ---- 2. Get onboarding conversion rates ----
    get_rates = get_tool("analytics_server", "get_stage_conversion_rates",
                         stage=STAGE)
    rates = get_rates()

    # ---- 3. Update CRM lifecycle stage ----
    update = get_tool("crm_server", "update_lifecycle_stage", stage=STAGE)
    update(contact_id=contact_id, stage="customer")

    # ---- 4. Create onboarding task in CRM ----
    create_task = get_tool("crm_server", "create_task", stage=STAGE)
    task = create_task(
        contact_id=contact_id,
        title=f"[Onboarding] Review activation for {email}",
    )

    # ---- 5. Log journey event ----
    log_event = get_tool("crm_server", "log_journey_event", stage=STAGE)
    log_event(contact_id=contact_id, event="onboarding_review")

    # ---- 6. Assess activation ----
    proposed = _assess_activation(ttv, rates)

    result = {
        "stage": STAGE,
        "contact_id": contact_id,
        "email": email,
        "days_to_value": ttv.get("days_to_value", 0),
        "benchmark_days": ttv.get("benchmark", 14),
        "onboarding_conversion": rates.get("onboarding", 0),
        "task_id": task.get("task_id", ""),
        "proposed_action": proposed,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("[Onboarding] %s  TTV=%dd  action=%s",
                email, ttv.get("days_to_value", 0), proposed["action"])

    existing = dict(state.get("stage_results", {}))
    existing[STAGE] = result
    return {"stage_results": existing}
