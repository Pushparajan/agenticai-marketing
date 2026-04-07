# File      : high_intent_accelerator.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
High-Intent Accelerator Agent.

Fast-tracks leads whose intent score exceeds 80 by:
  1. Booking a demo slot.
  2. Creating a priority CRM task for the sales team.
  3. Generating a personalised outreach email.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from agents import Agent, Runner, function_tool

from stage1_awareness.tools.crm_tools import update_contact_stage
from stage1_awareness.guardrails.brand_safety import brand_safety_check

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

SYSTEM_PROMPT = """You are the High-Intent Accelerator Agent.

You handle leads that have scored above 80 on the intent scale.  Your goal is
to convert their interest into a booked demo as quickly as possible.

## Workflow
1. Book a demo slot using book_demo.
2. Create a priority CRM task using create_priority_task so the account
   executive follows up within 24 hours.
3. Generate a personalised outreach email using generate_outreach_email.
4. Return a JSON summary with demo_booking, crm_task, and outreach_email.

## Guidelines
- Be responsive and enthusiastic but never pushy.
- Include specific value propositions relevant to the lead's industry.
- Every outreach email must pass brand safety checks.
"""


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@function_tool
def book_demo(
    contact_email: str,
    contact_name: str,
    company: str,
) -> str:
    """Book a product demo for a high-intent prospect.

    Args:
        contact_email: Prospect's email address.
        contact_name: Prospect's full name.
        company: Prospect's company name.
    """
    logger.info("Booking demo for %s at %s (mock=%s)", contact_name, company, USE_MOCK)
    if USE_MOCK:
        result = _book_demo_mock(contact_email, contact_name, company)
    else:
        result = _book_demo_real(contact_email, contact_name, company)
    return json.dumps(result)


@function_tool
def create_priority_task(
    contact_id: str,
    contact_email: str,
    task_description: str,
) -> str:
    """Create a priority follow-up task in the CRM for the sales team.

    Args:
        contact_id: CRM contact identifier.
        contact_email: Contact email for reference.
        task_description: Description of the task.
    """
    logger.info("Creating priority task for %s (mock=%s)", contact_email, USE_MOCK)
    if USE_MOCK:
        result = _create_task_mock(contact_id, contact_email, task_description)
    else:
        result = _create_task_real(contact_id, contact_email, task_description)

    # Also update CRM stage to "lead"
    update_contact_stage(contact_id, "lead")
    return json.dumps(result)


@function_tool
def generate_outreach_email(
    firstname: str,
    company: str,
    industry: str,
    demo_date: str,
) -> str:
    """Generate a personalised outreach email for the booked demo.

    Args:
        firstname: Prospect's first name.
        company: Company name.
        industry: Company industry.
        demo_date: Booked demo date/time string.
    """
    logger.info("Generating outreach email for %s (mock=%s)", firstname, USE_MOCK)
    if USE_MOCK:
        content = _mock_outreach(firstname, company, industry, demo_date)
    else:
        content = _real_outreach(firstname, company, industry, demo_date)

    safety = brand_safety_check(content)
    return json.dumps({"email_body": content, "brand_safety": safety})


# ---------------------------------------------------------------------------
# Mock implementations
# ---------------------------------------------------------------------------

def _book_demo_mock(email: str, name: str, company: str) -> dict[str, Any]:
    demo_time = datetime.now(timezone.utc) + timedelta(days=2, hours=10)
    return {
        "booking_id": f"demo_{uuid.uuid4().hex[:8]}",
        "contact_email": email,
        "contact_name": name,
        "company": company,
        "demo_datetime": demo_time.isoformat(),
        "meeting_link": "https://meetings.example.com/demo/abc123",
        "status": "confirmed",
    }


def _create_task_mock(
    contact_id: str, email: str, description: str
) -> dict[str, Any]:
    return {
        "task_id": f"task_{uuid.uuid4().hex[:8]}",
        "contact_id": contact_id,
        "contact_email": email,
        "description": description,
        "priority": "high",
        "due_date": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "status": "open",
    }


def _mock_outreach(
    firstname: str, company: str, industry: str, demo_date: str
) -> str:
    return (
        f"Hi {firstname},\n\n"
        f"Great news — your demo is confirmed for {demo_date}.\n\n"
        f"During the session we will walk through how {industry} teams like "
        f"{company} are using our platform to accelerate pipeline by up to 35%.\n\n"
        f"In the meantime, here is a brief overview of what we will cover:\n"
        f"- Automated lead scoring and routing\n"
        f"- Multi-channel nurture orchestration\n"
        f"- Real-time intent signal tracking\n\n"
        f"Looking forward to connecting.\n\n"
        f"Best regards"
    )


# ---------------------------------------------------------------------------
# Real API implementations
# ---------------------------------------------------------------------------

def _book_demo_real(email: str, name: str, company: str) -> dict[str, Any]:
    """Create a Calendly / HubSpot meeting link."""
    import httpx

    hubspot_key = os.getenv("HUBSPOT_API_KEY", "")
    try:
        resp = httpx.post(
            "https://api.hubapi.com/crm/v3/objects/meetings",
            json={
                "properties": {
                    "hs_meeting_title": f"Product Demo - {company}",
                    "hs_meeting_start_time": (
                        datetime.now(timezone.utc) + timedelta(days=2, hours=10)
                    ).isoformat(),
                    "hs_meeting_end_time": (
                        datetime.now(timezone.utc) + timedelta(days=2, hours=10, minutes=30)
                    ).isoformat(),
                    "hs_meeting_outcome": "SCHEDULED",
                }
            },
            headers={
                "Authorization": f"Bearer {hubspot_key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "booking_id": data.get("id", ""),
            "contact_email": email,
            "status": "confirmed",
        }
    except Exception as exc:
        logger.error("HubSpot meeting creation error: %s", exc)
        return _book_demo_mock(email, name, company)


def _create_task_real(
    contact_id: str, email: str, description: str
) -> dict[str, Any]:
    """Create a HubSpot task."""
    import httpx

    hubspot_key = os.getenv("HUBSPOT_API_KEY", "")
    try:
        resp = httpx.post(
            "https://api.hubapi.com/crm/v3/objects/tasks",
            json={
                "properties": {
                    "hs_task_subject": f"Priority follow-up: {email}",
                    "hs_task_body": description,
                    "hs_task_priority": "HIGH",
                    "hs_task_status": "NOT_STARTED",
                    "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                }
            },
            headers={
                "Authorization": f"Bearer {hubspot_key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "task_id": data.get("id", ""),
            "contact_id": contact_id,
            "priority": "high",
            "status": "open",
        }
    except Exception as exc:
        logger.error("HubSpot task creation error: %s", exc)
        return _create_task_mock(contact_id, email, description)


def _real_outreach(
    firstname: str, company: str, industry: str, demo_date: str
) -> str:
    """Use OpenAI to generate outreach content."""
    import httpx

    api_key = os.getenv("OPENAI_API_KEY", "")
    prompt = (
        f"Write a short outreach email to {firstname} at {company} ({industry}). "
        f"Demo date: {demo_date}. Keep it under 120 words, professional, value-driven."
    )
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.error("OpenAI outreach generation error: %s", exc)
        return _mock_outreach(firstname, company, industry, demo_date)


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

high_intent_accelerator = Agent(
    name="HighIntentAccelerator",
    instructions=SYSTEM_PROMPT,
    model=MODEL,
    tools=[book_demo, create_priority_task, generate_outreach_email],
)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

async def run_accelerator(lead: dict[str, Any]) -> dict[str, Any]:
    """Run the high-intent accelerator for a qualified lead.

    Args:
        lead: Dict with email, firstname, lastname, company, industry,
              contact_id, intent_score.

    Returns:
        Agent output with demo booking, CRM task, and outreach email.
    """
    prompt = (
        f"High-intent lead detected (score {lead.get('intent_score', 'N/A')}):\n"
        f"  Email: {lead['email']}\n"
        f"  Name: {lead['firstname']} {lead['lastname']}\n"
        f"  Company: {lead['company']}\n"
        f"  Industry: {lead.get('industry', 'Technology')}\n"
        f"  Contact ID: {lead.get('contact_id', 'unknown')}\n\n"
        f"Execute the full accelerator workflow."
    )
    logger.info("Running HighIntentAccelerator for %s", lead["email"])
    result = await Runner.run(high_intent_accelerator, prompt)
    return {"agent": "HighIntentAccelerator", "output": result.final_output}
