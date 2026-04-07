# File      : expansion_revenue_tools.py
# Stage     : 5 — Retention
# Chapter   : 10–11
# Framework : AutoGen + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Expansion-revenue and contract management tools.

Provides functions to retrieve contract details, calculate retention offers,
and surface expansion opportunities for at-risk customers.
"""

from __future__ import annotations

import json, logging, os, uuid
from datetime import datetime, timezone
from typing import Any

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_CONTRACTS: dict[str, dict[str, Any]] = {
    "CUST-001": dict(customer_id="CUST-001", company_name="TechCorp Inc.",
        contract_id="CTR-10001", plan="Enterprise", arr=120000, mrr=10000,
        start_date="2025-04-15", end_date="2026-04-14", days_to_renewal=7,
        auto_renew=False, seats_licensed=50, seats_active=22,
        modules_licensed=["core", "analytics", "integrations", "api"],
        modules_active=["core"], expansion_discussed=False,
        last_qbr_date="2025-12-10", csm="Sarah Chen",
        payment_status="current", lifetime_value=240000),
    "CUST-002": dict(customer_id="CUST-002", company_name="FinServ Global",
        contract_id="CTR-10002", plan="Professional", arr=84000, mrr=7000,
        start_date="2025-07-01", end_date="2026-06-30", days_to_renewal=84,
        auto_renew=True, seats_licensed=30, seats_active=25,
        modules_licensed=["core", "analytics"],
        modules_active=["core", "analytics"], expansion_discussed=False,
        last_qbr_date="2026-01-15", csm="James Rodriguez",
        payment_status="current", lifetime_value=168000),
    "CUST-003": dict(customer_id="CUST-003", company_name="RetailMax",
        contract_id="CTR-10003", plan="Professional", arr=60000, mrr=5000,
        start_date="2025-09-01", end_date="2026-08-31", days_to_renewal=146,
        auto_renew=True, seats_licensed=20, seats_active=12,
        modules_licensed=["core", "analytics", "integrations"],
        modules_active=["core"], expansion_discussed=False,
        last_qbr_date="2026-02-01", csm="Lisa Park",
        payment_status="current", lifetime_value=60000),
}

_OFFERS: dict[str, dict[str, Any]] = {
    "CUST-001|critical": dict(customer_id="CUST-001", risk_level="critical",
        max_discount_authorised=25, discount_amount=30000,
        contract_extension_incentive="2 months free on 24-month renewal",
        expansion_credit_offer=15000, total_retention_budget=45000,
        approval_required=True, approver="VP Sales",
        rationale="LTV of $240k justifies significant retention investment."),
    "CUST-002|high": dict(customer_id="CUST-002", risk_level="high",
        max_discount_authorised=15, discount_amount=12600,
        contract_extension_incentive="1 month free on 18-month renewal",
        expansion_credit_offer=8000, total_retention_budget=20600,
        approval_required=True, approver="Sales Director",
        rationale="Competitive threat requires commercial counter-offer."),
    "CUST-003|medium": dict(customer_id="CUST-003", risk_level="medium",
        max_discount_authorised=10, discount_amount=6000,
        contract_extension_incentive="10% off on 12-month early renewal",
        expansion_credit_offer=5000, total_retention_budget=11000,
        approval_required=False, approver="CSM Manager",
        rationale="Value-gap can be addressed with training + modest incentive."),
}

_EXPANSION: dict[str, list[dict[str, Any]]] = {
    "CUST-001": [
        dict(opportunity="Reactivate analytics module", potential_arr_increase=0,
             type="utilization", effort="low",
             description="Licensed for analytics but not using it. Guided onboarding could re-engage 28 users."),
        dict(opportunity="Add AI assistant add-on", potential_arr_increase=24000,
             type="upsell", effort="medium",
             description="Industry peers see 40% efficiency gain with AI assistant."),
    ],
    "CUST-002": [
        dict(opportunity="Upgrade to Enterprise plan", potential_arr_increase=36000,
             type="upsell", effort="medium",
             description="Unlocks API access and advanced integrations for CRM needs."),
        dict(opportunity="Add 20 seats for marketing team", potential_arr_increase=14000,
             type="expansion", effort="low",
             description="Marketing team expressed interest during last QBR."),
    ],
    "CUST-003": [
        dict(opportunity="Activate integrations module", potential_arr_increase=0,
             type="utilization", effort="low",
             description="Licensed but unused. Could solve data-mismatch issues."),
    ],
}

# ---------------------------------------------------------------------------
# Real API helper
# ---------------------------------------------------------------------------

def _api_call(method: str, url_env: str, default_url: str, path: str,
              key_env: str, params: dict | None = None,
              body: dict | None = None) -> dict[str, Any]:
    import httpx
    url = os.getenv(url_env, default_url)
    key = os.getenv(key_env, "")
    headers = {"Authorization": f"Bearer {key}"}
    if method == "GET":
        resp = httpx.get(f"{url}{path}", params=params, headers=headers, timeout=10)
    else:
        resp = httpx.post(f"{url}{path}", json=body, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def _def_contract(cid: str) -> dict[str, Any]:
    return dict(customer_id=cid, company_name="Unknown",
        contract_id=f"CTR-{uuid.uuid4().hex[:6]}", plan="Standard",
        arr=36000, mrr=3000, start_date="2025-01-01", end_date="2026-01-01",
        days_to_renewal=90, auto_renew=True, seats_licensed=10, seats_active=8,
        modules_licensed=["core"], modules_active=["core"],
        expansion_discussed=False, last_qbr_date="", csm="Unassigned",
        payment_status="current", lifetime_value=36000)

def _def_offer(cid: str, rl: str) -> dict[str, Any]:
    return dict(customer_id=cid, risk_level=rl, max_discount_authorised=5,
        discount_amount=1800, contract_extension_incentive="None",
        expansion_credit_offer=0, total_retention_budget=1800,
        approval_required=False, approver="CSM",
        rationale="Standard low-risk retention budget.")

# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def get_contract_details(customer_id: str) -> str:
    """Return contract and subscription details for a customer.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON with plan, ARR, renewal date, seat utilisation, module
        activation, and CSM assignment.
    """
    logger.info("get_contract_details(%s) mock=%s", customer_id, USE_MOCK)
    if USE_MOCK:
        result = _CONTRACTS.get(customer_id, _def_contract(customer_id))
    else:
        try:
            result = _api_call("GET", "CRM_API_URL", "https://crm.internal/api/v1",
                               f"/contracts/{customer_id}", "CRM_API_KEY")
        except Exception as exc:
            logger.warning("CRM API error: %s — mock", exc)
            result = _CONTRACTS.get(customer_id, _def_contract(customer_id))

    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(result, indent=2)


def calculate_retention_offer(customer_id: str, risk_level: str) -> str:
    """Calculate the maximum authorised retention offer for a customer.

    Args:
        customer_id: Unique customer identifier.
        risk_level: One of low, medium, high, critical.

    Returns:
        JSON with max_discount_authorised, contract_extension_incentive,
        expansion_credit_offer, and approval details.
    """
    logger.info("calculate_retention_offer(%s, %s) mock=%s", customer_id, risk_level, USE_MOCK)
    if USE_MOCK:
        key = f"{customer_id}|{risk_level}"
        result = _OFFERS.get(key, _def_offer(customer_id, risk_level))
    else:
        try:
            result = _api_call("POST", "PRICING_API_URL",
                               "https://pricing.internal/api/v1",
                               "/retention-offer", "PRICING_API_KEY",
                               body={"customer_id": customer_id, "risk_level": risk_level})
        except Exception as exc:
            logger.warning("Pricing API error: %s — mock", exc)
            key = f"{customer_id}|{risk_level}"
            result = _OFFERS.get(key, _def_offer(customer_id, risk_level))

    result["calculated_at"] = datetime.now(timezone.utc).isoformat()
    result["offer_id"] = str(uuid.uuid4())
    return json.dumps(result, indent=2)


def get_expansion_opportunities(customer_id: str) -> str:
    """Identify expansion and up-sell opportunities for a customer.

    Args:
        customer_id: Unique customer identifier.

    Returns:
        JSON listing potential expansion opportunities with estimated
        ARR increase and effort level.
    """
    logger.info("get_expansion_opportunities(%s) mock=%s", customer_id, USE_MOCK)
    if USE_MOCK:
        opps = _EXPANSION.get(customer_id, [])
    else:
        try:
            data = _api_call("GET", "CRM_API_URL", "https://crm.internal/api/v1",
                             f"/expansion/{customer_id}", "CRM_API_KEY")
            opps = data.get("opportunities", [])
        except Exception as exc:
            logger.warning("Expansion API error: %s — mock", exc)
            opps = _EXPANSION.get(customer_id, [])

    return json.dumps({
        "customer_id": customer_id,
        "opportunities": opps,
        "total_potential_arr": sum(o.get("potential_arr_increase", 0) for o in opps),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2)
