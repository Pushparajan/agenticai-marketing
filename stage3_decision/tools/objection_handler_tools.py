# File      : objection_handler_tools.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Tools for handling prospect objections during the Decision stage.

Every function follows the **USE_MOCK** pattern:
- ``USE_MOCK=true`` (default)  -> deterministic mock data
- ``USE_MOCK=false``           -> calls the real OpenAI API
"""

from __future__ import annotations

import json
import os

from langchain_core.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_COMMON_OBJECTIONS: dict[str, list[dict[str, str]]] = {
    "default": [
        {
            "objection": "Too expensive compared to alternatives",
            "frequency": "high",
            "best_response": "Focus on total cost of ownership and ROI.",
        },
        {
            "objection": "We need more time to evaluate",
            "frequency": "medium",
            "best_response": "Offer a guided pilot with clear success metrics.",
        },
        {
            "objection": "Concerned about implementation complexity",
            "frequency": "medium",
            "best_response": "Highlight dedicated onboarding team and average go-live time.",
        },
        {
            "objection": "Not sure about data security and compliance",
            "frequency": "low",
            "best_response": "Share SOC-2 / ISO-27001 certifications and DPA.",
        },
    ],
    "fintech": [
        {
            "objection": "Regulatory compliance uncertainty",
            "frequency": "high",
            "best_response": "Present compliance roadmap and audit trail features.",
        },
        {
            "objection": "Integration with legacy banking systems",
            "frequency": "high",
            "best_response": "Demo pre-built connectors for core-banking APIs.",
        },
    ],
    "healthcare": [
        {
            "objection": "HIPAA and PHI handling concerns",
            "frequency": "high",
            "best_response": "Walk through BAA, encryption-at-rest, and access controls.",
        },
        {
            "objection": "Clinician adoption resistance",
            "frequency": "medium",
            "best_response": "Share adoption playbook and change-management support.",
        },
    ],
}

_MOCK_RESPONSES: dict[str, str] = {
    "too expensive": (
        "I understand cost is a concern.  When our customers compare the total "
        "cost of ownership over 3 years — including the manual work our platform "
        "eliminates — they typically see a 3-4x ROI.  Would it help if I walked "
        "you through a customized ROI model for your team?"
    ),
    "implementation": (
        "Great question.  Our average enterprise go-live is 6 weeks with a "
        "dedicated solutions engineer.  We also offer a phased rollout so you "
        "can start seeing value in the first sprint.  Can I connect you with "
        "our implementation lead for a scoping call?"
    ),
    "security": (
        "Security is our top priority.  We hold SOC-2 Type II, ISO 27001, and "
        "offer a signed DPA on every plan.  All data is encrypted at rest "
        "(AES-256) and in transit (TLS 1.3).  I can share our latest penetration "
        "test summary — would that be useful?"
    ),
    "default": (
        "Thank you for raising that.  Let me address it directly: our platform "
        "is designed with flexibility in mind, and most customers in your "
        "industry have navigated a similar concern.  I would love to set up a "
        "call with one of our customer references who faced the same situation."
    ),
}


# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------

def _real_get_common_objections(industry: str) -> str:
    """Call OpenAI to retrieve common objections for *industry*."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a B2B sales enablement assistant.  Return a JSON "
                    "array of common objections for the given industry.  Each "
                    "element must have keys: objection, frequency, best_response."
                ),
            },
            {
                "role": "user",
                "content": f"List the top 4 objections in the {industry} industry.",
            },
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content or "[]"


def _real_generate_objection_response(objection: str, product: str) -> str:
    """Call OpenAI to craft a persuasive response to *objection*."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior B2B sales coach.  Craft a concise, "
                    "empathetic, and persuasive response to the prospect's "
                    "objection about the given product.  Keep it under 100 words."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Product: {product}\n"
                    f"Objection: {objection}\n"
                    "Write a response the sales rep can use."
                ),
            },
        ],
        temperature=0.6,
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

@tool
def get_common_objections(industry: str) -> str:
    """Return common objections for the given industry as JSON.

    Args:
        industry: Industry vertical (e.g. 'fintech', 'healthcare').

    Returns:
        JSON string with an array of objection objects.
    """
    if USE_MOCK:
        key = industry.lower().strip()
        data = _COMMON_OBJECTIONS.get(key, _COMMON_OBJECTIONS["default"])
        return json.dumps(data, indent=2)
    return _real_get_common_objections(industry)


@tool
def generate_objection_response(objection: str, product: str) -> str:
    """Generate a persuasive response to a prospect's objection.

    Args:
        objection: The prospect's objection text.
        product: The product or service being sold.

    Returns:
        A sales-ready response string.
    """
    if USE_MOCK:
        lower = objection.lower()
        for keyword, resp in _MOCK_RESPONSES.items():
            if keyword in lower:
                return resp
        return _MOCK_RESPONSES["default"]
    return _real_generate_objection_response(objection, product)
