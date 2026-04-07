# File      : main.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Retention Intelligence Room — entry point.

Runs three demo scenarios through the retention room:
  1. Usage decline    (CUST-001) — critical risk, usage_gap driver
  2. Competitor threat (CUST-002) — high risk, competitor driver
  3. Renewal at risk  (CUST-003) — medium risk, value_gap driver

Usage:
    export USE_MOCK_APIS=true
    python main.py                  # Run all three scenarios
    python main.py --scenario 1     # Run only scenario 1
    python main.py --scenario 2     # Run only scenario 2
    python main.py --scenario 3     # Run only scenario 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Resolve imports
# ---------------------------------------------------------------------------
_STAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _STAGE_DIR not in sys.path:
    sys.path.insert(0, _STAGE_DIR)

from groupchats.retention_intelligence_room import (
    evaluate_triggers,
    run_retention_room,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Usage Decline",
        "customer_id": "CUST-001",
        "context": (
            "TechCorp Inc. (CUST-001) has seen a dramatic usage decline over "
            "the past 30 days. Active features dropped from 85% to 28% of "
            "baseline. Their NPS fell from 8 to 4. They have filed 5 support "
            "tickets in the last month, 4 of which are negative. Contract "
            "renewal is in 7 days with no expansion discussion. This is a "
            "$120K ARR Enterprise account with $240K lifetime value."
        ),
        "expected_triggers": [
            "usage_decline_below_50pct_baseline",
            "nps_below_7",
            "3_consecutive_negative_tickets",
            "renewal_under_60_days",
        ],
    },
    {
        "id": 2,
        "name": "Competitor Threat",
        "customer_id": "CUST-002",
        "context": (
            "FinServ Global (CUST-002) is evaluating CompetitorX. Their NPS "
            "dropped from 8 to 6 and their latest survey verbatim explicitly "
            "mentions evaluating alternatives with better integrations. A "
            "support ticket references 'Competitor X has Salesforce "
            "integration'. This is an $84K ARR Professional account. Renewal "
            "is in 84 days but the competitor evaluation is active."
        ),
        "expected_triggers": [
            "nps_below_7",
            "competitor_mentioned",
        ],
    },
    {
        "id": 3,
        "name": "Renewal at Risk",
        "customer_id": "CUST-003",
        "context": (
            "RetailMax (CUST-003) has been filing negative support tickets "
            "about ROI concerns and data mismatches. Their NPS is at 7 (down "
            "from 9) and they have 3 consecutive negative tickets. They are "
            "licensed for integrations but not using them. This is a $60K ARR "
            "Professional account. Renewal is in 146 days but the negative "
            "trend is concerning."
        ),
        "expected_triggers": [
            "3_consecutive_negative_tickets",
        ],
    },
]


# ---------------------------------------------------------------------------
# Scenario runners
# ---------------------------------------------------------------------------


def run_trigger_evaluation_only(scenario: dict[str, Any]) -> dict[str, Any]:
    """Evaluate triggers without running the full room (no LLM needed)."""
    print(f"\n{'#'*60}")
    print(f"# SCENARIO {scenario['id']}: {scenario['name']}")
    print(f"# Customer: {scenario['customer_id']}")
    print(f"{'#'*60}")
    print(f"\nContext: {scenario['context'][:200]}...\n")

    result = evaluate_triggers(scenario["customer_id"])

    print(f"\nTrigger evaluation result:")
    print(json.dumps(result, indent=2))

    # Verify expected triggers
    expected = set(scenario.get("expected_triggers", []))
    actual = set(result.get("triggers_fired", []))
    matched = expected & actual
    missed = expected - actual
    extra = actual - expected

    print(f"\nExpected triggers: {sorted(expected)}")
    print(f"Matched:          {sorted(matched)}")
    if missed:
        print(f"Missed:           {sorted(missed)}")
    if extra:
        print(f"Extra:            {sorted(extra)}")
    print(f"Should activate:  {result['should_activate']}")

    return result


async def run_full_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    """Run a full scenario through the retention room (requires LLM)."""
    print(f"\n{'#'*60}")
    print(f"# SCENARIO {scenario['id']}: {scenario['name']}")
    print(f"# Customer: {scenario['customer_id']}")
    print(f"{'#'*60}")
    print(f"\nContext: {scenario['context'][:200]}...\n")

    result = await run_retention_room(
        customer_id=scenario["customer_id"],
        scenario_context=scenario["context"],
    )

    print(f"\n{'='*60}")
    print(f"SCENARIO {scenario['id']} COMPLETE")
    print(f"{'='*60}")
    print(f"Room activated:    {result['room_activated']}")
    print(f"Triggers fired:    {result['triggers']['triggers_fired']}")
    if result.get("final_response"):
        print(f"\n--- Final Response (first 500 chars) ---")
        print(result["final_response"][:500])
    print()

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run demo scenarios — triggers-only mode or full room mode."""
    parser = argparse.ArgumentParser(
        description="Retention Intelligence Room — Demo Scenarios"
    )
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3],
        help="Run a specific scenario (1, 2, or 3). Default: all.",
    )
    parser.add_argument(
        "--triggers-only",
        action="store_true",
        default=False,
        help="Only evaluate triggers; skip the full LLM-based room.",
    )
    args = parser.parse_args()

    # Select scenarios
    if args.scenario:
        selected = [s for s in SCENARIOS if s["id"] == args.scenario]
    else:
        selected = SCENARIOS

    print(f"\n{'*'*60}")
    print("*  RETENTION INTELLIGENCE ROOM — DEMO")
    print(f"*  Mode: {'Triggers Only' if args.triggers_only else 'Full Room'}")
    print(f"*  Scenarios: {[s['id'] for s in selected]}")
    print(f"*  USE_MOCK_APIS: {os.getenv('USE_MOCK_APIS', 'true')}")
    print(f"{'*'*60}\n")

    if args.triggers_only:
        results = []
        for scenario in selected:
            result = run_trigger_evaluation_only(scenario)
            results.append(result)

        print(f"\n{'='*60}")
        print("SUMMARY — Trigger Evaluation")
        print(f"{'='*60}")
        for scenario, result in zip(selected, results):
            status = "ACTIVATED" if result["should_activate"] else "INACTIVE"
            print(
                f"  Scenario {scenario['id']} ({scenario['name']}): "
                f"{status} — {result['trigger_count']} trigger(s)"
            )
    else:

        async def _run_all() -> list[dict[str, Any]]:
            results = []
            for scenario in selected:
                result = await run_full_scenario(scenario)
                results.append(result)
            return results

        results = asyncio.run(_run_all())

        print(f"\n{'='*60}")
        print("SUMMARY — Full Room Execution")
        print(f"{'='*60}")
        for scenario, result in zip(selected, results):
            status = "ACTIVATED" if result["room_activated"] else "INACTIVE"
            print(
                f"  Scenario {scenario['id']} ({scenario['name']}): "
                f"{status} — {result['triggers']['trigger_count']} trigger(s)"
            )


if __name__ == "__main__":
    main()
