# File      : close_offer_tools.py
# Stage     : 3 — Decision
# Chapter   : 7–8
# Framework : LangGraph
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Tools for generating close offers and urgency campaigns.

Every function follows the **USE_MOCK** pattern:
- ``USE_MOCK=true`` (default)  -> deterministic mock data
- ``USE_MOCK=false``           -> calls the real OpenAI API
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_close_offer(deal_value: float, tier: str) -> dict:
    """Build a deterministic close offer based on deal value and tier."""
    discount_pct = 0
    bonus = ""

    if deal_value >= 100_000:
        discount_pct = 15
        bonus = "Complimentary executive onboarding + 3 months premium support"
    elif deal_value >= 50_000:
        discount_pct = 10
        bonus = "Free onboarding workshop + dedicated CSM"
    elif deal_value >= 20_000:
        discount_pct = 7
        bonus = "Extended 45-day trial of premium features"
    else:
        discount_pct = 5
        bonus = "Free migration assistance"

    tier_labels = {
        "starter": "Starter",
        "professional": "Professional",
        "enterprise": "Enterprise",
        "standard": "Professional",  # default mapping
    }
    tier_label = tier_labels.get(tier.lower(), "Professional")

    expiry = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")

    return {
        "offer_type": "close_offer",
        "tier": tier_label,
        "original_value": deal_value,
        "discount_percent": discount_pct,
        "discounted_value": round(deal_value * (1 - discount_pct / 100), 2),
        "bonus": bonus,
        "valid_until": expiry,
        "cta": "Sign by {expiry} to lock in this pricing.".format(expiry=expiry),
        "message": (
            f"We have prepared an exclusive {tier_label} plan offer for your "
            f"team: {discount_pct}% off the annual commitment "
            f"(${deal_value:,.0f} -> ${deal_value * (1 - discount_pct / 100):,.0f}) "
            f"plus {bonus.lower()}.  This offer is valid until {expiry}."
        ),
    }


def _mock_urgency_campaign(contact_id: str, days_stalled: int) -> dict:
    """Build a deterministic urgency / reactivation campaign."""
    if days_stalled > 21:
        urgency = "critical"
        subject = "We have not heard from you — is there anything blocking your decision?"
        body = (
            "Hi there, it has been over three weeks since we last connected.  "
            "We want to make sure you have everything you need.  Our current "
            "promotional pricing ends this Friday — would a quick call help "
            "clear any remaining questions?"
        )
    elif days_stalled > 14:
        urgency = "high"
        subject = "Your exclusive offer expires soon"
        body = (
            "Just a friendly reminder: the custom pricing we discussed is "
            "available for a limited time.  Several teams in your industry "
            "have recently signed up — I would love to share their results "
            "with you.  Can we schedule 15 minutes this week?"
        )
    else:
        urgency = "medium"
        subject = "Checking in on your evaluation"
        body = (
            "I wanted to follow up on your evaluation.  If you have any "
            "outstanding questions or need additional resources, I am here "
            "to help.  Would a product deep-dive session be useful?"
        )

    return {
        "campaign_type": "urgency_reactivation",
        "contact_id": contact_id,
        "days_stalled": days_stalled,
        "urgency_level": urgency,
        "email_subject": subject,
        "email_body": body,
        "channels": ["email", "linkedin_inmail"] if urgency == "critical" else ["email"],
        "follow_up_in_days": 3,
    }


# ---------------------------------------------------------------------------
# Real API helpers
# ---------------------------------------------------------------------------

def _real_generate_close_offer(deal_value: float, tier: str) -> str:
    """Use OpenAI to generate a creative close offer."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a B2B sales strategist.  Generate a compelling, "
                    "personalized close offer in JSON format with keys: "
                    "offer_type, tier, discount_percent, bonus, valid_until, "
                    "message."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Deal value: ${deal_value:,.0f}\n"
                    f"Pricing tier viewed: {tier}\n"
                    "Create a close offer."
                ),
            },
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content or "{}"


def _real_create_urgency_campaign(contact_id: str, days_stalled: int) -> str:
    """Use OpenAI to draft an urgency reactivation campaign."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a demand-gen specialist.  Draft a multi-channel "
                    "urgency reactivation campaign in JSON with keys: "
                    "campaign_type, urgency_level, email_subject, email_body, "
                    "channels, follow_up_in_days."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Contact ID: {contact_id}\n"
                    f"Days stalled in decision: {days_stalled}\n"
                    "Create the campaign."
                ),
            },
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content or "{}"


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

@tool
def generate_close_offer(deal_value: float, tier: str) -> str:
    """Generate a personalised close offer for the prospect.

    Args:
        deal_value: Monetary value of the deal in USD.
        tier: Pricing tier the prospect has been viewing.

    Returns:
        JSON string with the full close offer details.
    """
    if USE_MOCK:
        return json.dumps(_mock_close_offer(deal_value, tier), indent=2)
    return _real_generate_close_offer(deal_value, tier)


@tool
def create_urgency_campaign(contact_id: str, days_stalled: int) -> str:
    """Create an urgency / reactivation campaign for a stalled deal.

    Args:
        contact_id: CRM contact identifier.
        days_stalled: Number of days the deal has been stalled.

    Returns:
        JSON string with the campaign details.
    """
    if USE_MOCK:
        return json.dumps(
            _mock_urgency_campaign(contact_id, days_stalled), indent=2
        )
    return _real_create_urgency_campaign(contact_id, days_stalled)
