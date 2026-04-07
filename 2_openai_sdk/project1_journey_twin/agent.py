# =============================================================================
# agent.py
# Project: Customer Journey Digital Twin
# Chapter: 2 - OpenAI Agents SDK
# Description: OpenAI Agents SDK agent with buyer-persona system prompt,
#              CRM tools, brand-voice guardrail, HITL pricing escalation,
#              and session persistence.
# Author: Pushparajan Ramar
# =============================================================================
"""Customer Journey Digital Twin agent built on OpenAI Agents SDK."""
from __future__ import annotations

import json, logging, os
from typing import Any

import yaml
from dotenv import load_dotenv
from agents import (  # type: ignore[import-untyped]
    Agent, GuardrailFunctionOutput, OutputGuardrail, Runner, function_tool,
)
from tools import (
    check_pricing_request, get_contact_history,
    get_product_catalogue, log_conversation,
)

load_dotenv()

logger = logging.getLogger("journey_twin.agent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def _load_config() -> dict[str, Any]:
    """Load the full YAML configuration file."""
    with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


CONFIG: dict[str, Any] = _load_config()

# ---------------------------------------------------------------------------
# Session store (in-memory; swap for Redis/DB in production)
# ---------------------------------------------------------------------------
_sessions: dict[str, list[dict[str, str]]] = {}


def get_session(contact_id: str) -> list[dict[str, str]]:
    """Retrieve or create conversation history for a contact.

    Args:
        contact_id: Unique contact identifier.
    Returns:
        Mutable list of message dicts.
    """
    if contact_id not in _sessions:
        _sessions[contact_id] = []
    return _sessions[contact_id]


def clear_session(contact_id: str) -> None:
    """Clear persisted session for a contact."""
    _sessions.pop(contact_id, None)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
def _build_system_prompt() -> str:
    """Build a detailed system prompt from config.yaml persona and brand voice."""
    p = CONFIG["buyer_persona"]
    b = CONFIG["brand_voice"]
    stages = "\n".join(f"  - {s['stage']}: {s['description']}"
                       for s in CONFIG["journey_stages"])
    pains = "\n".join(f"  - {x}" for x in p["pain_points"])
    goals = "\n".join(f"  - {x}" for x in p["goals"])
    rules = "\n".join(f"  - {x}" for x in b["guidelines"])
    banned = ", ".join(f'"{x}"' for x in b.get("prohibited_phrases", []))

    return f"""You are a Customer Journey Digital Twin agent for a marketing
technology company. Support the buyer journey of prospects matching this profile.

== BUYER PERSONA ==
Name: {p['name']} | Title: {p['title']} | Industry: {p['industry']}
Company: {p['company_name']} ({p['company_size']}) | Revenue: {p['annual_revenue']}
Tech Stack: {', '.join(p.get('tech_stack', []))}
Communication: {p.get('preferred_communication', 'Professional')}
Budget Authority: {'Yes' if p.get('budget_authority') else 'No'}
Decision Timeline: {p.get('decision_timeline', 'TBD')}

Pain Points:
{pains}

Goals:
{goals}

== JOURNEY STAGES ==
{stages}

== BRAND VOICE ==
Tone: {b['tone']}
{rules}
Prohibited phrases: {banned}

== INSTRUCTIONS ==
1. Look up contact history and journey stage before responding.
2. Tailor responses to the prospect's stage, pain points, and goals.
3. If the prospect asks about pricing/quotes/discounts, use
   check_pricing_request to flag it, then tell them a sales rep will
   follow up. Do NOT quote specific prices.
4. Log every meaningful interaction via log_conversation.
5. Adhere strictly to brand voice guidelines.
6. Be consultative — ask clarifying questions and offer resources.
"""


# ---------------------------------------------------------------------------
# Tool wrappers for Agents SDK
# ---------------------------------------------------------------------------
@function_tool
def tool_get_contact_history(contact_id: str) -> str:
    """Fetch the contact's engagement timeline and profile from the CRM."""
    return json.dumps(get_contact_history(contact_id), default=str)


@function_tool
def tool_get_product_catalogue() -> str:
    """Retrieve the full product catalog with features and pricing tiers."""
    return json.dumps(get_product_catalogue(), default=str)


@function_tool
def tool_log_conversation(contact_id: str, message: str, sentiment: str) -> str:
    """Log a conversation turn to the CRM with sentiment analysis."""
    return json.dumps(log_conversation(contact_id, message, sentiment), default=str)


@function_tool
def tool_check_pricing_request(message: str) -> str:
    """Check whether a prospect message contains pricing-related questions."""
    return json.dumps(check_pricing_request(message), default=str)


# ---------------------------------------------------------------------------
# Brand voice guardrail
# ---------------------------------------------------------------------------
def brand_voice_check(output_text: str) -> bool:
    """Return True if output contains no prohibited phrases."""
    prohibited = CONFIG.get("brand_voice", {}).get("prohibited_phrases", [])
    lower = output_text.lower()
    for phrase in prohibited:
        if phrase.lower() in lower:
            logger.warning("Brand voice violation: '%s'", phrase)
            return False
    return True


async def _output_guardrail(
    _ctx: Any, _agent: Any, output: Any,
) -> GuardrailFunctionOutput:
    """Output guardrail enforcing brand voice compliance."""
    text = output.response if hasattr(output, "response") else str(output)
    ok = brand_voice_check(text)
    return GuardrailFunctionOutput(
        output_info={"compliant": ok}, tripwire_triggered=not ok)


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------
def create_agent() -> Agent:
    """Create and return the configured Journey Twin agent."""
    agent = Agent(
        name="CustomerJourneyTwin",
        instructions=_build_system_prompt(),
        tools=[tool_get_contact_history, tool_get_product_catalogue,
               tool_log_conversation, tool_check_pricing_request],
        output_guardrails=[OutputGuardrail(guardrail_function=_output_guardrail)],
    )
    logger.info("Agent created with %d tools", len(agent.tools))
    return agent


# ---------------------------------------------------------------------------
# Conversation runner
# ---------------------------------------------------------------------------
async def run_conversation(contact_id: str, user_message: str) -> str:
    """Run a single conversation turn with session persistence and HITL.

    Args:
        contact_id: CRM contact identifier.
        user_message: Latest prospect message.
    Returns:
        Agent's response text (with escalation notice if applicable).
    """
    pricing_check = check_pricing_request(user_message)
    escalation_note = ""
    if pricing_check["is_pricing_request"]:
        escalation_note = (
            "\n\n[ESCALATION NOTICE]: This message has been flagged as a "
            "pricing enquiry. A sales representative has been notified and "
            "will follow up with a personalised proposal.")
        logger.info("HITL escalation triggered for contact %s", contact_id)

    session = get_session(contact_id)
    session.append({"role": "user", "content": user_message})
    agent = create_agent()

    try:
        result = await Runner.run(agent, input=session)
        response_text = result.final_output
    except Exception as exc:
        logger.error("Agent run failed: %s", exc)
        response_text = (
            "I apologise, but I'm having trouble processing your request "
            "right now. Let me connect you with a team member who can help.")

    if not brand_voice_check(response_text):
        response_text = (
            "Thank you for your message. A member of our team will "
            "follow up shortly with a thoughtful response.")
        logger.warning("Brand voice guardrail replaced agent output")

    full_response = response_text + escalation_note
    session.append({"role": "assistant", "content": full_response})
    sentiment = "positive" if pricing_check["is_pricing_request"] else "neutral"
    log_conversation(contact_id, user_message, sentiment)
    return full_response


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio

    async def _demo() -> None:
        """Run a short demo of the agent."""
        print("=" * 60)
        print("Customer Journey Digital Twin — Agent Demo")
        print("=" * 60)
        contact = "demo-contact-001"
        for msg in [
            "Hi, I need a solution to unify our marketing data.",
            "What products do you offer for analytics and attribution?",
            "How much does the Enterprise Suite cost per month?",
        ]:
            print(f"\nUser: {msg}")
            print(f"Agent: {await run_conversation(contact, msg)}")

    asyncio.run(_demo())
