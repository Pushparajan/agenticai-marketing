# File      : routing.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Conditional routing logic for the Decision-stage graph.

``route_decision_action`` inspects the current state and returns the name
of the next node to execute.  The priority order is:

1. High-value deal needing human approval
2. High intent + proposal viewed  -> close offer
3. Objections raised              -> address objections
4. Competitors named              -> battlecard / comparison
5. Stalled deal (>14 days)        -> urgency reactivation
6. Default                        -> standard nurture
"""

from __future__ import annotations


def route_decision_action(state: dict) -> str:
    """Return the next node key based on the current decision signals.

    Parameters
    ----------
    state : dict
        The full ``DecisionJourneyState``.

    Returns
    -------
    str
        One of the node keys:
        ``'request_human_approval'``, ``'send_close_offer'``,
        ``'address_objections'``, ``'send_comparison_content'``,
        ``'reactivate_with_urgency'``, or ``'send_next_nurture'``.
    """
    deal_value: float = state.get("deal_value", 0.0)
    human_approved: bool = state.get("human_approved", False)
    intent_score: int = state.get("intent_score", 0)
    proposal_viewed: bool = state.get("proposal_viewed", False)
    objections: list[str] = state.get("objections_raised", [])
    competitors: list[str] = state.get("competitors_named", [])
    days_in_decision: int = state.get("days_in_decision", 0)

    # 1. High-value deal gate
    if deal_value > 50_000 and not human_approved:
        return "request_human_approval"

    # 2. Ready to close
    if intent_score >= 85 and proposal_viewed:
        return "send_close_offer"

    # 3. Objections need addressing
    if objections:
        return "address_objections"

    # 4. Competitive pressure
    if competitors:
        return "send_comparison_content"

    # 5. Deal has stalled
    if days_in_decision > 14:
        return "reactivate_with_urgency"

    # 6. Default nurture
    return "send_next_nurture"
