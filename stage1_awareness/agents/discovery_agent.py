# File      : discovery_agent.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Discovery Agent — first touchpoint in the awareness pipeline.

Responsibilities:
  1. Match incoming leads against the Ideal Customer Profile (ICP).
  2. Enrich leads with firmographic and technographic data.
  3. Score intent signals.
  4. Create / update CRM contacts.
  5. Generate brand-safe first-touch content.

All outbound content is validated through the brand_safety_check guardrail.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from agents import Agent, Runner, function_tool, GuardrailFunctionOutput, InputGuardrail

from stage1_awareness.tools.intent_scoring import score_intent_signals
from stage1_awareness.tools.crm_tools import create_crm_contact
from stage1_awareness.tools.web_search_tools import search_company_info, get_tech_stack
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

SYSTEM_PROMPT = """You are the Discovery Agent for an enterprise B2B SaaS company.

## Ideal Customer Profile (ICP)
- Industry: Technology, Financial Services, Healthcare
- Company size: 50-10,000 employees
- Annual revenue: $10M-$2B
- Role titles: VP Marketing, Head of Growth, CMO, Director of Demand Gen
- Tech stack signals: HubSpot, Salesforce, Segment, Marketo

## Brand Voice
- Professional yet approachable
- Data-driven and specific — cite numbers when possible
- Never aggressive or pushy
- Focus on value and outcomes, not features

## Your Workflow
1. When you receive a new lead, use enrich_firmographics to learn about their company.
2. Use score_intent_signals to gauge their interest level.
3. Create or verify the CRM contact with create_crm_contact.
4. Generate a personalised first-touch message with generate_first_touch_content.
5. Return a JSON summary with: email, company_info, intent_profile, crm_result,
   first_touch_content, and brand_safety_result.

## Routing Rules
- Return the intent score and tier so the triage agent can route appropriately.
- Always include the full intent profile in your response.
"""

# ---------------------------------------------------------------------------
# Tool wrappers registered with the OpenAI Agents SDK
# ---------------------------------------------------------------------------


@function_tool
def tool_score_intent_signals(contact_email: str) -> str:
    """Score a contact's behavioural intent signals.

    Args:
        contact_email: Email address of the prospect.
    """
    result = score_intent_signals(contact_email)
    return json.dumps(result)


@function_tool
def tool_create_crm_contact(
    email: str,
    firstname: str,
    lastname: str,
    company: str,
    source: str,
) -> str:
    """Create a new contact record in the CRM.

    Args:
        email: Contact email.
        firstname: First name.
        lastname: Last name.
        company: Company name.
        source: Lead source.
    """
    result = create_crm_contact(email, firstname, lastname, company, source)
    return json.dumps(result)


@function_tool
def tool_generate_first_touch_content(
    firstname: str,
    company: str,
    industry: str,
    intent_tier: str,
) -> str:
    """Generate a personalised first-touch outreach message.

    Args:
        firstname: Prospect first name.
        company: Company name.
        industry: Company industry.
        intent_tier: Intent tier (high / mid / cold).
    """
    if USE_MOCK:
        content = _mock_first_touch(firstname, company, industry, intent_tier)
    else:
        content = _real_first_touch(firstname, company, industry, intent_tier)

    safety = brand_safety_check(content)
    return json.dumps({
        "content": content,
        "brand_safety": safety,
    })


@function_tool
def tool_enrich_firmographics(domain: str) -> str:
    """Look up firmographic and technographic data for a company domain.

    Args:
        domain: Company web domain.
    """
    company_info = search_company_info(domain)
    tech_stack = get_tech_stack(domain)
    return json.dumps({"company": company_info, "tech_stack": tech_stack})


# ---------------------------------------------------------------------------
# Content generation helpers
# ---------------------------------------------------------------------------

def _mock_first_touch(
    firstname: str, company: str, industry: str, intent_tier: str
) -> str:
    """Generate deterministic mock first-touch content."""
    templates = {
        "high": (
            f"Hi {firstname},\n\n"
            f"I noticed {company} has been researching workflow automation solutions. "
            f"Companies in {industry} typically see a 35% improvement in pipeline velocity "
            f"after adopting our platform.\n\n"
            f"Would you be open to a 15-minute call this week to explore how we can help?\n\n"
            f"Best regards"
        ),
        "mid": (
            f"Hi {firstname},\n\n"
            f"I came across {company} and thought you might find our latest guide on "
            f"'{industry} Marketing Automation Trends' valuable.\n\n"
            f"It covers strategies that teams like yours are using to streamline demand gen.\n\n"
            f"Happy to share — just reply to this email.\n\n"
            f"Best regards"
        ),
        "cold": (
            f"Hi {firstname},\n\n"
            f"We recently published a case study on how {industry} companies are modernising "
            f"their marketing stack. Thought it might be relevant to {company}.\n\n"
            f"Here is the link: https://example.com/case-study/{industry.lower().replace(' ', '-')}\n\n"
            f"Best regards"
        ),
    }
    return templates.get(intent_tier, templates["cold"])


def _real_first_touch(
    firstname: str, company: str, industry: str, intent_tier: str
) -> str:
    """Use OpenAI to generate first-touch content (non-agent call)."""
    import httpx

    api_key = os.getenv("OPENAI_API_KEY", "")
    prompt = (
        f"Write a short, professional first-touch email for {firstname} at "
        f"{company} ({industry}). Intent tier: {intent_tier}. "
        f"Keep it under 100 words. Be value-focused, not pushy."
    )
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250,
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.error("OpenAI content generation error: %s", exc)
        return _mock_first_touch(firstname, company, industry, intent_tier)


# ---------------------------------------------------------------------------
# Brand-safety input guardrail
# ---------------------------------------------------------------------------

async def _brand_safety_guardrail(ctx: Any, agent: Any, input_text: str) -> GuardrailFunctionOutput:
    """Pre-check incoming requests for brand-safety red flags."""
    result = brand_safety_check(input_text)
    return GuardrailFunctionOutput(
        output_info=result,
        tripwire_triggered=not result["passed"],
    )


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

discovery_agent = Agent(
    name="DiscoveryAgent",
    instructions=SYSTEM_PROMPT,
    model=MODEL,
    tools=[
        tool_score_intent_signals,
        tool_create_crm_contact,
        tool_generate_first_touch_content,
        tool_enrich_firmographics,
    ],
    input_guardrails=[
        InputGuardrail(guardrail_function=_brand_safety_guardrail),
    ],
)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

async def run_discovery(lead: dict[str, str]) -> dict[str, Any]:
    """Run the discovery agent for a single lead.

    Args:
        lead: Dict with ``email``, ``firstname``, ``lastname``,
              ``company``, ``source``.

    Returns:
        The agent's final output as a parsed dict (or raw string).
    """
    prompt = (
        f"New lead received:\n"
        f"  Email: {lead['email']}\n"
        f"  First name: {lead['firstname']}\n"
        f"  Last name: {lead['lastname']}\n"
        f"  Company: {lead['company']}\n"
        f"  Source: {lead['source']}\n\n"
        f"Run the full discovery workflow and return the JSON summary."
    )
    logger.info("Running DiscoveryAgent for %s", lead["email"])
    result = await Runner.run(discovery_agent, prompt)
    return {"agent": "DiscoveryAgent", "output": result.final_output}
