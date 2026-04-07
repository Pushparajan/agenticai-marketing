# File      : onboarding_coordinator.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Onboarding Coordinator agent — synthesises outputs into a structured plan.

Takes the Product Specialist's aha-feature recommendation and the CS
Agent's activation sequence and produces a final JSON onboarding plan
with a well-defined schema.
"""

from __future__ import annotations

import os

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

COORDINATOR_SYSTEM_MESSAGE = """\
You are the **Onboarding Coordinator**. Your job is to synthesise the
outputs from the Product Specialist and the Customer Success Agent into a
single, structured onboarding action plan.

You do NOT call any tools yourself.  Instead you read the conversation,
extract the key findings from both specialists, and produce a final JSON
object with **exactly** this schema:

```json
{
  "customer_id": "<string>",
  "aha_feature": "<string — the single feature most likely to drive value>",
  "activation_sequence": [
    "<step 1 description>",
    "<step 2 description>",
    "..."
  ],
  "first_check_in_date": "<YYYY-MM-DD>",
  "risk_flags": [
    "<flag 1>",
    "..."
  ],
  "recommended_content": [
    "<article / video / guide title>",
    "..."
  ],
  "owner": "<CS team member or role>"
}
```

Rules:
1. The ``aha_feature`` must come from the Product Specialist's analysis.
2. The ``activation_sequence`` must be ordered by priority and reflect the
   CS Agent's recommendations.
3. ``first_check_in_date`` must be an ISO date string.  If the customer
   is high-risk, set the check-in within 24-48 hours from today.
4. ``risk_flags`` should be empty list ``[]`` if no risks were found.
5. ``recommended_content`` should include 2-4 items from the specialists'
   suggestions.
6. ``owner`` should be the CS team member recommended by the CS Agent.

Output ONLY the JSON object — no markdown fences, no extra commentary.
"""

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_onboarding_coordinator(
    model: str | None = None,
    api_key: str | None = None,
) -> AssistantAgent:
    """Create and return the Onboarding Coordinator ``AssistantAgent``.

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
        name="OnboardingCoordinator",
        description=(
            "Coordinator that reads Product Specialist and CS Agent outputs "
            "and synthesises a final structured JSON onboarding action plan."
        ),
        model_client=model_client,
        system_message=COORDINATOR_SYSTEM_MESSAGE,
        tools=[],  # Coordinator does not use tools
    )
    return agent
