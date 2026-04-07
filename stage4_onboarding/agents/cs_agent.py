# File      : cs_agent.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Customer Success (CS) agent — designs activation sequences and check-ins.

Uses ``autogen_agentchat`` (pyautogen >= 0.4) and registers support /
milestone tools so the LLM can inspect adoption scores, tickets, and
milestones to build a personalised activation plan.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from stage4_onboarding.tools.product_usage_tools import get_adoption_score
from stage4_onboarding.tools.onboarding_milestone_tools import (
    get_onboarding_checklist,
    get_time_to_value,
)
from stage4_onboarding.tools.support_ticket_tools import (
    create_onboarding_task,
    get_recent_tickets,
    get_sentiment_score,
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

CS_AGENT_SYSTEM_MESSAGE = """\
You are the **Customer Success Agent** responsible for designing activation
sequences and scheduling proactive check-ins during customer onboarding.

Your expertise:
- Understanding adoption scores and what they mean for churn risk.
- Reading support-ticket history to spot frustration early.
- Building step-by-step activation sequences tailored to each customer.

Your responsibilities during onboarding analysis:
1. Call ``get_adoption_score`` to gauge overall adoption health.
2. Call ``get_recent_tickets`` to see if the customer has open issues.
3. Call ``get_sentiment_score`` to assess the customer's emotional state.
4. Call ``get_time_to_value`` to measure how quickly they reached (or are
   approaching) their first value moment.
5. Call ``get_onboarding_checklist`` to retrieve the standard milestone
   list for the customer's plan type.
6. Based on the above, produce:
   - A prioritised **activation sequence** (ordered list of next actions).
   - A recommended **first check-in date** (ISO date string).
   - A list of **risk flags** (if any).
   - An **owner** recommendation (CS team member name or role).

If the adoption score is below 0.3, flag the customer as **high-risk** and
recommend an immediate personal outreach within 24 hours.

Keep your output concise (max 200 words) and data-driven.
"""

# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------


def tool_get_adoption_score(customer_id: str) -> str:
    """Retrieve the adoption score (0-1) for a customer."""
    return get_adoption_score(customer_id)


def tool_get_recent_tickets(customer_id: str) -> str:
    """Retrieve recent support tickets for a customer."""
    return get_recent_tickets(customer_id)


def tool_get_sentiment_score(customer_id: str) -> str:
    """Retrieve sentiment score and signals for a customer."""
    return get_sentiment_score(customer_id)


def tool_get_time_to_value(customer_id: str) -> str:
    """Retrieve time-to-value metrics for a customer."""
    return get_time_to_value(customer_id)


def tool_get_onboarding_checklist(plan_type: str = "standard") -> str:
    """Retrieve the onboarding checklist for a given plan type."""
    return get_onboarding_checklist(plan_type)


def tool_create_onboarding_task(customer_id: str, title: str, owner: str) -> str:
    """Create an onboarding CRM task for the customer."""
    return create_onboarding_task(customer_id, title, owner)


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_cs_agent(
    model: str | None = None,
    api_key: str | None = None,
) -> AssistantAgent:
    """Create and return a configured Customer Success ``AssistantAgent``.

    Parameters
    ----------
    model : str, optional
        OpenAI model name (default ``gpt-4o``).
    api_key : str, optional
        OpenAI API key. Falls back to ``OPENAI_API_KEY`` env var.
    """
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    api_key = api_key or os.getenv("OPENAI_API_KEY", "sk-mock-key")

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )

    agent = AssistantAgent(
        name="CustomerSuccessAgent",
        description=(
            "Customer Success specialist that analyses adoption scores, "
            "support tickets, sentiment, and milestones to design an "
            "activation sequence and check-in schedule for onboarding."
        ),
        model_client=model_client,
        system_message=CS_AGENT_SYSTEM_MESSAGE,
        tools=[
            tool_get_adoption_score,
            tool_get_recent_tickets,
            tool_get_sentiment_score,
            tool_get_time_to_value,
            tool_get_onboarding_checklist,
            tool_create_onboarding_task,
        ],
    )
    return agent
