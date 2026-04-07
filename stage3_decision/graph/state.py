# File      : state.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
DecisionJourneyState — the shared state that flows through every node
in the Decision-stage LangGraph.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class DecisionJourneyState(TypedDict, total=False):
    """Typed state dictionary for the Decision-stage graph.

    Fields
    ------
    contact_id          : CRM contact identifier.
    company             : Company / account name.
    deal_id             : CRM deal identifier.
    deal_value          : Monetary value of the deal (USD).
    intent_score        : Buyer-intent score 0-100.
    days_in_decision    : Calendar days since the deal entered the Decision stage.
    objections_raised   : List of objection strings surfaced by the prospect.
    competitors_named   : List of competitor names mentioned by the prospect.
    stakeholders        : List of stakeholder names / roles involved.
    proposal_viewed     : Whether the prospect has opened the proposal.
    pricing_tier_viewed : Which pricing tier page/doc was last viewed.
    last_action         : Label of the most recent action taken by the graph.
    next_action         : Label of the next planned action.
    human_approved      : Whether a human rep has approved the proposed action.
    messages            : Append-only message list (LangGraph add_messages reducer).
    """

    contact_id: str
    company: str
    deal_id: str
    deal_value: float
    intent_score: int
    days_in_decision: int
    objections_raised: list[str]
    competitors_named: list[str]
    stakeholders: list[str]
    proposal_viewed: bool
    pricing_tier_viewed: str
    last_action: str
    next_action: str
    human_approved: bool
    messages: Annotated[list, add_messages]
