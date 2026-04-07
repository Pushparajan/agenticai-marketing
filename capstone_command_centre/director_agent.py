# File      : director_agent.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
MarketingOpsDirector — the approval gate for the Command Centre.

Reviews proposed actions from all six stage agents and applies business
rules (budget caps, frequency limits, compliance, brand safety) before
approving, modifying, or rejecting each action.

In mock mode the director runs locally with deterministic rule logic.
In live mode it delegates to GPT-4.1 for nuanced judgement.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Business-rule thresholds
# ---------------------------------------------------------------------------

SPEND_CAP_GBP = 500          # Any single action above this needs approval
BULK_CONTACT_LIMIT = 100     # Bulk ops touching > N contacts need approval
MAX_TOUCHES_PER_WEEK = 3     # Frequency cap per contact
HIGH_STAKES_KEYWORDS = [
    "contract", "legal", "pricing", "discount", "refund",
    "termination", "penalty", "compliance",
]
BRAND_SAFETY_KEYWORDS = [
    "guaranteed", "risk-free", "unlimited", "act now",
]


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

def _check_spend(action: dict[str, Any]) -> str | None:
    spend = action.get("suggested_spend", 0)
    if spend > SPEND_CAP_GBP:
        return (f"Spend £{spend:.0f} exceeds £{SPEND_CAP_GBP} cap. "
                f"Reduced to £{SPEND_CAP_GBP}.")
    return None


def _check_bulk(action: dict[str, Any]) -> str | None:
    contacts = action.get("contacts_affected", 0)
    if contacts > BULK_CONTACT_LIMIT:
        return (f"Bulk operation targets {contacts} contacts "
                f"(limit {BULK_CONTACT_LIMIT}). Requires human approval.")
    return None


def _check_high_stakes(action: dict[str, Any]) -> str | None:
    desc = action.get("description", "").lower()
    for kw in HIGH_STAKES_KEYWORDS:
        if kw in desc:
            return f"High-stakes keyword '{kw}' detected — flagged for review."
    return None


def _check_brand_safety(action: dict[str, Any]) -> str | None:
    desc = action.get("description", "").lower()
    for kw in BRAND_SAFETY_KEYWORDS:
        if kw in desc:
            return f"Brand-safety concern: '{kw}' found in action copy."
    return None


def _check_frequency(action: dict[str, Any], recent_touches: int) -> str | None:
    if recent_touches >= MAX_TOUCHES_PER_WEEK:
        return (f"Contact already received {recent_touches} touches this week "
                f"(limit {MAX_TOUCHES_PER_WEEK}). Defer action.")
    return None


def _apply_rules(
    stage: str,
    action: dict[str, Any],
    recent_touches: int = 0,
) -> dict[str, Any]:
    """Run all business rules against a proposed action.

    Returns a decision dict with ``verdict`` (approved / modified / rejected),
    ``warnings``, and ``modifications``.
    """
    warnings: list[str] = []
    modifications: list[str] = []
    verdict = "approved"

    # --- Spend cap ---
    spend_flag = _check_spend(action)
    if spend_flag:
        modifications.append(spend_flag)
        action["suggested_spend"] = min(action.get("suggested_spend", 0),
                                        SPEND_CAP_GBP)
        verdict = "modified"

    # --- Bulk limit ---
    bulk_flag = _check_bulk(action)
    if bulk_flag:
        warnings.append(bulk_flag)
        verdict = "rejected"

    # --- High-stakes ---
    hs_flag = _check_high_stakes(action)
    if hs_flag:
        warnings.append(hs_flag)
        if verdict != "rejected":
            verdict = "modified"

    # --- Brand safety ---
    bs_flag = _check_brand_safety(action)
    if bs_flag:
        warnings.append(bs_flag)
        if verdict != "rejected":
            verdict = "modified"

    # --- Frequency ---
    freq_flag = _check_frequency(action, recent_touches)
    if freq_flag:
        warnings.append(freq_flag)
        verdict = "rejected"

    return {
        "stage": stage,
        "original_action": action.get("action", "unknown"),
        "verdict": verdict,
        "warnings": warnings,
        "modifications": modifications,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# LLM-based review (live mode)
# ---------------------------------------------------------------------------

def _llm_review(stage_results: dict[str, Any]) -> dict[str, Any]:
    """Use GPT-4.1 to review proposed actions (requires OPENAI_API_KEY)."""
    try:
        from openai import OpenAI
        client = OpenAI()

        prompt = (
            "You are the MarketingOpsDirector. Review the following proposed "
            "marketing actions from each stage agent. For each action, decide: "
            "approve, modify, or reject. Apply these rules:\n"
            f"- Spend cap: £{SPEND_CAP_GBP} per action\n"
            f"- Bulk limit: {BULK_CONTACT_LIMIT} contacts\n"
            f"- Max touches: {MAX_TOUCHES_PER_WEEK}/week per contact\n"
            "- Flag high-stakes language (pricing, legal, contracts)\n"
            "- Flag brand-safety issues (guaranteed, risk-free, act now)\n\n"
            "Return JSON with key 'decisions' containing a list of objects "
            "with keys: stage, verdict, warnings, modifications.\n\n"
            f"Proposed actions:\n{json.dumps(stage_results, indent=2)}"
        )

        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content or "{}")
    except Exception as exc:
        logger.warning("LLM review failed (%s), falling back to rules.", exc)
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def review_actions(state: dict[str, Any]) -> dict[str, Any]:
    """Review all proposed stage actions and return approval decisions.

    Parameters
    ----------
    state : dict
        The full CommandCentreState with ``stage_results`` populated.

    Returns
    -------
    dict
        Partial state update with ``approval_decisions`` — a dict keyed
        by stage name, each containing the director's verdict.
    """
    stage_results: dict[str, Any] = state.get("stage_results", {})
    recent_touches: int = state.get("recent_touches", 1)

    if not USE_MOCK:
        llm_result = _llm_review(stage_results)
        if llm_result.get("decisions"):
            decisions = {
                d["stage"]: d for d in llm_result["decisions"]
            }
            return {"approval_decisions": decisions}

    # ---- Rule-based review (mock / fallback) ----
    decisions: dict[str, Any] = {}
    for stage_name, result in stage_results.items():
        action = result.get("proposed_action", {})
        decision = _apply_rules(stage_name, action, recent_touches)
        decisions[stage_name] = decision
        logger.info(
            "[Director] %-15s  verdict=%-10s  warnings=%d",
            stage_name, decision["verdict"], len(decision["warnings"]),
        )

    return {"approval_decisions": decisions}
