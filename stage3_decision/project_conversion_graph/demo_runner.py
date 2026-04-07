# File      : demo_runner.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Simulates a 21-day decision journey for three deal archetypes.

Deal archetypes
---------------
1. **Clean close** — high intent, no objections, closes quickly.
2. **Competitive** — competitor named mid-journey, battlecard dispatched.
3. **Stalled**     — goes cold after day 14, urgency reactivation fires.

Usage
-----
    python -m stage3_decision.project_conversion_graph.demo_runner
"""

from __future__ import annotations

import asyncio
import copy
import os
import sys
import uuid

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from stage3_decision.graph.graph import build_decision_graph


# ---------------------------------------------------------------------------
# Archetype definitions (day-by-day state mutations)
# ---------------------------------------------------------------------------

_BASE_STATE = {
    "contact_id": "",
    "company": "",
    "deal_id": "",
    "deal_value": 0.0,
    "intent_score": 50,
    "days_in_decision": 0,
    "objections_raised": [],
    "competitors_named": [],
    "stakeholders": [],
    "proposal_viewed": False,
    "pricing_tier_viewed": "standard",
    "last_action": "",
    "next_action": "",
    "human_approved": False,
    "messages": [],
}


def _clean_close_timeline() -> list[dict]:
    """Day-by-day mutations for the *clean close* archetype."""
    return [
        {"day": 1, "patch": {"intent_score": 55}},
        {"day": 3, "patch": {"intent_score": 65, "proposal_viewed": True}},
        {"day": 5, "patch": {"intent_score": 78}},
        {"day": 7, "patch": {"intent_score": 88}},  # crosses 85 + proposal
    ]


def _competitive_timeline() -> list[dict]:
    """Day-by-day mutations for the *competitive* archetype."""
    return [
        {"day": 1, "patch": {"intent_score": 50}},
        {"day": 4, "patch": {"intent_score": 58}},
        {"day": 7, "patch": {"intent_score": 55, "competitors_named": ["RivalY"]}},
        {"day": 10, "patch": {"intent_score": 68, "competitors_named": []}},
        {"day": 14, "patch": {"intent_score": 75, "proposal_viewed": True}},
        {"day": 17, "patch": {"intent_score": 87}},  # close ready
    ]


def _stalled_timeline() -> list[dict]:
    """Day-by-day mutations for the *stalled* archetype."""
    return [
        {"day": 1, "patch": {"intent_score": 50}},
        {"day": 4, "patch": {"intent_score": 55}},
        {"day": 7, "patch": {"intent_score": 52}},
        {"day": 10, "patch": {"intent_score": 48}},
        {"day": 14, "patch": {"intent_score": 42}},  # stalls
        {"day": 17, "patch": {"intent_score": 38}},  # urgency fires (>14 days)
        {"day": 21, "patch": {"intent_score": 60, "proposal_viewed": True}},
    ]


ARCHETYPES = [
    {
        "name": "Clean Close",
        "base_overrides": {
            "contact_id": "contact-401",
            "company": "SwiftPay Inc.",
            "deal_id": "deal-401",
            "deal_value": 45000.0,
            "stakeholders": ["VP Sales", "CFO"],
            "pricing_tier_viewed": "professional",
        },
        "timeline": _clean_close_timeline(),
    },
    {
        "name": "Competitive",
        "base_overrides": {
            "contact_id": "contact-402",
            "company": "DataBridge Ltd.",
            "deal_id": "deal-402",
            "deal_value": 62000.0,
            "stakeholders": ["CTO", "Head of Engineering"],
            "pricing_tier_viewed": "enterprise",
        },
        "timeline": _competitive_timeline(),
    },
    {
        "name": "Stalled",
        "base_overrides": {
            "contact_id": "contact-403",
            "company": "MediTrack Health",
            "deal_id": "deal-403",
            "deal_value": 28000.0,
            "stakeholders": ["Director of Operations"],
            "pricing_tier_viewed": "standard",
        },
        "timeline": _stalled_timeline(),
    },
]


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

async def simulate_archetype(graph, archetype: dict) -> None:
    """Run through a full timeline for one deal archetype."""
    name = archetype["name"]
    print(f"\n{'#' * 70}")
    print(f"#  Archetype: {name}")
    print(f"{'#' * 70}")

    state = copy.deepcopy(_BASE_STATE)
    state.update(archetype["base_overrides"])

    thread_id = uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": thread_id}}

    for step in archetype["timeline"]:
        day = step["day"]
        patch = step["patch"]

        # Apply day mutations
        state["days_in_decision"] = day
        state.update(patch)
        # Keep messages from previous iterations
        prev_messages = state.get("messages", [])
        state["messages"] = prev_messages

        print(f"\n  --- Day {day:>2} ---")
        print(f"  Intent: {state['intent_score']}  |  "
              f"Proposal viewed: {state['proposal_viewed']}  |  "
              f"Competitors: {state['competitors_named']}  |  "
              f"Days: {state['days_in_decision']}")

        # Use a fresh thread for each invocation to avoid state conflicts
        thread_id = uuid.uuid4().hex[:12]
        config = {"configurable": {"thread_id": thread_id}}

        # For high-value deals that need human approval, auto-approve for demo.
        # The interrupt_before on pause_for_human_review means ainvoke returns
        # after evaluate_decision_signals (the node *before* the interrupted
        # node).  We detect this by checking the routing function directly.
        from stage3_decision.graph.routing import route_decision_action

        result = await graph.ainvoke(dict(state), config=config)

        if (
            state["deal_value"] > 50_000
            and not state.get("human_approved", False)
            and route_decision_action(state) == "request_human_approval"
        ):
            print("  >> [HUMAN-IN-THE-LOOP] Graph paused — auto-approving for demo...")
            state["human_approved"] = True
            thread_id = uuid.uuid4().hex[:12]
            config = {"configurable": {"thread_id": thread_id}}
            result = await graph.ainvoke(dict(state), config=config)

        action = result.get("last_action", "N/A")
        print(f"  >> Action taken: {action}")

        # Show latest message summary (last message only)
        msgs = result.get("messages", [])
        if msgs:
            last_msg = msgs[-1]
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            # Truncate for readability
            lines = content.split("\n")
            preview = lines[0][:100]
            print(f"  >> Message: {preview}...")

        # Carry forward relevant state for next iteration
        state["last_action"] = result.get("last_action", "")
        state["next_action"] = result.get("next_action", "")
        state["human_approved"] = result.get("human_approved", state.get("human_approved", False))

    print(f"\n  {'=' * 60}")
    print(f"  Archetype '{name}' simulation complete.")
    print(f"  Final action: {state.get('last_action', 'N/A')}")
    print(f"  {'=' * 60}\n")


async def main() -> None:
    """Run the full 21-day simulation for all archetypes."""
    print("\n" + "=" * 70)
    print("  Stage 3 — Decision  |  21-Day Journey Simulation")
    print("=" * 70)

    use_mock = os.getenv("USE_MOCK", "true").lower()
    print(f"\n  USE_MOCK = {use_mock}")
    if use_mock == "true":
        print("  (Running with mock data — set USE_MOCK=false for real APIs)\n")

    graph = build_decision_graph()

    for archetype in ARCHETYPES:
        await simulate_archetype(graph, archetype)

    print("\n" + "=" * 70)
    print("  All archetypes complete.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
