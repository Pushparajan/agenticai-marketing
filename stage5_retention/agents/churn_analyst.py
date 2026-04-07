# File      : churn_analyst.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Churn Risk Analyst agent.

An AutoGen AssistantAgent that classifies customer churn risk as
low / medium / high / critical and identifies the primary driver:
usage_gap | value_gap | price | competitor | support | relationship.

Uses tools from tools/churn_risk_tools.py and tools/nps_sentiment_tools.py.
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
    get_churn_risk_score,
    predict_churn_probability,
)
from tools.nps_sentiment_tools import (
    get_nps_score,
    get_sentiment_trend,
    get_support_ticket_sentiment,
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

CHURN_ANALYST_PROMPT = """\
You are the Churn Risk Analyst. Your job is to assess customer health and
classify churn risk.

## Responsibilities
1. Retrieve the customer's churn-risk profile using `get_churn_risk_score`.
2. Check the NPS score using `get_nps_score`.
3. Analyse support-ticket sentiment using `get_support_ticket_sentiment`.
4. Predict churn probability for 30/60/90 day horizons using
   `predict_churn_probability`.
5. Optionally check sentiment trend using `get_sentiment_trend`.

## Classification Rules
- **critical**: risk_score >= 80 OR (NPS < 5 AND usage < 30% baseline)
- **high**: risk_score >= 60 OR (NPS < 7 AND 3+ consecutive negative tickets)
- **medium**: risk_score >= 40 OR (NPS drop of 3+ points in 90 days)
- **low**: everything else

## Primary Driver Identification
Determine the single most impactful driver from:
- `usage_gap` — active features < 50% of baseline
- `value_gap` — customer cites ROI concerns or underutilisation
- `price` — pricing objection in tickets or NPS verbatim
- `competitor` — competitor mentioned in any signal
- `support` — 3+ negative support tickets or escalation
- `relationship` — CSM change, lack of QBRs, engagement drop

## Output Format
Provide your assessment as a JSON block:
```json
{
  "customer_id": "...",
  "risk_level": "low|medium|high|critical",
  "risk_score": 0-100,
  "primary_driver": "...",
  "secondary_driver": "...",
  "triggers_fired": ["..."],
  "churn_probability_30d": 0.0-1.0,
  "churn_probability_60d": 0.0-1.0,
  "churn_probability_90d": 0.0-1.0,
  "nps_current": 0-10,
  "key_signals": ["..."],
  "recommendation": "brief next-step recommendation"
}
```

Always call the tools FIRST before providing your assessment. Do not guess.
"""

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def create_churn_analyst(
    model: str | None = None,
    api_key: str | None = None,
) -> AssistantAgent:
    """Create and return the Churn_Risk_Analyst AssistantAgent.

    Args:
        model: OpenAI model name (default: gpt-4o from env or fallback).
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var).

    Returns:
        A configured AssistantAgent with churn-analysis tools registered.
    """
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )

    agent = AssistantAgent(
        name="Churn_Risk_Analyst",
        model_client=model_client,
        system_message=CHURN_ANALYST_PROMPT,
        tools=[
            get_churn_risk_score,
            predict_churn_probability,
            get_nps_score,
            get_sentiment_trend,
            get_support_ticket_sentiment,
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
        agent = create_churn_analyst()
        response = await agent.on_messages(
            [TextMessage(content="Assess churn risk for customer CUST-001.", source="user")],
            cancellation_token=CancellationToken(),
        )
        print("=== Churn Analyst Response ===")
        print(response.chat_message.content)

    asyncio.run(_test())
