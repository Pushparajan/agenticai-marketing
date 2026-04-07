# File      : retention_intelligence_room.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Retention Intelligence Room — multi-agent group chat.

Orchestrates three specialist agents (Churn Risk Analyst, Retention
Strategist, Commercial Agent) and a UserProxyAgent to produce a
comprehensive intervention_plan JSON for at-risk customers.

## Trigger Conditions (any one fires the room)
1. Usage decline: 30-day active features < 50% of baseline
2. NPS drop below 7
3. 3 consecutive negative support tickets
4. Renewal < 60 days with no expansion discussion
5. Competitor mentioned in any signal
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ---------------------------------------------------------------------------
# Resolve imports
# ---------------------------------------------------------------------------
_STAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _STAGE_DIR not in sys.path:
    sys.path.insert(0, _STAGE_DIR)

from agents.churn_analyst import create_churn_analyst
from agents.retention_strategist import create_retention_strategist
from agents.commercial_agent import create_commercial_agent

from tools.churn_risk_tools import get_churn_risk_score
from tools.nps_sentiment_tools import (
    get_nps_score,
    get_support_ticket_sentiment,
)
from tools.expansion_revenue_tools import get_contract_details

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Trigger evaluation
# ---------------------------------------------------------------------------

TRIGGER_DEFINITIONS = {
    "usage_decline_below_50pct_baseline": (
        "30-day active features < 50% of baseline"
    ),
    "nps_below_7": "NPS score dropped below 7",
    "3_consecutive_negative_tickets": (
        "3 or more consecutive negative support tickets"
    ),
    "renewal_under_60_days": (
        "Renewal < 60 days with no expansion discussion"
    ),
    "competitor_mentioned": "Competitor mentioned in signals",
}


def evaluate_triggers(customer_id: str) -> dict[str, Any]:
    """Evaluate all trigger conditions for a customer.

    Returns a dict with trigger names mapped to booleans, plus a list
    of fired triggers and whether the room should activate.
    """
    # Gather signals from tools (these return JSON strings)
    risk_data = json.loads(get_churn_risk_score(customer_id))
    nps_data = json.loads(get_nps_score(customer_id))
    ticket_data = json.loads(get_support_ticket_sentiment(customer_id))
    contract_data = json.loads(get_contract_details(customer_id))

    triggers: dict[str, bool] = {}

    # 1. Usage decline
    active_pct = risk_data.get("active_features_pct", 1.0)
    baseline_pct = risk_data.get("baseline_features_pct", 1.0)
    triggers["usage_decline_below_50pct_baseline"] = (
        active_pct < 0.50 * baseline_pct
    )

    # 2. NPS below 7
    triggers["nps_below_7"] = nps_data.get("current_nps", 10) < 7

    # 3. Consecutive negative tickets
    triggers["3_consecutive_negative_tickets"] = (
        ticket_data.get("consecutive_negative", 0) >= 3
    )

    # 4. Renewal < 60 days without expansion discussion
    days_to_renewal = contract_data.get("days_to_renewal", 999)
    expansion_discussed = contract_data.get("expansion_discussed", True)
    triggers["renewal_under_60_days"] = (
        days_to_renewal < 60 and not expansion_discussed
    )

    # 5. Competitor mentioned
    verbatim = nps_data.get("verbatim", "").lower()
    ticket_texts = " ".join(
        t.get("subject", "").lower()
        for t in ticket_data.get("tickets", [])
    )
    competitor_keywords = ["competitor", "alternative", "switch", "evaluating"]
    triggers["competitor_mentioned"] = any(
        kw in verbatim or kw in ticket_texts for kw in competitor_keywords
    )

    fired = [name for name, active in triggers.items() if active]

    return {
        "customer_id": customer_id,
        "triggers": triggers,
        "triggers_fired": fired,
        "should_activate": len(fired) > 0,
        "trigger_count": len(fired),
    }


# ---------------------------------------------------------------------------
# Room factory
# ---------------------------------------------------------------------------


def create_retention_room(
    model: str | None = None,
    api_key: str | None = None,
    max_rounds: int = 12,
) -> tuple[RoundRobinGroupChat, UserProxyAgent]:
    """Create the Retention Intelligence Room group chat.

    Args:
        model: OpenAI model name.
        api_key: OpenAI API key.
        max_rounds: Maximum conversation rounds before termination.

    Returns:
        Tuple of (RoundRobinGroupChat, UserProxyAgent).
    """
    churn_analyst = create_churn_analyst(model=model, api_key=api_key)
    retention_strategist = create_retention_strategist(model=model, api_key=api_key)
    commercial_agent = create_commercial_agent(model=model, api_key=api_key)

    user_proxy = UserProxyAgent(
        name="Retention_Coordinator",
    )

    termination = MaxMessageTermination(max_messages=max_rounds) | TextMentionTermination("INTERVENTION_PLAN_COMPLETE")

    team = RoundRobinGroupChat(
        participants=[
            user_proxy,
            churn_analyst,
            retention_strategist,
            commercial_agent,
        ],
        termination_condition=termination,
    )

    return team, user_proxy


# ---------------------------------------------------------------------------
# Run the room
# ---------------------------------------------------------------------------


async def run_retention_room(
    customer_id: str,
    scenario_context: str = "",
    model: str | None = None,
    api_key: str | None = None,
    max_rounds: int = 12,
) -> dict[str, Any]:
    """Evaluate triggers, run the room if needed, and return results.

    Args:
        customer_id: Customer to analyse.
        scenario_context: Additional context for the agents.
        model: OpenAI model name.
        api_key: OpenAI API key.
        max_rounds: Max conversation rounds.

    Returns:
        Dictionary with trigger evaluation, conversation transcript,
        and the final intervention plan.
    """
    logger.info("Evaluating triggers for %s ...", customer_id)
    trigger_result = evaluate_triggers(customer_id)

    print(f"\n{'='*60}")
    print(f"TRIGGER EVALUATION — {customer_id}")
    print(f"{'='*60}")
    print(json.dumps(trigger_result, indent=2))

    if not trigger_result["should_activate"]:
        print(f"\nNo triggers fired for {customer_id}. Room not activated.")
        return {
            "customer_id": customer_id,
            "triggers": trigger_result,
            "room_activated": False,
            "intervention_plan": None,
        }

    print(f"\n{trigger_result['trigger_count']} trigger(s) fired! Activating Retention Intelligence Room ...\n")

    # Build the task message
    fired_descriptions = [
        f"  - {TRIGGER_DEFINITIONS.get(t, t)}"
        for t in trigger_result["triggers_fired"]
    ]
    task = (
        f"RETENTION ALERT for customer {customer_id}\n\n"
        f"Triggers fired:\n" + "\n".join(fired_descriptions) + "\n\n"
        f"Additional context: {scenario_context}\n\n"
        f"Process:\n"
        f"1. Churn_Risk_Analyst: Assess churn risk, classify level and driver.\n"
        f"2. Retention_Strategist: Select intervention and build win-back plan.\n"
        f"3. Commercial_Agent: Calculate retention offer and expansion opportunities.\n\n"
        f"After all agents have contributed, the final speaker should output a "
        f"consolidated intervention_plan JSON and end with INTERVENTION_PLAN_COMPLETE."
    )

    team, _ = create_retention_room(
        model=model, api_key=api_key, max_rounds=max_rounds
    )

    # Collect messages from the stream
    transcript: list[dict[str, str]] = []
    final_content = ""

    async for event in team.run_stream(task=task):
        # event can be a TaskResult or a message
        if hasattr(event, "messages"):
            # TaskResult — extract final messages
            for msg in event.messages:
                source = getattr(msg, "source", "system")
                content = getattr(msg, "content", str(msg))
                if isinstance(content, list):
                    content = " ".join(str(c) for c in content)
                transcript.append({"source": source, "content": content})
                final_content = content
        else:
            source = getattr(event, "source", "system")
            content = getattr(event, "content", str(event))
            if isinstance(content, list):
                content = " ".join(str(c) for c in content)
            print(f"[{source}]: {content[:200]}{'...' if len(content) > 200 else ''}")

    return {
        "customer_id": customer_id,
        "triggers": trigger_result,
        "room_activated": True,
        "transcript_length": len(transcript),
        "final_response": final_content,
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    async def _test() -> None:
        result = await run_retention_room(
            customer_id="CUST-001",
            scenario_context="Usage has dropped dramatically over the past 30 days.",
        )
        print(f"\n{'='*60}")
        print("ROOM RESULT")
        print(f"{'='*60}")
        print(json.dumps(
            {k: v for k, v in result.items() if k != "final_response"},
            indent=2,
        ))
        if result.get("final_response"):
            print("\n--- Final Response ---")
            print(result["final_response"][:1000])

    asyncio.run(_test())
