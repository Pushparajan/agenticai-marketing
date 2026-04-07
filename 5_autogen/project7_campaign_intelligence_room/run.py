# run.py
# Project 7: Campaign Intelligence Room
# Chapter Reference: Chapter 5 - AutoGen
# Description: CLI runner for the multi-agent campaign intelligence session
# Author: Pushparajan Ramar

"""Campaign Intelligence Room CLI runner.

Launches a collaborative multi-agent planning session where four
specialist agents — MarketAnalyst, CompetitiveIntelAgent,
CampaignStrategist, and BrandSafetyReviewer — work together to
produce a comprehensive campaign plan.

Usage
-----
    # Default demo scenario (Q3 enterprise pipeline campaign)
    python run.py

    # Custom scenario
    python run.py --scenario "Launch a brand awareness campaign for our \
        new AI analytics product targeting CFOs in EMEA"

    # Adjust turn count
    python run.py --max-turns 12

    # JSON-only output
    python run.py --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_DIVIDER = "=" * 72
_SUB_DIVIDER = "-" * 72


def _print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{_DIVIDER}")
    print(f"  {title}")
    print(_DIVIDER)


def _print_conversation(result: Any) -> None:
    """Print the conversation history from a TaskResult."""
    _print_header("CONVERSATION HISTORY")
    for idx, msg in enumerate(result.messages, start=1):
        source = msg.source if hasattr(msg, "source") else "system"
        content = msg.content if hasattr(msg, "content") else str(msg)
        if not isinstance(content, str):
            content = str(content)

        # Truncate very long tool outputs for display
        display_content = content
        if len(display_content) > 1500:
            display_content = display_content[:1500] + "\n  ... [truncated]"

        print(f"\n{_SUB_DIVIDER}")
        print(f"  Turn {idx}  |  Agent: {source}")
        print(_SUB_DIVIDER)
        for line in display_content.split("\n"):
            print(f"  {line}")
    print()


def _print_section(title: str, data: Any) -> None:
    """Print a single plan section with adaptive formatting."""
    print(f"\n  {title:^68}")
    print(f"  {'-' * 68}")
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, list):
                print(f"  {key}:")
                for item in val:
                    if isinstance(item, dict):
                        summary = ", ".join(f"{k}: {v}" for k, v in item.items())
                        print(f"    - {summary}")
                    else:
                        print(f"    - {item}")
            else:
                print(f"  {key}: {val}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                summary = ", ".join(f"{k}: {v}" for k, v in item.items())
                print(f"  - {summary}")
            else:
                print(f"  - {item}")
    else:
        print(f"  {data}")


def _print_campaign_plan(plan: dict[str, Any]) -> None:
    """Print the extracted campaign plan in a readable format."""
    _print_header("FINAL CAMPAIGN PLAN")
    print(f"\n  Campaign:  {plan.get('campaign_name', 'N/A')}")
    print(f"  Objective: {plan.get('objective', 'N/A')}")

    sections = [
        ("MARKET ANALYSIS", "market_analysis"),
        ("COMPETITIVE LANDSCAPE", "competitive_landscape"),
        ("TARGET AUDIENCE", "target_audience"),
        ("CHANNEL MIX", "channels"),
        ("BUDGET", "budget"),
        ("ROI PROJECTION", "roi_projection"),
        ("TIMELINE", "timeline"),
        ("KEY PERFORMANCE INDICATORS", "kpis"),
        ("BRAND SAFETY REVIEW", "brand_safety_review"),
    ]
    for title, key in sections:
        data = plan.get(key)
        if data:
            _print_section(title, data)

    print()


def _print_summary(result: Any, plan: dict[str, Any] | None) -> None:
    """Print session summary."""
    _print_header("SESSION SUMMARY")
    msg_count = len(result.messages)
    agents_seen = set()
    for msg in result.messages:
        source = msg.source if hasattr(msg, "source") else "system"
        agents_seen.add(source)

    print(f"\n  Total messages:    {msg_count}")
    print(f"  Agents involved:   {', '.join(sorted(agents_seen))}")
    print(f"  Plan extracted:    {'Yes' if plan else 'No'}")
    if plan:
        print(f"  Campaign name:     {plan.get('campaign_name', 'N/A')}")
    use_mock = os.getenv("USE_MOCK", "true").lower() == "true"
    print(f"  Mock mode:         {use_mock}")
    print()


# ---------------------------------------------------------------------------
# Main async runner
# ---------------------------------------------------------------------------

async def _run_campaign(
    scenario: str,
    max_turns: int,
    json_output: bool,
) -> None:
    """Run the campaign intelligence session asynchronously."""
    # Import here to avoid circular imports at module level
    from groupchat import run_campaign_room, extract_campaign_plan, DEFAULT_SCENARIO

    effective_scenario = scenario or DEFAULT_SCENARIO

    if not json_output:
        _print_header("CAMPAIGN INTELLIGENCE ROOM")
        print(f"\n  Scenario:\n  {effective_scenario}")
        print(f"\n  Max turns: {max_turns}")
        use_mock = os.getenv("USE_MOCK", "true").lower() == "true"
        print(f"  Mock mode: {use_mock}\n")
        print("  Starting multi-agent session...\n")

    result = await run_campaign_room(
        scenario=effective_scenario,
        max_turns=max_turns,
    )

    plan = extract_campaign_plan(result)

    if json_output:
        output = {
            "campaign_plan": plan,
            "message_count": len(result.messages),
            "scenario": effective_scenario,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_conversation(result)
        if plan:
            _print_campaign_plan(plan)
        else:
            _print_header("CAMPAIGN PLAN")
            print("\n  No structured JSON campaign plan was extracted.")
            print("  Review the conversation above for agent contributions.\n")
        _print_summary(result, plan)


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="campaign_intelligence_room",
        description=(
            "Campaign Intelligence Room — a multi-agent system that "
            "collaboratively produces a comprehensive campaign plan "
            "using market research, competitive analysis, budget "
            "modelling, and brand safety review."
        ),
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="",
        help=(
            "Campaign scenario / brief. Defaults to a Q3 enterprise "
            "pipeline generation scenario if not provided."
        ),
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="Maximum number of agent turns (default: 10).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output the campaign plan as raw JSON only.",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the Campaign Intelligence Room CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        asyncio.run(
            _run_campaign(
                scenario=args.scenario,
                max_turns=args.max_turns,
                json_output=args.json_output,
            )
        )
    except KeyboardInterrupt:
        print("\n\n  Session interrupted by user.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
