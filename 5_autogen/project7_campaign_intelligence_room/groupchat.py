# groupchat.py
# Project 7: Campaign Intelligence Room
# Chapter Reference: Chapter 5 - AutoGen
# Description: AutoGen GroupChat orchestration for multi-agent campaign planning
# Author: Pushparajan Ramar

"""Campaign Intelligence Room group-chat orchestration.

Sets up an AutoGen RoundRobinGroupChat with four specialist agents and
runs a collaborative campaign planning session.  The agents take turns
contributing market research, competitive analysis, campaign strategy,
and brand safety review to produce a unified campaign plan.

Compatible with pyautogen >= 0.4 (autogen_agentchat API).

Environment variables consumed (via .env):
    USE_MOCK       - "true" (default) or "false"
    OPENAI_API_KEY - Required for LLM calls
    OPENAI_MODEL   - Model name (default "gpt-4o")
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv

from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.base import TaskResult

from agents import create_agents

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SCENARIO: str = (
    "Plan a Q3 pipeline generation campaign for our enterprise segment. "
    "We sell a B2B SaaS marketing automation platform competing with "
    "HubSpot and Salesforce Marketing Cloud. Our target audience is "
    "VP/Director-level marketing leaders at companies with 500-5,000 "
    "employees in North America. Budget range is $40,000-$60,000 for "
    "a 90-day campaign. We want to generate 250+ MQLs and $2M in "
    "qualified pipeline."
)

MAX_TURNS: int = 10


# ---------------------------------------------------------------------------
# Group chat factory
# ---------------------------------------------------------------------------

def create_campaign_room(
    max_turns: int = MAX_TURNS,
) -> RoundRobinGroupChat:
    """Create a RoundRobinGroupChat with all campaign intelligence agents.

    Configures round-robin speaker selection so each specialist agent
    contributes in order:
        MarketAnalyst -> CompetitiveIntelAgent -> CampaignStrategist
        -> BrandSafetyReviewer -> (repeat)

    Args:
        max_turns: Maximum number of agent turns before auto-termination.

    Returns:
        Configured RoundRobinGroupChat ready to run.
    """
    agents_dict = create_agents()

    # Ordered participant list for round-robin
    participants = [
        agents_dict["MarketAnalyst"],
        agents_dict["CompetitiveIntelAgent"],
        agents_dict["CampaignStrategist"],
        agents_dict["BrandSafetyReviewer"],
    ]

    # Termination conditions
    max_msg_termination = MaxMessageTermination(max_messages=max_turns)
    text_termination = TextMentionTermination("CAMPAIGN_PLAN_COMPLETE")

    termination = max_msg_termination | text_termination

    group_chat = RoundRobinGroupChat(
        participants=participants,
        termination_condition=termination,
    )

    log.info(
        "Created Campaign Intelligence Room: %d agents, max_turns=%d",
        len(participants), max_turns,
    )
    return group_chat


# ---------------------------------------------------------------------------
# Run helpers
# ---------------------------------------------------------------------------

async def run_campaign_room(
    scenario: str = DEFAULT_SCENARIO,
    max_turns: int = MAX_TURNS,
) -> TaskResult:
    """Run the Campaign Intelligence Room on a given scenario.

    Creates the group chat, injects the scenario as the initial task,
    and runs the collaborative session to completion.

    Args:
        scenario:  The campaign planning scenario / brief.
        max_turns: Maximum number of agent turns.

    Returns:
        TaskResult containing the full message history.
    """
    group_chat = create_campaign_room(max_turns=max_turns)

    task_message = (
        f"CAMPAIGN BRIEF:\n{scenario}\n\n"
        "INSTRUCTIONS FOR ALL AGENTS:\n"
        "1. Each agent should use their tools to gather data and analysis.\n"
        "2. Build upon the previous agents' contributions.\n"
        "3. The CampaignStrategist should synthesise all inputs into a "
        "structured campaign plan.\n"
        "4. The BrandSafetyReviewer should review the proposed messaging "
        "and flag any compliance issues.\n"
        "5. On the final turn, the CampaignStrategist should output the "
        "complete campaign plan as a JSON object with these keys:\n"
        '   "campaign_name", "objective", "market_analysis", '
        '   "competitive_landscape", "target_audience", "channels", '
        '   "budget", "roi_projection", "timeline", "kpis", '
        '   "brand_safety_review"\n'
        "6. End the final message with the text CAMPAIGN_PLAN_COMPLETE."
    )

    log.info("Starting Campaign Intelligence Room session...")
    result = await group_chat.run(task=task_message)
    log.info(
        "Campaign Intelligence Room session complete: %d messages",
        len(result.messages),
    )
    return result


def extract_campaign_plan(result: TaskResult) -> dict[str, Any] | None:
    """Extract the final JSON campaign plan from the task result.

    Scans messages in reverse order looking for the last JSON block
    produced by the CampaignStrategist.

    Args:
        result: TaskResult from run_campaign_room.

    Returns:
        Parsed campaign plan dict, or None if no JSON block found.
    """
    for message in reversed(result.messages):
        content = message.content if hasattr(message, "content") else str(message)
        if not isinstance(content, str):
            continue

        # Look for JSON blocks in the message
        # Try fenced code blocks first
        json_matches = re.findall(
            r"```(?:json)?\s*\n?([\s\S]*?)\n?```",
            content,
        )
        for match in json_matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and "campaign_name" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue

        # Try finding raw JSON objects
        brace_depth = 0
        start_idx = None
        for i, ch in enumerate(content):
            if ch == "{":
                if brace_depth == 0:
                    start_idx = i
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if brace_depth == 0 and start_idx is not None:
                    candidate = content[start_idx : i + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict) and "campaign_name" in parsed:
                            return parsed
                    except json.JSONDecodeError:
                        pass
                    start_idx = None

    log.warning("No structured campaign plan JSON found in conversation.")
    return None


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def _demo() -> None:
        print("=" * 72)
        print("  Campaign Intelligence Room — GroupChat Demo")
        print("=" * 72)
        print(f"\n  Scenario: {DEFAULT_SCENARIO[:80]}...")
        print(f"  Max turns: {MAX_TURNS}\n")

        result = await run_campaign_room()

        print("\n" + "=" * 72)
        print("  CONVERSATION HISTORY")
        print("=" * 72)
        for msg in result.messages:
            source = msg.source if hasattr(msg, "source") else "system"
            content = msg.content if hasattr(msg, "content") else str(msg)
            preview = content[:200] if isinstance(content, str) else str(content)[:200]
            print(f"\n  [{source}]")
            print(f"  {preview}...")

        plan = extract_campaign_plan(result)
        if plan:
            print("\n" + "=" * 72)
            print("  EXTRACTED CAMPAIGN PLAN")
            print("=" * 72)
            print(json.dumps(plan, indent=2))
        else:
            print("\n  [No structured JSON campaign plan extracted]")

    asyncio.run(_demo())
