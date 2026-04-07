# state.py
# Project 5: Adaptive Customer Journey Orchestrator
# Chapter Reference: Chapter 4 - LangGraph
# Description: Journey state definition for the customer journey orchestrator
# Author: Pushparajan Ramar

"""JourneyState TypedDict for the adaptive customer journey orchestrator.

Defines the shared state that flows through every node in the LangGraph
state machine.  Each field captures a dimension of the contact's journey
progression -- from initial engagement scoring through nurture sequences
to eventual sales handoff.
"""

from __future__ import annotations

from typing import TypedDict


class JourneyState(TypedDict):
    """Shared state for the customer journey orchestration graph.

    Attributes:
        contact_id:      Unique identifier for the contact (e.g. HubSpot ID).
        email:           Contact email address.
        first_name:      Contact first name for personalization.
        engagement_score: Composite engagement score from 0 (cold) to 100 (hot).
        touchpoints_sent: Total number of outbound touchpoints delivered so far.
        last_action:     Name of the most recent graph node that executed.
        channel_history: Ordered list of channels used (e.g. "email", "demo").
        qualified:       Whether the contact is marketing-qualified for sales.
        day:             Current simulation day (1-30 in the runner).
        messages:        Chronological log of actions taken during the journey.
    """

    contact_id: str
    email: str
    first_name: str
    engagement_score: int          # 0-100
    touchpoints_sent: int
    last_action: str
    channel_history: list[str]
    qualified: bool
    day: int                       # simulation day
    messages: list[str]            # log of actions taken
