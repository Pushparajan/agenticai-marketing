# File      : main.py
# Stage     : 6 — Advocacy
# Chapter   : 12
# Framework : MCP + OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Entry-point for the Advocacy Activation Agent demo.

Runs three demo scenarios representing common advocate profiles:
  1. High-NPS promoter (CUST-001) — enterprise, high LTV, active community
  2. Recent expander  (CUST-002) — mid-market, recent upsell, NPS 8
  3. Community-active  (CUST-003) — mid-market, very active, NPS 9

Set USE_MOCK_APIS=true (default) to run without external API keys.
Set OPENAI_API_KEY to use the real OpenAI Agents SDK runtime.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import textwrap

# Ensure project root is on sys.path for imports
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from stage6_advocacy.agents.advocacy_activation_agent import (
    advocacy_activation_agent,
    classify_advocacy_action,
    run_advocacy_agent,
)
from stage6_advocacy.tools.nps_tools import get_nps_score
from stage6_advocacy.tools.review_request_tools import (
    check_review_request_cooldown,
    request_g2_review,
)
from stage6_advocacy.tools.referral_programme_tools import (
    trigger_referral_programme,
    create_referral_link,
)
from stage6_advocacy.tools.community_invite_tools import (
    get_community_activity,
    invite_to_community,
    request_case_study_participation,
)
from stage6_advocacy.tools.nps_tools import send_nps_followup

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Demo customer profiles
# ---------------------------------------------------------------------------

DEMO_CUSTOMERS = [
    {
        "id": "CUST-001",
        "label": "High-NPS Promoter (Enterprise)",
        "description": (
            "Sarah at TechCorp — NPS 10, LTV $185K, active community member. "
            "Prime candidate for case study and G2 review."
        ),
    },
    {
        "id": "CUST-002",
        "label": "Recent Expander (Mid-Market)",
        "description": (
            "James at GrowthIO — NPS 8, recent expansion deal. "
            "Ideal for referral programme enrolment."
        ),
    },
    {
        "id": "CUST-003",
        "label": "Community-Active User (Mid-Market)",
        "description": (
            "Mei at CommunityPlus — NPS 9, 67 posts in 90 days, "
            "already a moderator. Explore case study + deeper engagement."
        ),
    },
]

# ---------------------------------------------------------------------------
# Local tool-only demo (no LLM required)
# ---------------------------------------------------------------------------


def run_local_demo() -> None:
    """Execute advocacy workflows using tools directly (no LLM call)."""
    print("=" * 70)
    print("  ADVOCACY ACTIVATION AGENT — LOCAL TOOL DEMO")
    print("  (USE_MOCK_APIS=true, no OpenAI API key required)")
    print("=" * 70)

    for customer in DEMO_CUSTOMERS:
        cid = customer["id"]
        print(f"\n{'─' * 70}")
        print(f"  Customer: {customer['label']}")
        print(f"  {customer['description']}")
        print(f"{'─' * 70}")

        # 1. Retrieve NPS profile
        nps_raw = get_nps_score(cid)
        profile = json.loads(nps_raw)
        print(f"\n  [NPS Profile]")
        print(f"    Score       : {profile.get('nps_score', 'N/A')}")
        print(f"    LTV         : ${profile.get('ltv', 0):,.2f}")
        print(f"    Segment     : {profile.get('segment', 'N/A')}")
        print(f"    Expansion   : {profile.get('recent_expansion', False)}")
        print(f"    Community   : {profile.get('active_community', False)}")

        # 2. Community activity
        activity_raw = get_community_activity(cid)
        activity = json.loads(activity_raw)
        print(f"\n  [Community Activity]")
        print(f"    Engagement  : {activity.get('engagement_score', 0)}/100")
        print(f"    Posts (90d) : {activity.get('posts_last_90_days', 0)}")
        print(f"    Moderator   : {activity.get('is_moderator', False)}")

        # 3. Classify actions
        actions = classify_advocacy_action(profile)
        print(f"\n  [Recommended Actions] {actions}")

        # 4. Execute each action
        for action in actions:
            print(f"\n  >> Executing: {action}")

            if action == "case_study":
                result = request_case_study_participation(
                    cid,
                    use_case=profile.get("comment", "General success story"),
                )
                data = json.loads(result)
                print(f"     Status    : {data.get('status')}")
                print(f"     Incentive : {data.get('incentive')}")

            elif action == "referral_programme":
                tier = "gold" if profile.get("ltv", 0) > 50000 else "silver"
                result = trigger_referral_programme(cid, tier)
                data = json.loads(result)
                print(f"     Status    : {data.get('status', 'enrolled')}")
                print(f"     Tier      : {data.get('programme_tier', tier)}")
                link_result = json.loads(create_referral_link(cid))
                print(f"     Link      : {link_result.get('referral_link')}")

            elif action == "community_moderator":
                result = invite_to_community(
                    profile.get("contact_email", ""),
                    "moderator",
                )
                data = json.loads(result)
                print(f"     Status    : {data.get('status')}")
                print(f"     Join link : {data.get('join_link')}")

            elif action == "g2_review":
                email = profile.get("contact_email", "")
                cooldown_raw = check_review_request_cooldown(email)
                cooldown = json.loads(cooldown_raw)
                if cooldown.get("in_cooldown"):
                    print(f"     SKIPPED   : In cooldown (last request recent)")
                else:
                    result = request_g2_review(
                        email,
                        personalisation_note=(
                            f"Thanks for being a valued customer! "
                            f"Your feedback on G2 would help others "
                            f"discover what you love about our platform."
                        ),
                    )
                    data = json.loads(result)
                    print(f"     Status    : {data.get('status')}")

            elif action == "nps_followup":
                result = send_nps_followup(cid, profile.get("nps_score", 0))
                data = json.loads(result)
                print(f"     Action    : {data.get('action')}")
                print(f"     Message   : {data.get('message', '')[:80]}...")

    print(f"\n{'=' * 70}")
    print("  Demo complete. All actions executed with mock data.")
    print(f"{'=' * 70}\n")


# ---------------------------------------------------------------------------
# Full agent demo (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------


async def run_agent_demo() -> None:
    """Run the full agent demo with all three customer scenarios."""
    print("=" * 70)
    print("  ADVOCACY ACTIVATION AGENT — FULL AGENT DEMO")
    print("  (Using OpenAI Agents SDK with gpt-4.1)")
    print("=" * 70)

    for customer in DEMO_CUSTOMERS:
        print(f"\n{'─' * 70}")
        print(f"  Customer: {customer['label']}")
        print(f"{'─' * 70}")

        prompt = textwrap.dedent(f"""\
            Process the following customer for advocacy activation:

            Customer ID: {customer['id']}
            Context: {customer['description']}

            Please:
            1. Retrieve their NPS score and full profile.
            2. Check their community activity.
            3. Determine which advocacy actions are appropriate using the
               scoring framework.
            4. Execute each recommended action.
            5. Send the appropriate NPS follow-up.
            6. Provide a summary of all actions taken with any relevant
               links and next steps.
        """)

        response = await run_advocacy_agent(prompt)
        print(f"\n{response}\n")

    print(f"\n{'=' * 70}")
    print("  Agent demo complete.")
    print(f"{'=' * 70}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point — choose local or agent demo based on env."""
    os.environ.setdefault("USE_MOCK_APIS", "true")

    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    if "--local" in sys.argv or not has_openai_key:
        if not has_openai_key:
            logger.info(
                "OPENAI_API_KEY not set — running local tool demo. "
                "Set OPENAI_API_KEY or pass --agent to use the full agent."
            )
        run_local_demo()
    else:
        asyncio.run(run_agent_demo())


if __name__ == "__main__":
    main()
