# File      : main.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Demand-generation demo — entry point.

Processes three sample leads at different intent levels to demonstrate
the full awareness-stage triage flow:

  1. alice@techcorp.com   — high intent  (score > 80)
  2. bob@startup.io       — mid intent   (score 40-79)
  3. charlie@bigco.org    — cold          (score < 40)

Run:
    python -m stage1_awareness.project_demand_gen.main
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sample leads
# ---------------------------------------------------------------------------

SAMPLE_LEADS: list[dict[str, str]] = [
    {
        "email": "alice@techcorp.com",
        "firstname": "Alice",
        "lastname": "Chen",
        "company": "TechCorp Inc.",
        "industry": "Technology",
        "title": "VP Marketing",
        "source": "google_ads",
    },
    {
        "email": "bob@startup.io",
        "firstname": "Bob",
        "lastname": "Martinez",
        "company": "Startup.io",
        "industry": "Developer Tools",
        "title": "Head of Growth",
        "source": "content_download",
    },
    {
        "email": "charlie@bigco.org",
        "firstname": "Charlie",
        "lastname": "Okafor",
        "company": "BigCo International",
        "industry": "Manufacturing",
        "title": "Marketing Coordinator",
        "source": "organic",
    },
]


# ---------------------------------------------------------------------------
# Direct (non-LLM) triage for mock demo
# ---------------------------------------------------------------------------

def run_direct_triage(lead: dict[str, str]) -> dict[str, Any]:
    """Execute the awareness triage pipeline without calling the LLM.

    This function directly invokes the tool functions so the demo works
    in mock mode without an OpenAI API key.
    """
    from stage1_awareness.tools.intent_scoring import score_intent_signals
    from stage1_awareness.tools.crm_tools import create_crm_contact, update_contact_stage
    from stage1_awareness.tools.web_search_tools import search_company_info, get_tech_stack
    from stage1_awareness.guardrails.brand_safety import brand_safety_check

    email = lead["email"]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("Processing lead: %s", email)

    # 1. Enrich
    domain = email.split("@")[1]
    company_info = search_company_info(domain)
    tech_stack = get_tech_stack(domain)

    # 2. Score intent
    intent = score_intent_signals(email)
    score = intent["score"]
    tier = intent["tier"]
    logger.info("  Intent score: %d -> %s", score, tier.upper())

    # 3. Create CRM contact
    crm = create_crm_contact(
        email=email,
        firstname=lead["firstname"],
        lastname=lead["lastname"],
        company=lead["company"],
        source=lead["source"],
    )
    contact_id = crm["contact_id"]

    # 4. Route based on tier
    result: dict[str, Any] = {
        "email": email,
        "intent": intent,
        "company_info": company_info,
        "tech_stack": tech_stack,
        "crm": crm,
    }

    if tier == "high":
        # Fast-track: demo + priority task + outreach
        from stage1_awareness.agents.high_intent_accelerator import _book_demo_mock, _create_task_mock, _mock_outreach
        from datetime import timedelta

        demo = _book_demo_mock(email, f"{lead['firstname']} {lead['lastname']}", lead["company"])
        task = _create_task_mock(contact_id, email, f"Priority follow-up for {lead['company']}")
        outreach = _mock_outreach(
            lead["firstname"], lead["company"],
            lead.get("industry", "Technology"), demo["demo_datetime"],
        )
        safety = brand_safety_check(outreach)
        update_contact_stage(contact_id, "lead")

        result["action"] = "high_intent_accelerator"
        result["demo"] = demo
        result["task"] = task
        result["outreach"] = {"content": outreach, "brand_safety": safety}
        logger.info("  Demo booked, priority CRM task created")

    elif tier == "mid":
        # Nurture enrolment
        from stage1_awareness.agents.nurture_enrolment_agent import FLOW_MAPPINGS
        import uuid

        title = lead.get("title", "").lower()
        if any(kw in title for kw in ["vp market", "cmo"]):
            persona = "vp_marketing"
        elif "growth" in title:
            persona = "head_of_growth"
        elif "demand" in title or "director" in title:
            persona = "director_demand_gen"
        else:
            persona = "default"

        industry = lead.get("industry", "Technology")
        persona_flows = FLOW_MAPPINGS.get(persona, FLOW_MAPPINGS["default"])
        flow_id = persona_flows.get(industry, persona_flows.get("default", "general_awareness_drip"))
        update_contact_stage(contact_id, "marketing_qualified_lead")

        result["action"] = "nurture_enrolment"
        result["persona"] = persona
        result["flow_id"] = flow_id
        result["enrolment_id"] = f"enr_{uuid.uuid4().hex[:8]}"
        logger.info("  Enrolled in nurture flow: %s", flow_id)

    else:
        # Cold — log for re-evaluation
        from datetime import timedelta

        reeval = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        result["action"] = "cold_prospect_logged"
        result["re_evaluation_date"] = reeval
        logger.info("  Logged for 30-day re-evaluation on %s", reeval)

    return result


# ---------------------------------------------------------------------------
# Async runner (uses LLM agents when USE_MOCK is False)
# ---------------------------------------------------------------------------

async def run_with_agents() -> list[dict[str, Any]]:
    """Run the full triage pipeline using OpenAI Agents SDK agents."""
    from stage1_awareness.agents.triage_agent import run_triage
    from stage1_awareness.tools.crm_tools import create_crm_contact

    results: list[dict[str, Any]] = []
    for lead in SAMPLE_LEADS:
        # Ensure CRM record exists
        create_crm_contact(
            email=lead["email"],
            firstname=lead["firstname"],
            lastname=lead["lastname"],
            company=lead["company"],
            source=lead["source"],
        )
        result = await run_triage(lead)
        results.append(result)
        logger.info("Triage result for %s: routed to %s", lead["email"], result["agent"])
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the demand-gen demo."""
    logger.info("=" * 60)
    logger.info("Stage 1 — Awareness: Demand Generation Demo")
    logger.info("USE_MOCK=%s", USE_MOCK)
    logger.info("=" * 60)

    if USE_MOCK:
        # Direct mode — no LLM calls, fully deterministic
        logger.info("Running in DIRECT (mock) mode — no LLM calls required")
        results = [run_direct_triage(lead) for lead in SAMPLE_LEADS]
    else:
        # Agent mode — requires OPENAI_API_KEY
        logger.info("Running in AGENT mode — requires OPENAI_API_KEY")
        results = asyncio.run(run_with_agents())

    # Print summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    for r in results:
        email = r.get("email", r.get("output", "")[:60])
        action = r.get("action", r.get("agent", "unknown"))
        score = r.get("intent", {}).get("score", "N/A")
        logger.info("  %s | score=%s | action=%s", email, score, action)

    logger.info("Demo complete.")


if __name__ == "__main__":
    main()
