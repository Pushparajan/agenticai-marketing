# File      : commercial_agent.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Commercial Agent.

An AutoGen AssistantAgent that calculates and recommends financial
retention offers including:
  - max_discount_authorised
  - contract_extension_incentive
  - expansion_credit_offer

Uses tools from tools/expansion_revenue_tools.py.
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

from tools.expansion_revenue_tools import (
    calculate_retention_offer,
    get_contract_details,
    get_expansion_opportunities,
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

COMMERCIAL_AGENT_PROMPT = """\
You are the Commercial Agent. Your role is to calculate financially sound
retention offers that balance customer save-rate with margin protection.

## Responsibilities
1. Retrieve full contract details using `get_contract_details`.
2. Calculate the retention offer using `calculate_retention_offer`.
3. Identify expansion opportunities using `get_expansion_opportunities`.

## Offer Calculation Guidelines

### Discount Authority Matrix
| Risk Level | Max Discount | Approval Required |
|-----------|-------------|-------------------|
| critical  | 25%         | VP Sales          |
| high      | 15%         | Sales Director    |
| medium    | 10%         | CSM Manager       |
| low       | 5%          | CSM (auto)        |

### Contract Extension Incentives
- critical: Up to 2 months free on 24-month renewal
- high: Up to 1 month free on 18-month renewal
- medium: 10% off on early 12-month renewal
- low: Standard renewal terms

### Expansion Credit Strategy
- Always look for expansion upsell to offset retention discount
- Frame discounts as "investment credits" tied to expansion
- Never exceed 30% of ARR as total retention budget

## Business Rules
- Total retention budget must not exceed 30% of customer ARR
- Discounts on critical accounts require VP Sales approval
- All offers must include a contract extension commitment
- Expansion credits are contingent on upsell agreement

## Output Format
Provide your offer as a JSON block:
```json
{
  "customer_id": "...",
  "contract_summary": {
    "plan": "...",
    "arr": 0,
    "days_to_renewal": 0,
    "seats_utilisation": "X/Y active"
  },
  "retention_offer": {
    "max_discount_authorised": "X%",
    "discount_amount": 0,
    "contract_extension_incentive": "...",
    "expansion_credit_offer": 0,
    "total_retention_budget": 0,
    "approval_required": true/false,
    "approver": "..."
  },
  "expansion_opportunities": [
    {"opportunity": "...", "potential_arr_increase": 0}
  ],
  "net_revenue_impact": "...",
  "recommendation": "..."
}
```

Always call all three tools before providing your recommendation.
"""

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def create_commercial_agent(
    model: str | None = None,
    api_key: str | None = None,
) -> AssistantAgent:
    """Create and return the Commercial_Agent AssistantAgent.

    Args:
        model: OpenAI model name (default: gpt-4o from env or fallback).
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var).

    Returns:
        A configured AssistantAgent with commercial/contract tools registered.
    """
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )

    agent = AssistantAgent(
        name="Commercial_Agent",
        model_client=model_client,
        system_message=COMMERCIAL_AGENT_PROMPT,
        tools=[
            get_contract_details,
            calculate_retention_offer,
            get_expansion_opportunities,
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
        agent = create_commercial_agent()
        prompt = (
            "Prepare a retention offer for CUST-001 classified as critical "
            "risk. Include contract details and expansion opportunities."
        )
        response = await agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            cancellation_token=CancellationToken(),
        )
        print("=== Commercial Agent Response ===")
        print(response.chat_message.content)

    asyncio.run(_test())
