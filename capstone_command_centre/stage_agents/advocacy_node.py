# File      : advocacy_node.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Stage 6 — Advocacy node for the Capstone Command Centre.

Wraps the MCP + OpenAI Agents advocacy logic.  Identifies promoters,
matches them to the best advocacy programme (G2 review, referral,
case study, community), and proposes outreach actions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from capstone_command_centre.mcp_client import get_tool

logger = logging.getLogger(__name__)

STAGE = "advocacy"


# ---------------------------------------------------------------------------
# Helper — match advocate to programme
# ---------------------------------------------------------------------------

def _match_programme(
    advocate: dict[str, Any],
    nps_dist: dict[str, Any],
    referral_pipeline: dict[str, Any],
) -> dict[str, Any]:
    """Select the best advocacy ask for a given promoter."""
    nps = advocate.get("nps", 0)
    ltv = advocate.get("ltv", 0)
    pipeline_value = referral_pipeline.get("pipeline_value", 0)

    actions: list[dict[str, Any]] = []

    # NPS 9-10 with high LTV — full advocacy suite
    if nps >= 9 and ltv >= 40_000:
        actions = [
            {
                "programme": "g2_review",
                "description": "Request G2 review — high NPS promoter.",
            },
            {
                "programme": "referral",
                "description": "Enrol in referral programme with tiered rewards.",
            },
            {
                "programme": "case_study",
                "description": "Invite to co-create a customer success story.",
            },
            {
                "programme": "community",
                "description": "Invite to customer advisory board / community.",
            },
        ]
    elif nps >= 7:
        actions = [
            {
                "programme": "capterra_review",
                "description": "Request Capterra review — good NPS.",
            },
            {
                "programme": "referral",
                "description": "Enrol in referral programme.",
            },
        ]
    else:
        actions = [
            {
                "programme": "community",
                "description": "Invite to community for deeper engagement.",
            },
        ]

    return {
        "action": "activate_advocacy_programmes",
        "description": (
            f"Matched {len(actions)} programme(s) for advocate "
            f"(NPS={nps}, LTV=£{ltv:,})."
        ),
        "programmes": actions,
        "urgency": "medium",
        "suggested_spend": 0,
    }


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------

def advocacy_node(state: dict[str, Any]) -> dict[str, Any]:
    """Execute Stage 6 advocacy logic and return a partial state update.

    Uses Advocacy and CRM MCP servers.  Returns
    ``stage_results.advocacy`` with advocate matches and proposed
    programmes.
    """
    email = state.get("contact_email", "unknown@example.com")
    contact_id = state.get("contact_id", "C-1001")
    logger.info("[Advocacy] Processing %s", email)

    # ---- 1. Identify eligible advocates ----
    identify = get_tool("advocacy_server", "identify_advocates", stage=STAGE)
    advocates_data = identify()
    advocates = advocates_data.get("advocates", [])

    # Find this contact in the advocate list
    advocate = next(
        (a for a in advocates if a.get("email") == email),
        {"email": email, "nps": 0, "ltv": 0, "eligible": False},
    )

    # ---- 2. Get NPS distribution ----
    nps_fn = get_tool("advocacy_server", "get_nps_distribution", stage=STAGE)
    nps_dist = nps_fn()

    # ---- 3. Get referral pipeline health ----
    ref_fn = get_tool("advocacy_server", "get_referral_pipeline", stage=STAGE)
    referral_pipeline = ref_fn()

    # ---- 4. Execute advocacy actions if eligible ----
    executed_programmes: list[str] = []
    if advocate.get("eligible"):
        # Request G2 review
        g2_fn = get_tool("advocacy_server", "request_g2_review", stage=STAGE)
        g2_fn(email=email)
        executed_programmes.append("g2_review")

        # Trigger referral programme
        ref_trigger = get_tool("advocacy_server", "trigger_referral_programme",
                               stage=STAGE)
        ref_trigger(email=email)
        executed_programmes.append("referral")

    # ---- 5. Log journey event in CRM ----
    log_event = get_tool("crm_server", "log_journey_event", stage=STAGE)
    log_event(contact_id=contact_id, event="advocacy_activated")

    # ---- 6. Build proposed action ----
    proposed = _match_programme(advocate, nps_dist, referral_pipeline)

    result = {
        "stage": STAGE,
        "contact_id": contact_id,
        "email": email,
        "is_eligible_advocate": advocate.get("eligible", False),
        "nps": advocate.get("nps", 0),
        "ltv": advocate.get("ltv", 0),
        "nps_distribution": nps_dist,
        "referral_pipeline_value": referral_pipeline.get("pipeline_value", 0),
        "executed_programmes": executed_programmes,
        "proposed_action": proposed,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("[Advocacy] %s  eligible=%s  programmes=%d",
                email, advocate.get("eligible"), len(executed_programmes))

    existing = dict(state.get("stage_results", {}))
    existing[STAGE] = result
    return {"stage_results": existing}
