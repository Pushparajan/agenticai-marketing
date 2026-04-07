# File      : retention_node.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Stage 5 — Retention node for the Capstone Command Centre.

Wraps the AutoGen + MCP retention-room logic.  Identifies churn risk,
calculates LTV-based intervention budgets, and proposes retention
actions (proactive outreach, save offer, expansion nudge).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from capstone_command_centre.mcp_client import get_tool

logger = logging.getLogger(__name__)

STAGE = "retention"


# ---------------------------------------------------------------------------
# Helper — retention strategy
# ---------------------------------------------------------------------------

def _retention_strategy(
    churn_cohort: dict[str, Any],
    ltv_pred: dict[str, Any],
    cohort_retention: dict[str, Any],
) -> dict[str, Any]:
    """Design a retention action based on risk signals and LTV."""
    avg_risk = churn_cohort.get("avg_risk_score", 0)
    predicted_ltv = ltv_pred.get("predicted_ltv", 0)
    m6_retention = cohort_retention.get("month_6", 0.7)

    # High churn risk — proactive save offer
    if avg_risk >= 0.6:
        budget = min(predicted_ltv * 0.10, 800)
        return {
            "action": "proactive_save_offer",
            "description": (
                f"Churn risk {avg_risk:.0%}. Deploy proactive save offer "
                f"(budget £{budget:.0f}) with dedicated CSM outreach."
            ),
            "urgency": "high",
            "suggested_spend": budget,
            "contacts_affected": churn_cohort.get("cohort_size", 0),
        }

    # Moderate risk — engagement nudge
    if avg_risk >= 0.3 or m6_retention < 0.75:
        return {
            "action": "engagement_nudge",
            "description": (
                f"Moderate risk ({avg_risk:.0%}). Send value-reinforcement "
                "content and schedule QBR."
            ),
            "urgency": "medium",
            "suggested_spend": 0,
            "contacts_affected": churn_cohort.get("cohort_size", 0),
        }

    # Low risk — expansion opportunity
    return {
        "action": "expansion_nudge",
        "description": (
            f"Healthy retention (M6={m6_retention:.0%}). Propose upsell / "
            "cross-sell based on usage patterns."
        ),
        "urgency": "low",
        "suggested_spend": 0,
        "contacts_affected": 0,
    }


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------

def retention_node(state: dict[str, Any]) -> dict[str, Any]:
    """Execute Stage 5 retention logic and return a partial state update.

    Uses CRM, CDP, and Analytics servers.  Returns
    ``stage_results.retention`` with risk assessment and proposed action.
    """
    email = state.get("contact_email", "unknown@example.com")
    contact_id = state.get("contact_id", "C-1001")
    logger.info("[Retention] Processing %s", email)

    # ---- 1. Identify churn-risk cohort via CDP ----
    churn_fn = get_tool("cdp_server", "identify_churn_risk_cohort", stage=STAGE)
    churn_cohort = churn_fn()

    # ---- 2. Get LTV prediction via CDP ----
    ltv_fn = get_tool("cdp_server", "get_ltv_prediction", stage=STAGE)
    ltv_pred = ltv_fn(email=email)

    # ---- 3. Get cohort retention curve via Analytics ----
    retention_fn = get_tool("analytics_server", "get_cohort_retention", stage=STAGE)
    cohort_retention = retention_fn()

    # ---- 4. Update CRM with retention review ----
    log_event = get_tool("crm_server", "log_journey_event", stage=STAGE)
    log_event(contact_id=contact_id, event="retention_review")

    # ---- 5. Create retention task ----
    create_task = get_tool("crm_server", "create_task", stage=STAGE)
    task = create_task(
        contact_id=contact_id,
        title=f"[Retention] Risk review for {email}",
    )

    # ---- 6. Build proposed action ----
    proposed = _retention_strategy(churn_cohort, ltv_pred, cohort_retention)

    result = {
        "stage": STAGE,
        "contact_id": contact_id,
        "email": email,
        "churn_risk_score": churn_cohort.get("avg_risk_score", 0),
        "cohort_size": churn_cohort.get("cohort_size", 0),
        "predicted_ltv": ltv_pred.get("predicted_ltv", 0),
        "month_6_retention": cohort_retention.get("month_6", 0),
        "task_id": task.get("task_id", ""),
        "proposed_action": proposed,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("[Retention] %s  risk=%.2f  action=%s",
                email, churn_cohort.get("avg_risk_score", 0), proposed["action"])

    existing = dict(state.get("stage_results", {}))
    existing[STAGE] = result
    return {"stage_results": existing}
