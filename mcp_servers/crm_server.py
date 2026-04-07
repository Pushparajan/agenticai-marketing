# File      : crm_server.py
# Stage     : All Stages
# Chapter   : 13-14
# Framework : MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
HubSpot CRM MCP Server
Provides tools for contact management, deal tracking, lifecycle stages,
and journey event logging across all customer journey stages.
"""

import json
import os
import logging
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CRM] %(message)s")
logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("MCP_MOCK", "true").lower() == "true"
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY", "")

mcp = FastMCP("crm-hubspot")


@mcp.tool()
def get_contact(email: str) -> str:
    """Retrieve a HubSpot contact record by email address."""
    logger.info("get_contact called | email=%s", email)
    if not USE_MOCK:
        # Real API: GET /crm/v3/objects/contacts/search
        pass
    return json.dumps({
        "contact_id": "CTX-20481",
        "email": email,
        "first_name": "Sarah",
        "last_name": "Mitchell",
        "company": "NovaTech Solutions",
        "lifecycle_stage": "opportunity",
        "lead_score": 82,
        "last_activity": "2026-04-05T14:23:00Z",
        "source": "organic_search",
        "created_at": "2026-01-15T09:00:00Z",
        "properties": {
            "industry": "SaaS",
            "annual_revenue": "$2.4M",
            "employee_count": 85
        }
    })


@mcp.tool()
def update_lifecycle_stage(contact_id: str, stage: str) -> str:
    """Update the lifecycle stage of a contact (e.g. subscriber, lead, MQL, SQL, opportunity, customer, evangelist)."""
    logger.info("update_lifecycle_stage called | contact_id=%s stage=%s", contact_id, stage)
    if not USE_MOCK:
        # Real API: PATCH /crm/v3/objects/contacts/{contact_id}
        pass
    return json.dumps({
        "contact_id": contact_id,
        "previous_stage": "lead",
        "new_stage": stage,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "status": "success"
    })


@mcp.tool()
def create_contact(email: str, first_name: str, last_name: str, company: str) -> str:
    """Create a new contact in HubSpot CRM."""
    logger.info("create_contact called | email=%s company=%s", email, company)
    if not USE_MOCK:
        # Real API: POST /crm/v3/objects/contacts
        pass
    return json.dumps({
        "contact_id": "CTX-20499",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "company": company,
        "lifecycle_stage": "subscriber",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "created"
    })


@mcp.tool()
def log_journey_event(contact_id: str, event_type: str, stage: str, metadata: str) -> str:
    """Log a customer journey event against a contact (e.g. page_view, demo_request, onboarding_complete)."""
    logger.info("log_journey_event called | contact_id=%s event=%s stage=%s", contact_id, event_type, stage)
    if not USE_MOCK:
        # Real API: POST /crm/v3/timeline/events
        pass
    return json.dumps({
        "event_id": "EVT-88412",
        "contact_id": contact_id,
        "event_type": event_type,
        "journey_stage": stage,
        "metadata": json.loads(metadata) if metadata else {},
        "logged_at": datetime.utcnow().isoformat() + "Z",
        "status": "recorded"
    })


@mcp.tool()
def get_deal(deal_id: str) -> str:
    """Retrieve a HubSpot deal by ID including stage, amount, and close date."""
    logger.info("get_deal called | deal_id=%s", deal_id)
    if not USE_MOCK:
        # Real API: GET /crm/v3/objects/deals/{deal_id}
        pass
    close_date = (datetime.utcnow() + timedelta(days=18)).strftime("%Y-%m-%d")
    return json.dumps({
        "deal_id": deal_id,
        "deal_name": "NovaTech Solutions - Enterprise Plan",
        "stage": "contract_sent",
        "amount": 48000.00,
        "currency": "USD",
        "close_date": close_date,
        "pipeline": "default",
        "owner": "James Rodriguez",
        "associated_contact": "CTX-20481",
        "probability": 0.75,
        "created_at": "2026-02-20T11:30:00Z"
    })


@mcp.tool()
def update_deal_stage(deal_id: str, stage: str) -> str:
    """Move a deal to a new pipeline stage (e.g. qualified, proposal, contract_sent, closed_won)."""
    logger.info("update_deal_stage called | deal_id=%s stage=%s", deal_id, stage)
    if not USE_MOCK:
        # Real API: PATCH /crm/v3/objects/deals/{deal_id}
        pass
    return json.dumps({
        "deal_id": deal_id,
        "previous_stage": "contract_sent",
        "new_stage": stage,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "status": "success"
    })


@mcp.tool()
def create_task(contact_id: str, title: str, due_days: int, owner_email: str) -> str:
    """Create a follow-up task in HubSpot linked to a contact."""
    logger.info("create_task called | contact_id=%s title=%s", contact_id, title)
    if not USE_MOCK:
        # Real API: POST /crm/v3/objects/tasks
        pass
    due_date = (datetime.utcnow() + timedelta(days=due_days)).strftime("%Y-%m-%d")
    return json.dumps({
        "task_id": "TSK-3341",
        "contact_id": contact_id,
        "title": title,
        "due_date": due_date,
        "owner": owner_email,
        "priority": "high",
        "status": "not_started",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })


@mcp.tool()
def bulk_export_contacts(lifecycle_stage: str, limit: int) -> str:
    """Export a batch of contacts filtered by lifecycle stage."""
    logger.info("bulk_export_contacts called | stage=%s limit=%d", lifecycle_stage, limit)
    if not USE_MOCK:
        # Real API: POST /crm/v3/objects/contacts/search
        pass
    contacts = [
        {"contact_id": "CTX-20481", "email": "s.mitchell@novatech.io", "company": "NovaTech Solutions", "lead_score": 82},
        {"contact_id": "CTX-20482", "email": "d.chen@brightpath.com", "company": "BrightPath Analytics", "lead_score": 74},
        {"contact_id": "CTX-20483", "email": "r.patel@vortexlabs.co", "company": "Vortex Labs", "lead_score": 91},
        {"contact_id": "CTX-20484", "email": "l.garcia@summit.dev", "company": "Summit Engineering", "lead_score": 67},
        {"contact_id": "CTX-20485", "email": "a.johnson@peakflow.io", "company": "PeakFlow Systems", "lead_score": 88},
    ]
    return json.dumps({
        "lifecycle_stage": lifecycle_stage,
        "total_matching": 247,
        "exported_count": min(limit, len(contacts)),
        "contacts": contacts[:limit],
        "exported_at": datetime.utcnow().isoformat() + "Z"
    })


if __name__ == "__main__":
    mcp.run()
