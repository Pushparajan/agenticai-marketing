# File      : advocacy_activation_agent.py
# Stage     : 6 — Advocacy
# Chapter   : 12
# Framework : MCP + OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Advocacy Activation Agent — powered by the OpenAI Agents SDK.

Identifies advocates, makes participation frictionless, and matches
the right ask to the right advocate using a scoring framework:

  NPS >= 9 AND LTV > tier_threshold  ->  case study ask
  NPS >= 8 AND recent_expansion      ->  referral programme
  NPS >= 7 AND active_community      ->  community moderator invite
  Any satisfied customer (NPS >= 7)   ->  G2 review request (throttled)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agents import Agent, Runner, function_tool

# -- Tool modules (MCP-style functions) ------------------------------------
from stage6_advocacy.tools.nps_tools import (
    get_nps_score,
    get_nps_distribution,
    identify_advocates,
    send_nps_followup,
)
from stage6_advocacy.tools.review_request_tools import (
    check_review_request_cooldown,
    request_g2_review,
)
from stage6_advocacy.tools.referral_programme_tools import (
    trigger_referral_programme,
    get_referral_pipeline,
    create_referral_link,
)
from stage6_advocacy.tools.community_invite_tools import (
    invite_to_community,
    get_community_activity,
    request_case_study_participation,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LTV tier thresholds
# ---------------------------------------------------------------------------

LTV_TIER_THRESHOLD = 50_000.0   # USD — above this qualifies for case study

# ---------------------------------------------------------------------------
# Scoring / classification
# ---------------------------------------------------------------------------

def classify_advocacy_action(profile: dict[str, Any]) -> list[str]:
    """Determine which advocacy actions to take for a customer profile.

    Returns an ordered list of recommended action keys.
    """
    actions: list[str] = []
    nps = profile.get("nps_score", 0)
    ltv = profile.get("ltv", 0.0)
    recent_expansion = profile.get("recent_expansion", False)
    active_community = profile.get("active_community", False)

    # Highest-value ask first
    if nps >= 9 and ltv > LTV_TIER_THRESHOLD:
        actions.append("case_study")

    if nps >= 8 and recent_expansion:
        actions.append("referral_programme")

    if nps >= 7 and active_community:
        actions.append("community_moderator")

    # Universal — throttled via cooldown
    if nps >= 7:
        actions.append("g2_review")

    # NPS follow-up is always sent
    actions.append("nps_followup")

    return actions


# ---------------------------------------------------------------------------
# Wrap plain functions as @function_tool for OpenAI Agents SDK
# ---------------------------------------------------------------------------

@function_tool
def tool_get_nps_score(customer_id: str) -> str:
    """Retrieve the latest NPS score and profile for a customer."""
    return get_nps_score(customer_id)


@function_tool
def tool_get_nps_distribution() -> str:
    """Return the NPS score distribution across all surveyed customers."""
    return get_nps_distribution()


@function_tool
def tool_identify_advocates(min_nps: int, min_ltv: float) -> str:
    """Identify customers who qualify as advocates based on NPS and LTV thresholds."""
    return identify_advocates(min_nps, min_ltv)


@function_tool
def tool_send_nps_followup(customer_id: str, nps_score: int) -> str:
    """Send an NPS follow-up email appropriate to the customer's score band."""
    return send_nps_followup(customer_id, nps_score)


@function_tool
def tool_request_g2_review(contact_email: str, personalisation_note: str) -> str:
    """Send a personalised G2 review request (respects cooldown throttle)."""
    return request_g2_review(contact_email, personalisation_note)


@function_tool
def tool_check_review_request_cooldown(contact_email: str) -> str:
    """Check whether a contact is within the review-request cooldown window."""
    return check_review_request_cooldown(contact_email)


@function_tool
def tool_trigger_referral_programme(customer_id: str, programme_tier: str) -> str:
    """Enrol a customer in the referral programme at the specified tier."""
    return trigger_referral_programme(customer_id, programme_tier)


@function_tool
def tool_get_referral_pipeline(customer_id: str) -> str:
    """Get the referral pipeline summary for an enrolled customer."""
    return get_referral_pipeline(customer_id)


@function_tool
def tool_create_referral_link(customer_id: str) -> str:
    """Generate or retrieve a unique referral link for a customer."""
    return create_referral_link(customer_id)


@function_tool
def tool_invite_to_community(contact_email: str, community_type: str) -> str:
    """Invite a customer to a community channel (slack, forum, advisory board, etc.)."""
    return invite_to_community(contact_email, community_type)


@function_tool
def tool_get_community_activity(customer_id: str) -> str:
    """Retrieve a customer's community engagement activity and score."""
    return get_community_activity(customer_id)


@function_tool
def tool_request_case_study_participation(customer_id: str, use_case: str) -> str:
    """Request a customer to participate in a case study for a specific use case."""
    return request_case_study_participation(customer_id, use_case)


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are the **Advocacy Activation Agent** — a specialised AI agent that
turns satisfied customers into active advocates.

Your three core principles:
1. **Identify advocates** — Use NPS scores, LTV data, community activity,
   and expansion history to find your best potential advocates.
2. **Make participation frictionless** — Pre-fill information, provide
   direct links, and minimise steps for every advocacy ask.
3. **Match the right ask to the right advocate** — Use the scoring
   framework to ensure each customer receives an appropriate request:

   - NPS >= 9 AND LTV > $50,000  →  Case study participation
   - NPS >= 8 AND recent expansion  →  Referral programme enrolment
   - NPS >= 7 AND active community member  →  Community moderator invite
   - Any satisfied customer (NPS >= 7)  →  G2 review request (throttled)

**Workflow for each customer:**
1. Retrieve the customer's NPS score and profile.
2. Check community activity and engagement.
3. Classify which advocacy actions are appropriate.
4. Execute each action using the available tools.
5. Send an NPS follow-up appropriate to their score band.
6. Summarise all actions taken with links and next steps.

Always explain *why* you chose each action and keep the tone warm,
appreciative, and never pushy. Respect cooldown windows for review
requests.
"""

advocacy_activation_agent = Agent(
    name="AdvocacyActivationAgent",
    model="gpt-4.1",
    instructions=SYSTEM_PROMPT,
    tools=[
        tool_get_nps_score,
        tool_get_nps_distribution,
        tool_identify_advocates,
        tool_send_nps_followup,
        tool_request_g2_review,
        tool_check_review_request_cooldown,
        tool_trigger_referral_programme,
        tool_get_referral_pipeline,
        tool_create_referral_link,
        tool_invite_to_community,
        tool_get_community_activity,
        tool_request_case_study_participation,
    ],
)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

async def run_advocacy_agent(prompt: str) -> str:
    """Run the advocacy activation agent with the given prompt.

    Args:
        prompt: Natural-language instruction for the agent.

    Returns:
        The agent's final text response.
    """
    result = await Runner.run(advocacy_activation_agent, input=prompt)
    return result.final_output
