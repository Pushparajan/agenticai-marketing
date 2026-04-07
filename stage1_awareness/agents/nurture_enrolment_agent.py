# File      : nurture_enrolment_agent.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Nurture Enrolment Agent.

Enrols mid-intent leads (score 40-79) into the appropriate Klaviyo
nurture flow based on persona, industry, and behavioural signals.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from agents import Agent, Runner, function_tool

from stage1_awareness.tools.crm_tools import update_contact_stage

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
# Klaviyo flow mappings
# ---------------------------------------------------------------------------

FLOW_MAPPINGS: dict[str, dict[str, str]] = {
    "vp_marketing": {
        "Technology": "saas_eval_drip",
        "Financial Services": "finserv_compliance_nurture",
        "Healthcare": "healthcare_roi_sequence",
        "default": "general_marketing_leader_drip",
    },
    "head_of_growth": {
        "Technology": "growth_playbook_series",
        "Financial Services": "finserv_growth_sequence",
        "Healthcare": "healthcare_growth_nurture",
        "default": "general_growth_drip",
    },
    "director_demand_gen": {
        "Technology": "saas_eval_drip",
        "Financial Services": "finserv_demandgen_nurture",
        "Healthcare": "healthcare_demandgen_series",
        "default": "general_demandgen_drip",
    },
    "default": {
        "default": "general_awareness_drip",
    },
}

SYSTEM_PROMPT = """You are the Nurture Enrolment Agent.

You handle mid-intent leads (score 40-79).  Your goal is to keep them
engaged through educational content until they are ready for a sales
conversation.

## Workflow
1. Determine the best persona category for the lead using select_persona.
2. Select and enrol the lead into the matching Klaviyo flow using enrol_in_flow.
3. Update the CRM stage to "marketing_qualified_lead".
4. Return a JSON summary with persona, selected_flow, enrolment_result,
   and crm_update.
"""


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@function_tool
def select_persona(title: str) -> str:
    """Map a job title to an internal persona category.

    Args:
        title: The lead's job title.
    """
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["vp market", "vice president market", "cmo"]):
        persona = "vp_marketing"
    elif any(kw in title_lower for kw in ["growth", "head of growth"]):
        persona = "head_of_growth"
    elif any(kw in title_lower for kw in ["demand gen", "demand generation", "director"]):
        persona = "director_demand_gen"
    else:
        persona = "default"
    logger.info("Mapped title '%s' to persona '%s'", title, persona)
    return json.dumps({"title": title, "persona": persona})


@function_tool
def enrol_in_flow(
    contact_email: str,
    persona: str,
    industry: str,
) -> str:
    """Enrol a contact into the matching Klaviyo nurture flow.

    Args:
        contact_email: The contact's email address.
        persona: Internal persona category.
        industry: Company industry.
    """
    # Select flow
    persona_flows = FLOW_MAPPINGS.get(persona, FLOW_MAPPINGS["default"])
    flow_id = persona_flows.get(industry, persona_flows.get("default", "general_awareness_drip"))

    logger.info(
        "Enrolling %s in flow '%s' (persona=%s, industry=%s, mock=%s)",
        contact_email, flow_id, persona, industry, USE_MOCK,
    )

    if USE_MOCK:
        result = _enrol_mock(contact_email, flow_id)
    else:
        result = _enrol_real(contact_email, flow_id)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Mock / Real enrolment
# ---------------------------------------------------------------------------

def _enrol_mock(email: str, flow_id: str) -> dict[str, Any]:
    """Simulate Klaviyo flow enrolment."""
    return {
        "enrolment_id": f"enr_{uuid.uuid4().hex[:8]}",
        "email": email,
        "flow_id": flow_id,
        "status": "enrolled",
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
    }


def _enrol_real(email: str, flow_id: str) -> dict[str, Any]:
    """Add a profile to a Klaviyo flow via the API."""
    import httpx

    klaviyo_key = os.getenv("KLAVIYO_API_KEY", "")
    try:
        # Ensure profile exists
        profile_resp = httpx.post(
            "https://a.klaviyo.com/api/profiles/",
            json={
                "data": {
                    "type": "profile",
                    "attributes": {"email": email},
                }
            },
            headers={
                "Authorization": f"Klaviyo-API-Key {klaviyo_key}",
                "Content-Type": "application/json",
                "revision": "2024-02-15",
            },
            timeout=10,
        )
        profile_id = profile_resp.json().get("data", {}).get("id", "")

        # Trigger flow via event
        httpx.post(
            "https://a.klaviyo.com/api/events/",
            json={
                "data": {
                    "type": "event",
                    "attributes": {
                        "metric": {"data": {"type": "metric", "attributes": {"name": f"Nurture Enrolment - {flow_id}"}}},
                        "profile": {"data": {"type": "profile", "id": profile_id}},
                        "properties": {"flow_id": flow_id},
                    },
                }
            },
            headers={
                "Authorization": f"Klaviyo-API-Key {klaviyo_key}",
                "Content-Type": "application/json",
                "revision": "2024-02-15",
            },
            timeout=10,
        )
        return {
            "enrolment_id": profile_id,
            "email": email,
            "flow_id": flow_id,
            "status": "enrolled",
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error("Klaviyo enrolment error: %s", exc)
        return {"email": email, "flow_id": flow_id, "status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

nurture_enrolment_agent = Agent(
    name="NurtureEnrolmentAgent",
    instructions=SYSTEM_PROMPT,
    model=MODEL,
    tools=[select_persona, enrol_in_flow],
)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

async def run_nurture_enrolment(lead: dict[str, Any]) -> dict[str, Any]:
    """Enrol a mid-intent lead into the right nurture sequence.

    Args:
        lead: Dict with email, firstname, lastname, company, industry,
              title, contact_id, intent_score.

    Returns:
        Agent output with persona, flow, and enrolment details.
    """
    prompt = (
        f"Mid-intent lead for nurture enrolment (score {lead.get('intent_score', 'N/A')}):\n"
        f"  Email: {lead['email']}\n"
        f"  Name: {lead['firstname']} {lead['lastname']}\n"
        f"  Company: {lead['company']}\n"
        f"  Industry: {lead.get('industry', 'Technology')}\n"
        f"  Title: {lead.get('title', 'Marketing Manager')}\n"
        f"  Contact ID: {lead.get('contact_id', 'unknown')}\n\n"
        f"Select the right persona and enrol them in the matching nurture flow, "
        f"then update their CRM stage."
    )
    logger.info("Running NurtureEnrolmentAgent for %s", lead["email"])

    result = await Runner.run(nurture_enrolment_agent, prompt)

    # Update CRM stage
    contact_id = lead.get("contact_id", "")
    if contact_id:
        update_contact_stage(contact_id, "marketing_qualified_lead")

    return {"agent": "NurtureEnrolmentAgent", "output": result.final_output}
