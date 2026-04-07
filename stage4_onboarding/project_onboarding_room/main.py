# File      : main.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Entry point for the Onboarding Intelligence Room demo.

Runs two sample customer profiles through the full onboarding analysis:
  1. CUST-1001 — a smooth, high-adoption new customer.
  2. CUST-1002 — a struggling, low-adoption customer at risk of churn.

Usage
-----
    # Mock mode (default — no API keys needed)
    python -m stage4_onboarding.project_onboarding_room.main

    # Real mode (requires OPENAI_API_KEY + integrations)
    USE_MOCK=false OPENAI_API_KEY=sk-... python -m stage4_onboarding.project_onboarding_room.main
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Ensure project root is importable when run directly
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from stage4_onboarding.groupchats.onboarding_intelligence_room import (
    run_onboarding_analysis,
)

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Sample customer profiles
# ---------------------------------------------------------------------------

SAMPLE_CUSTOMERS: List[Dict[str, Any]] = [
    {
        "customer_id": "CUST-1001",
        "company": "TechNova Solutions",
        "industry": "SaaS / Technology",
        "plan": "standard",
        "signup_date": "2026-03-28",
        "days_since_signup": 10,
        "contact_name": "Alice Chen",
        "contact_role": "VP of Marketing",
        "team_size": 8,
        "goals": "Centralise marketing analytics and automate weekly reports",
        "scenario": "SMOOTH ONBOARDING",
    },
    {
        "customer_id": "CUST-1002",
        "company": "RetailEdge Inc.",
        "industry": "Retail / E-commerce",
        "plan": "standard",
        "signup_date": "2026-03-25",
        "days_since_signup": 13,
        "contact_name": "Bob Martinez",
        "contact_role": "Marketing Manager",
        "team_size": 3,
        "goals": "Track campaign ROI across channels",
        "scenario": "STRUGGLING ONBOARDING",
    },
]


# ---------------------------------------------------------------------------
# Mock-mode fallback runner
# ---------------------------------------------------------------------------


def _mock_onboarding_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a deterministic mock onboarding plan without calling any LLM.

    This allows the demo to run end-to-end even when no OPENAI_API_KEY is
    set and USE_MOCK=true.
    """
    from stage4_onboarding.tools.product_usage_tools import (
        get_adoption_score,
        get_feature_completion_rate,
        get_usage_heatmap,
        identify_friction_points,
    )
    from stage4_onboarding.tools.onboarding_milestone_tools import (
        get_time_to_value,
    )
    from stage4_onboarding.tools.support_ticket_tools import (
        create_onboarding_task,
        get_recent_tickets,
        get_sentiment_score,
    )

    cid = profile["customer_id"]
    print(f"\n{'='*60}")
    print(f"  Onboarding Intelligence Room — {cid}")
    print(f"  {profile['company']} | {profile['industry']}")
    print(f"  Scenario: {profile.get('scenario', 'N/A')}")
    print(f"{'='*60}")

    # --- Product Specialist phase ---
    print(f"\n  [ProductSpecialist] Analysing usage data...")
    heatmap = json.loads(get_usage_heatmap(cid, 7))
    completion = json.loads(get_feature_completion_rate(cid))
    friction = json.loads(identify_friction_points(cid))

    # Determine aha feature: the one with most sessions
    features = heatmap.get("features", {})
    aha_feature = max(features, key=lambda f: features[f]["sessions"]) if features else "dashboard"
    print(f"  [ProductSpecialist] Aha feature identified: '{aha_feature}'")
    print(f"  [ProductSpecialist] Completion rate: {completion.get('completion_rate', 0):.0%}")
    print(f"  [ProductSpecialist] Friction points: {friction.get('total_friction_signals', 0)}")

    # --- CS Agent phase ---
    print(f"\n  [CustomerSuccessAgent] Evaluating adoption health...")
    adoption = json.loads(get_adoption_score(cid))
    tickets = json.loads(get_recent_tickets(cid))
    sentiment = json.loads(get_sentiment_score(cid))
    ttv = json.loads(get_time_to_value(cid))

    adoption_score = adoption.get("adoption_score", 0.5)
    sentiment_label = sentiment.get("label", "neutral")
    open_tickets = tickets.get("open_count", 0)
    ttv_status = ttv.get("status", "unknown")

    print(f"  [CustomerSuccessAgent] Adoption score: {adoption_score}")
    print(f"  [CustomerSuccessAgent] Sentiment: {sentiment_label}")
    print(f"  [CustomerSuccessAgent] Open tickets: {open_tickets}")
    print(f"  [CustomerSuccessAgent] Time-to-value: {ttv_status}")

    # Build risk flags
    risk_flags: List[str] = []
    if adoption_score < 0.3:
        risk_flags.append("Very low adoption score — high churn risk")
    if open_tickets >= 2:
        risk_flags.append(f"{open_tickets} open support tickets")
    if sentiment_label == "negative":
        risk_flags.append("Negative sentiment detected")
    if ttv_status == "at_risk":
        risk_flags.append("No first-value event recorded yet")
    for fp in friction.get("friction_points", []):
        risk_flags.append(f"Friction: {fp['area']} — {fp['signal']}")

    # Build activation sequence from pending milestones
    pending = completion.get("pending", [])
    activation_sequence = []
    for milestone in pending:
        label = milestone.replace("_", " ").title()
        activation_sequence.append(f"Complete: {label}")
    if not activation_sequence:
        activation_sequence = ["Explore advanced features", "Schedule team training"]

    # Check-in date
    if adoption_score < 0.3:
        check_in = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        owner = "Sarah Kim (Senior CS Manager)"
    else:
        check_in = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d")
        owner = "James Lee (CS Associate)"

    # Recommended content
    recommended_content = []
    if aha_feature == "dashboard":
        recommended_content.append("Guide: Building Your First Dashboard in 5 Minutes")
        recommended_content.append("Video: Dashboard Best Practices")
    elif aha_feature == "reports":
        recommended_content.append("Guide: Scheduling Automated Reports")
        recommended_content.append("Video: Report Templates Walkthrough")
    else:
        recommended_content.append(f"Guide: Getting Started with {aha_feature.replace('_', ' ').title()}")

    if risk_flags:
        recommended_content.append("Article: Onboarding FAQ and Troubleshooting")
    recommended_content.append("Webinar: Platform Overview for New Customers")

    # --- Coordinator phase ---
    print(f"\n  [OnboardingCoordinator] Synthesising final plan...")

    plan: Dict[str, Any] = {
        "customer_id": cid,
        "aha_feature": aha_feature,
        "activation_sequence": activation_sequence,
        "first_check_in_date": check_in,
        "risk_flags": risk_flags,
        "recommended_content": recommended_content,
        "owner": owner,
    }

    # Dispatch
    print(f"\n  --- Dispatching onboarding plan ---")
    print(f"  [MOCK] Email sent to CS team for customer {cid}")
    task_result = create_onboarding_task(
        cid,
        f"Onboarding follow-up: activate '{aha_feature}' for {cid}",
        owner,
    )
    task_info = json.loads(task_result)
    print(f"  [DISPATCH] HubSpot task created: {task_info.get('task_id', 'N/A')}")

    print(f"\n  Final Onboarding Plan:")
    print(f"  {json.dumps(plan, indent=2)}")

    return plan


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def _run_with_llm() -> List[Dict[str, Any]]:
    """Run the full LLM-backed onboarding analysis for all samples."""
    results: List[Dict[str, Any]] = []
    for profile in SAMPLE_CUSTOMERS:
        plan = await run_onboarding_analysis(
            customer_profile=profile,
            dispatch=True,
            verbose=True,
        )
        results.append(plan)
    return results


def _run_mock_only() -> List[Dict[str, Any]]:
    """Run the deterministic mock path for all sample customers."""
    results: List[Dict[str, Any]] = []
    for profile in SAMPLE_CUSTOMERS:
        plan = _mock_onboarding_plan(profile)
        results.append(plan)
    return results


def main() -> None:
    """Entry point — detects mode and runs the appropriate path."""
    print("\n" + "=" * 60)
    print("  STAGE 4 — ONBOARDING INTELLIGENCE ROOM")
    print("  Framework: AutoGen (pyautogen >= 0.4)")
    print(f"  Mode: {'MOCK' if USE_MOCK else 'LIVE'}")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY", "")
    has_real_key = api_key and not api_key.startswith("sk-mock")

    if USE_MOCK and not has_real_key:
        # Pure mock path — no LLM calls at all
        print("\n  Running in pure mock mode (no LLM calls).\n")
        results = _run_mock_only()
    else:
        # LLM-backed path (works with both mock and real tools)
        print("\n  Running with LLM-backed agents.\n")
        results = asyncio.run(_run_with_llm())

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for plan in results:
        cid = plan.get("customer_id", "?")
        aha = plan.get("aha_feature", "?")
        risks = len(plan.get("risk_flags", []))
        owner = plan.get("owner", "?")
        check = plan.get("first_check_in_date", "?")
        print(f"\n  {cid}:")
        print(f"    Aha Feature     : {aha}")
        print(f"    Risk Flags      : {risks}")
        print(f"    Check-in Date   : {check}")
        print(f"    Owner           : {owner}")

    print("\n" + "=" * 60)
    print("  Demo complete.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
