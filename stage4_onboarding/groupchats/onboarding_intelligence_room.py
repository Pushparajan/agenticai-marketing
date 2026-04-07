# File      : onboarding_intelligence_room.py
# Stage     : 4 — Onboarding
# Chapter   : 9
# Framework : AutoGen
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""Onboarding Intelligence Room — a RoundRobinGroupChat of three specialist
agents that collaboratively produce a structured onboarding action plan.

Agents
------
1. **ProductSpecialist** — analyses usage heatmaps, feature completion, and
   friction points to identify the *aha* feature.
2. **CustomerSuccessAgent** — evaluates adoption score, support tickets, and
   sentiment to design the activation sequence and check-in schedule.
3. **OnboardingCoordinator** — synthesises both outputs into a final JSON
   onboarding plan.

A ``UserProxyAgent`` (``human_input_mode='NEVER'``) injects the initial
customer brief and collects the final output.

Trigger : New customer within first 30 days of sign-up.
Input   : Customer profile + first-week usage data.
Output  : Structured onboarding action plan JSON.
Dispatch: Email to CS team + HubSpot task.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat

from stage4_onboarding.agents.product_specialist import create_product_specialist
from stage4_onboarding.agents.cs_agent import create_cs_agent
from stage4_onboarding.agents.onboarding_coordinator import create_onboarding_coordinator
from stage4_onboarding.tools.support_ticket_tools import create_onboarding_task

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Mock dispatch helpers
# ---------------------------------------------------------------------------


def _send_cs_email(plan: Dict[str, Any]) -> Dict[str, str]:
    """Dispatch the onboarding plan to the CS team via email."""
    if USE_MOCK:
        print(f"  [MOCK] Email sent to CS team for customer {plan.get('customer_id', '?')}")
        return {"status": "sent", "to": "cs-team@example.com"}
    # Real implementation would use SendGrid / SES / SMTP
    import httpx

    resp = httpx.post(
        os.getenv("EMAIL_API_URL", "https://email.example.com/api/send"),
        json={
            "to": "cs-team@example.com",
            "subject": f"Onboarding Plan: {plan.get('customer_id')}",
            "body": json.dumps(plan, indent=2),
        },
        headers={"Authorization": f"Bearer {os.getenv('EMAIL_API_KEY', '')}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _create_hubspot_task(plan: Dict[str, Any]) -> str:
    """Create a HubSpot task from the onboarding plan."""
    customer_id = plan.get("customer_id", "unknown")
    owner = plan.get("owner", "cs-team")
    title = (
        f"Onboarding follow-up: activate '{plan.get('aha_feature', 'N/A')}' "
        f"for {customer_id}"
    )
    return create_onboarding_task(customer_id, title, owner)


# ---------------------------------------------------------------------------
# Room builder
# ---------------------------------------------------------------------------


def build_onboarding_room(
    model: str | None = None,
    api_key: str | None = None,
    max_rounds: int = 8,
) -> RoundRobinGroupChat:
    """Construct the Onboarding Intelligence Room group chat.

    Returns a ``RoundRobinGroupChat`` with four participants ready to
    receive a task string via ``run()`` or ``run_stream()``.
    """
    product_specialist = create_product_specialist(model=model, api_key=api_key)
    cs_agent = create_cs_agent(model=model, api_key=api_key)
    coordinator = create_onboarding_coordinator(model=model, api_key=api_key)

    user_proxy = UserProxyAgent(
        name="OnboardingTrigger",
        description=(
            "Automated trigger that supplies the customer profile and "
            "first-week usage data to kick off the onboarding analysis."
        ),
    )

    termination = MaxMessageTermination(max_messages=max_rounds)

    team = RoundRobinGroupChat(
        participants=[user_proxy, product_specialist, cs_agent, coordinator],
        termination_condition=termination,
        max_turns=max_rounds,
    )
    return team


def _build_customer_brief(profile: Dict[str, Any]) -> str:
    """Format a customer profile dict into a natural-language brief."""
    return (
        f"NEW ONBOARDING ANALYSIS REQUEST\n"
        f"================================\n"
        f"Customer ID   : {profile['customer_id']}\n"
        f"Company       : {profile['company']}\n"
        f"Industry      : {profile['industry']}\n"
        f"Plan          : {profile['plan']}\n"
        f"Signup Date   : {profile['signup_date']}\n"
        f"Days Since    : {profile['days_since_signup']}\n"
        f"Primary Contact: {profile['contact_name']} ({profile['contact_role']})\n"
        f"Team Size     : {profile['team_size']}\n"
        f"Goals         : {profile.get('goals', 'Not specified')}\n\n"
        f"Please analyse this customer's first-week usage and produce a "
        f"structured onboarding action plan. The Product Specialist should "
        f"start by examining usage data, then the Customer Success Agent "
        f"should evaluate adoption and support signals, and finally the "
        f"Onboarding Coordinator should synthesise everything into the "
        f"final JSON plan."
    )


def _extract_json_plan(result_text: str) -> Optional[Dict[str, Any]]:
    """Best-effort extraction of the JSON plan from the final message."""
    # Try to find JSON in the text
    text = result_text.strip()
    # Remove markdown fences if present
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()
    # Try finding a JSON object
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        candidate = text[brace_start : brace_end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    return None


# ---------------------------------------------------------------------------
# Public runner
# ---------------------------------------------------------------------------


async def run_onboarding_analysis(
    customer_profile: Dict[str, Any],
    model: str | None = None,
    api_key: str | None = None,
    dispatch: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Run the full onboarding intelligence room for a customer.

    Parameters
    ----------
    customer_profile : dict
        Must contain: customer_id, company, industry, plan, signup_date,
        days_since_signup, contact_name, contact_role, team_size.
    model : str, optional
        LLM model name.
    api_key : str, optional
        LLM API key.
    dispatch : bool
        Whether to dispatch email + HubSpot task after analysis.
    verbose : bool
        Print intermediate messages to stdout.

    Returns
    -------
    dict
        The structured onboarding action plan.
    """
    team = build_onboarding_room(model=model, api_key=api_key)
    brief = _build_customer_brief(customer_profile)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Onboarding Intelligence Room — {customer_profile['customer_id']}")
        print(f"  {customer_profile['company']} | {customer_profile['industry']}")
        print(f"{'='*60}\n")

    # Stream messages for visibility
    last_message = ""
    async for message in team.run_stream(task=brief):
        # TaskResult is the final item in the stream
        if hasattr(message, "messages"):
            # This is the TaskResult
            if message.messages:
                last_message = message.messages[-1].content
            break
        if verbose and hasattr(message, "content") and hasattr(message, "source"):
            source = getattr(message, "source", "?")
            content = getattr(message, "content", "")
            if isinstance(content, str) and content.strip():
                print(f"  [{source}]: {content[:200]}{'...' if len(content) > 200 else ''}")

    # Extract JSON plan from coordinator's output
    plan = _extract_json_plan(last_message) if isinstance(last_message, str) else None

    if plan is None:
        plan = {
            "customer_id": customer_profile["customer_id"],
            "aha_feature": "unknown",
            "activation_sequence": [],
            "first_check_in_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "risk_flags": ["Could not parse coordinator output"],
            "recommended_content": [],
            "owner": "cs-team",
            "raw_output": last_message if isinstance(last_message, str) else str(last_message),
        }

    # Ensure customer_id is set
    plan.setdefault("customer_id", customer_profile["customer_id"])

    # Dispatch
    if dispatch:
        if verbose:
            print(f"\n  --- Dispatching onboarding plan ---")
        _send_cs_email(plan)
        task_result = _create_hubspot_task(plan)
        if verbose:
            print(f"  [DISPATCH] HubSpot task created: {task_result[:120]}")

    if verbose:
        print(f"\n  Final Onboarding Plan:")
        print(f"  {json.dumps(plan, indent=2)}")

    return plan
