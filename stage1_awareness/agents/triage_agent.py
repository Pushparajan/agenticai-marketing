# File      : triage_agent.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Triage Agent — intent-score router.

Reads the intent profile produced by the Discovery Agent and routes
the lead to the appropriate downstream agent:

  * score > 80  -> HighIntentAccelerator (handoff)
  * 40-79       -> NurtureEnrolmentAgent (handoff)
  * < 40        -> Logs as cold prospect with 30-day re-evaluation date
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from agents import Agent, Runner, function_tool, handoff

from stage1_awareness.agents.high_intent_accelerator import high_intent_accelerator
from stage1_awareness.agents.nurture_enrolment_agent import nurture_enrolment_agent
from stage1_awareness.tools.intent_scoring import score_intent_signals

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the Triage Agent.  Your only job is to route leads
based on their intent score.

## Routing Rules
1. If intent score > 80  -> hand off to HighIntentAccelerator.
2. If intent score 40-79 -> hand off to NurtureEnrolmentAgent.
3. If intent score < 40  -> call log_cold_prospect and stop.

## Workflow
1. Call score_lead to obtain the intent profile for the lead.
2. Based on the score and tier, follow the routing rules above.
3. When handing off, include all lead context in your message.
"""

# ---------------------------------------------------------------------------
# Cold-prospect store (in-memory for demo)
# ---------------------------------------------------------------------------

cold_prospects: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@function_tool
def score_lead(contact_email: str) -> str:
    """Score a lead's intent signals and return the profile.

    Args:
        contact_email: The lead's email address.
    """
    profile = score_intent_signals(contact_email)
    return json.dumps(profile)


@function_tool
def log_cold_prospect(
    contact_email: str,
    intent_score: int,
    reason: str,
) -> str:
    """Log a cold prospect for 30-day re-evaluation.

    Args:
        contact_email: The lead's email address.
        intent_score: The computed intent score.
        reason: Brief explanation of why the lead is cold.
    """
    reeval_date = datetime.now(timezone.utc) + timedelta(days=30)
    record = {
        "email": contact_email,
        "intent_score": intent_score,
        "reason": reason,
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "re_evaluation_date": reeval_date.strftime("%Y-%m-%d"),
    }
    cold_prospects.append(record)
    logger.info(
        "Cold prospect logged: %s (score %d) — re-eval on %s",
        contact_email,
        intent_score,
        record["re_evaluation_date"],
    )
    return json.dumps(record)


# ---------------------------------------------------------------------------
# Handoffs
# ---------------------------------------------------------------------------

handoff_to_accelerator = handoff(
    agent=high_intent_accelerator,
    tool_name_override="transfer_to_high_intent_accelerator",
    tool_description_override=(
        "Hand off to the HighIntentAccelerator agent for leads with "
        "intent score above 80."
    ),
)

handoff_to_nurture = handoff(
    agent=nurture_enrolment_agent,
    tool_name_override="transfer_to_nurture_enrolment",
    tool_description_override=(
        "Hand off to the NurtureEnrolmentAgent for leads with "
        "intent score between 40 and 79."
    ),
)


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

triage_agent = Agent(
    name="TriageAgent",
    instructions=SYSTEM_PROMPT,
    model=MODEL,
    tools=[score_lead, log_cold_prospect],
    handoffs=[handoff_to_accelerator, handoff_to_nurture],
)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

async def run_triage(lead: dict[str, Any]) -> dict[str, Any]:
    """Run the triage agent for a single lead.

    The triage agent will score the lead and hand off to the appropriate
    downstream agent, or log it as a cold prospect.

    Args:
        lead: Dict with at minimum ``email``; may also include firstname,
              lastname, company, industry, title, contact_id, source.

    Returns:
        Dict with ``agent`` name and ``output`` from the final agent in
        the handoff chain.
    """
    prompt = (
        f"New lead to triage:\n"
        f"  Email: {lead['email']}\n"
        f"  Name: {lead.get('firstname', '')} {lead.get('lastname', '')}\n"
        f"  Company: {lead.get('company', 'Unknown')}\n"
        f"  Industry: {lead.get('industry', 'Technology')}\n"
        f"  Title: {lead.get('title', 'Marketing Manager')}\n"
        f"  Contact ID: {lead.get('contact_id', 'unknown')}\n"
        f"  Source: {lead.get('source', 'organic')}\n\n"
        f"Score this lead and route them according to the rules."
    )
    logger.info("Running TriageAgent for %s", lead["email"])
    result = await Runner.run(triage_agent, prompt)
    return {
        "agent": result.last_agent.name,
        "output": result.final_output,
    }
