# File      : retention_strategist.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Retention Strategist agent.

An AutoGen AssistantAgent that selects the optimal retention intervention
based on churn-risk analysis and historical play data.

Interventions:
  - executive_outreach
  - product_training
  - commercial_offer
  - competitive_repositioning
  - success_story_sharing

Uses tools from tools/churn_risk_tools.py and tools/win_back_tools.py.
"""

from __future__ import annotations

import json
import os
import sys

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ---------------------------------------------------------------------------
# Resolve imports for sibling packages
# ---------------------------------------------------------------------------
_STAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _STAGE_DIR not in sys.path:
    sys.path.insert(0, _STAGE_DIR)

from tools.churn_risk_tools import (
    get_similar_churned_customers,
    get_successful_retention_plays,
)
from tools.win_back_tools import (
    generate_win_back_sequence,
    get_competitive_counter_offer,
)
from tools.nps_sentiment_tools import get_sentiment_trend

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

RETENTION_STRATEGIST_PROMPT = """\
You are the Retention Strategist. Based on the Churn Risk Analyst's
assessment, you select and orchestrate the optimal retention intervention.

## Available Interventions
1. **executive_outreach** — VP/C-level engagement for critical accounts
2. **product_training** — Guided onboarding, feature adoption workshops
3. **commercial_offer** — Discount, credit, or contract incentive
4. **competitive_repositioning** — Battle-card driven counter-strategy
5. **success_story_sharing** — Peer case studies and ROI evidence

## Strategy Selection Rules
- **critical + usage_gap** → executive_outreach (primary) + product_training
- **critical + competitor** → executive_outreach + competitive_repositioning
- **high + competitor** → competitive_repositioning + commercial_offer
- **high + price** → commercial_offer + success_story_sharing
- **high + support** → executive_outreach + product_training
- **medium + value_gap** → success_story_sharing + product_training
- **medium + relationship** → executive_outreach + success_story_sharing
- **low** → standard CSM nurture (no escalation)

## Process
1. Review the churn-risk assessment from Churn_Risk_Analyst.
2. Use `get_successful_retention_plays` to look up historical success rates.
3. Use `get_similar_churned_customers` to learn from past losses.
4. Use `generate_win_back_sequence` to build a tailored outreach plan.
5. If competitor is mentioned, use `get_competitive_counter_offer`.
6. Optionally use `get_sentiment_trend` to validate timing.

## Output Format
Provide your strategy as a JSON block:
```json
{
  "customer_id": "...",
  "primary_intervention": "...",
  "secondary_intervention": "...",
  "rationale": "...",
  "historical_success_rate": 0.0-1.0,
  "win_back_sequence_summary": "...",
  "estimated_save_probability": 0.0-1.0,
  "urgency": "immediate|this_week|this_month",
  "escalation_required": true/false,
  "key_actions": ["..."]
}
```

Always use the tools to gather data before forming your recommendation.
"""

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def create_retention_strategist(
    model: str | None = None,
    api_key: str | None = None,
) -> AssistantAgent:
    """Create and return the Retention_Strategist AssistantAgent.

    Args:
        model: OpenAI model name (default: gpt-4o from env or fallback).
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var).

    Returns:
        A configured AssistantAgent with retention-strategy tools registered.
    """
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )

    agent = AssistantAgent(
        name="Retention_Strategist",
        model_client=model_client,
        system_message=RETENTION_STRATEGIST_PROMPT,
        tools=[
            get_successful_retention_plays,
            get_similar_churned_customers,
            generate_win_back_sequence,
            get_competitive_counter_offer,
            get_sentiment_trend,
        ],
    )

    return agent


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    from autogen_agentchat.messages import TextMessage
    from autogen_core import CancellationToken

    async def _test() -> None:
        agent = create_retention_strategist()
        prompt = (
            "The Churn Risk Analyst classified CUST-002 as high risk with "
            "primary driver 'competitor'. The competitor mentioned is "
            "CompetitorX. Recommend a retention strategy."
        )
        response = await agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            cancellation_token=CancellationToken(),
        )
        print("=== Retention Strategist Response ===")
        print(response.chat_message.content)

    asyncio.run(_test())
