# File      : product_specialist.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Product Specialist agent — identifies the *aha* feature for each customer.

Uses ``autogen_agentchat`` (pyautogen >= 0.4) and registers product-usage
tools so the LLM can inspect heatmaps, feature-completion rates, and
friction points to recommend which feature will deliver the fastest value.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from stage4_onboarding.tools.product_usage_tools import (
    get_feature_completion_rate,
    get_usage_heatmap,
    identify_friction_points,
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

PRODUCT_SPECIALIST_SYSTEM_MESSAGE = """\
You are the **Product Specialist** for our SaaS platform's onboarding team.

Your expertise:
- Deep knowledge of every product feature and its value drivers.
- Ability to read usage-heatmap data and feature-completion metrics.
- Identifying the single "aha" feature that will resonate most with a
  specific customer based on their role, industry, and early behaviour.

Your responsibilities during onboarding analysis:
1. Call ``get_usage_heatmap`` to understand which features the customer
   has explored and how deeply.
2. Call ``get_feature_completion_rate`` to see which milestones they have
   completed and which remain.
3. If usage looks low or scattered, call ``identify_friction_points`` to
   discover blockers.
4. Based on the data, recommend the *aha* feature — the one capability
   that, once activated, will make the customer say "I can't live
   without this product."

Always ground your recommendation in the data you retrieve.  Provide
a concise summary (max 200 words) with:
- The recommended aha feature and why.
- Any friction points that could block activation.
- Suggested content (guides, videos) to help the customer reach the aha
  moment faster.
"""

# ---------------------------------------------------------------------------
# Tool wrappers (plain functions for AutoGen tool registration)
# ---------------------------------------------------------------------------


def tool_get_usage_heatmap(customer_id: str, days: int = 7) -> str:
    """Retrieve the feature-usage heatmap for a customer."""
    return get_usage_heatmap(customer_id, days)


def tool_get_feature_completion_rate(customer_id: str) -> str:
    """Retrieve onboarding feature-completion rate for a customer."""
    return get_feature_completion_rate(customer_id)


def tool_identify_friction_points(customer_id: str) -> str:
    """Identify friction points in a customer's onboarding journey."""
    return identify_friction_points(customer_id)


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_product_specialist(
    model: str | None = None,
    api_key: str | None = None,
) -> AssistantAgent:
    """Create and return a configured Product Specialist ``AssistantAgent``.

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
        name="ProductSpecialist",
        description=(
            "Product expert that analyses usage heatmaps, feature completion "
            "rates, and friction points to identify the aha feature for a "
            "new customer during onboarding."
        ),
        model_client=model_client,
        system_message=PRODUCT_SPECIALIST_SYSTEM_MESSAGE,
        tools=[
            tool_get_usage_heatmap,
            tool_get_feature_completion_rate,
            tool_identify_friction_points,
        ],
    )
    return agent
