"""
Project 2 — Autonomous SDR Outreach Agent
File: tools.py
Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
Framework: OpenAI Agents SDK

Enrichment, CRM, and email dispatch tools with real API integrations
and deterministic mock fallbacks for offline / demo execution.

Each tool follows the pattern:
    if USE_MOCK is False and the relevant API key is set  ->  call the live API
    otherwise  ->  return realistic mock data

Environment variables consumed (via .env):
    USE_MOCK            — "true" (default) or "false"
    CLEARBIT_API_KEY    — Clearbit / Apollo enrichment key
    HUBSPOT_API_KEY     — HubSpot private-app token
    GMAIL_CREDENTIALS   — path to Gmail OAuth credentials JSON
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
CLEARBIT_API_KEY: str = os.getenv("CLEARBIT_API_KEY", "")
HUBSPOT_API_KEY: str = os.getenv("HUBSPOT_API_KEY", "")
GMAIL_CREDENTIALS: str = os.getenv("GMAIL_CREDENTIALS", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mock_id() -> str:
    """Return a short unique identifier for mock objects."""
    return uuid.uuid4().hex[:12]


# ===================================================================
# 1. Firmographic Enrichment
# ===================================================================

def enrich_firmographics(domain: str) -> dict[str, Any]:
    """Look up firmographic data for *domain* (Clearbit / Apollo style).

    Returns a dict with keys: domain, company_name, industry, employee_count,
    annual_revenue, headquarters, tech_stack, funding_stage, timestamp.
    """
    log.info("enrich_firmographics  domain=%s  mock=%s  ts=%s", domain, USE_MOCK, _ts())

    if not USE_MOCK and CLEARBIT_API_KEY:
        try:
            import requests

            resp = requests.get(
                f"https://company.clearbit.com/v2/companies/find?domain={domain}",
                headers={"Authorization": f"Bearer {CLEARBIT_API_KEY}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "domain": domain,
                "company_name": data.get("name", ""),
                "industry": data.get("category", {}).get("industry", ""),
                "employee_count": data.get("metrics", {}).get("employees", 0),
                "annual_revenue": data.get("metrics", {}).get("estimatedAnnualRevenue", ""),
                "headquarters": data.get("geo", {}).get("city", ""),
                "tech_stack": data.get("tech", []),
                "funding_stage": data.get("metrics", {}).get("raised", ""),
                "timestamp": _ts(),
            }
        except Exception as exc:
            log.warning("Clearbit API call failed, falling back to mock: %s", exc)

    # ----- mock fallback -----
    mock_db: dict[str, dict[str, Any]] = {
        "acmecorp.com": {
            "company_name": "Acme Corporation",
            "industry": "Manufacturing",
            "employee_count": 2500,
            "annual_revenue": "$500M-$1B",
            "headquarters": "Chicago, IL",
            "tech_stack": ["Salesforce", "Marketo", "Snowflake"],
            "funding_stage": "Public",
        },
        "startuphq.io": {
            "company_name": "StartupHQ",
            "industry": "SaaS / Developer Tools",
            "employee_count": 85,
            "annual_revenue": "$5M-$10M",
            "headquarters": "San Francisco, CA",
            "tech_stack": ["HubSpot", "Segment", "BigQuery"],
            "funding_stage": "Series A",
        },
        "globalretail.com": {
            "company_name": "Global Retail Inc.",
            "industry": "Retail / E-Commerce",
            "employee_count": 12000,
            "annual_revenue": "$2B-$5B",
            "headquarters": "New York, NY",
            "tech_stack": ["SAP", "Adobe Experience Cloud", "Databricks"],
            "funding_stage": "Public",
        },
    }
    fallback = mock_db.get(domain, {
        "company_name": domain.split(".")[0].title(),
        "industry": "Technology",
        "employee_count": 200,
        "annual_revenue": "$10M-$50M",
        "headquarters": "Austin, TX",
        "tech_stack": ["HubSpot"],
        "funding_stage": "Series B",
    })
    return {"domain": domain, **fallback, "timestamp": _ts()}


# ===================================================================
# 2. HubSpot Contact Lookup
# ===================================================================

def get_hubspot_contact(email: str) -> dict[str, Any]:
    """Fetch a contact record from HubSpot by *email*.

    Returns: contact_id, email, first_name, last_name, title, lifecycle_stage,
    lead_status, last_contacted, region, timestamp.
    """
    log.info("get_hubspot_contact  email=%s  mock=%s  ts=%s", email, USE_MOCK, _ts())

    if not USE_MOCK and HUBSPOT_API_KEY:
        try:
            import requests

            url = (
                "https://api.hubapi.com/crm/v3/objects/contacts/search"
            )
            payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email,
                    }]
                }],
                "properties": [
                    "email", "firstname", "lastname", "jobtitle",
                    "lifecyclestage", "hs_lead_status",
                ],
            }
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if results:
                props = results[0].get("properties", {})
                return {
                    "contact_id": results[0]["id"],
                    "email": props.get("email", email),
                    "first_name": props.get("firstname", ""),
                    "last_name": props.get("lastname", ""),
                    "title": props.get("jobtitle", ""),
                    "lifecycle_stage": props.get("lifecyclestage", ""),
                    "lead_status": props.get("hs_lead_status", ""),
                    "last_contacted": None,
                    "region": "US",
                    "timestamp": _ts(),
                }
        except Exception as exc:
            log.warning("HubSpot API call failed, falling back to mock: %s", exc)

    # ----- mock fallback -----
    mock_contacts: dict[str, dict[str, Any]] = {
        "jdoe@acmecorp.com": {
            "contact_id": "hub-100201",
            "first_name": "Jane",
            "last_name": "Doe",
            "title": "VP of Marketing",
            "lifecycle_stage": "marketingqualifiedlead",
            "lead_status": "OPEN",
            "last_contacted": "2026-03-15T10:00:00Z",
            "region": "US",
        },
        "alex@startuphq.io": {
            "contact_id": "hub-100302",
            "first_name": "Alex",
            "last_name": "Rivera",
            "title": "Head of Growth",
            "lifecycle_stage": "lead",
            "lead_status": "NEW",
            "last_contacted": None,
            "region": "US",
        },
        "chen.wei@globalretail.com": {
            "contact_id": "hub-100403",
            "first_name": "Wei",
            "last_name": "Chen",
            "title": "Chief Digital Officer",
            "lifecycle_stage": "opportunity",
            "lead_status": "IN_PROGRESS",
            "last_contacted": "2026-04-01T14:30:00Z",
            "region": "EU",
        },
    }
    fallback = mock_contacts.get(email, {
        "contact_id": f"hub-{_mock_id()}",
        "first_name": email.split("@")[0].title(),
        "last_name": "Unknown",
        "title": "Manager",
        "lifecycle_stage": "lead",
        "lead_status": "NEW",
        "last_contacted": None,
        "region": "US",
    })
    return {"email": email, **fallback, "timestamp": _ts()}


# ===================================================================
# 3. Recent CRM Activity
# ===================================================================

def get_recent_activity(contact_id: str) -> list[dict[str, Any]]:
    """Return recent CRM engagement events for *contact_id*.

    Each item: type, description, occurred_at.
    """
    log.info("get_recent_activity  contact_id=%s  mock=%s  ts=%s", contact_id, USE_MOCK, _ts())

    if not USE_MOCK and HUBSPOT_API_KEY:
        try:
            import requests

            url = (
                f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
                "/associations/engagements"
            )
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {HUBSPOT_API_KEY}"},
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get("results", [])
            return [
                {
                    "type": item.get("type", "UNKNOWN"),
                    "description": item.get("properties", {}).get("hs_body_preview", ""),
                    "occurred_at": item.get("properties", {}).get("hs_timestamp", ""),
                }
                for item in items[:10]
            ]
        except Exception as exc:
            log.warning("HubSpot activity call failed, falling back to mock: %s", exc)

    # ----- mock fallback -----
    now = datetime.now(timezone.utc)
    mock_activities: dict[str, list[dict[str, Any]]] = {
        "hub-100201": [
            {"type": "EMAIL_OPEN", "description": "Opened 'Q1 Product Update'", "occurred_at": (now - timedelta(days=5)).isoformat()},
            {"type": "PAGE_VIEW", "description": "Visited /pricing", "occurred_at": (now - timedelta(days=3)).isoformat()},
            {"type": "FORM_SUBMIT", "description": "Downloaded ROI whitepaper", "occurred_at": (now - timedelta(days=1)).isoformat()},
        ],
        "hub-100302": [
            {"type": "AD_CLICK", "description": "Clicked LinkedIn ad — 'Scale your GTM'", "occurred_at": (now - timedelta(days=7)).isoformat()},
        ],
        "hub-100403": [
            {"type": "MEETING", "description": "Attended product demo", "occurred_at": (now - timedelta(days=10)).isoformat()},
            {"type": "EMAIL_REPLY", "description": "Replied asking for enterprise pricing", "occurred_at": (now - timedelta(days=6)).isoformat()},
            {"type": "PAGE_VIEW", "description": "Visited /case-studies/retail", "occurred_at": (now - timedelta(days=2)).isoformat()},
            {"type": "FORM_SUBMIT", "description": "Requested security review docs", "occurred_at": (now - timedelta(days=1)).isoformat()},
        ],
    }
    return mock_activities.get(contact_id, [
        {"type": "PAGE_VIEW", "description": "Visited homepage", "occurred_at": (now - timedelta(days=2)).isoformat()},
    ])


# ===================================================================
# 4. Email Sequence Drafting
# ===================================================================

def draft_email_sequence(
    contact: dict[str, Any],
    company: dict[str, Any],
    template: str = "standard",
) -> list[dict[str, Any]]:
    """Generate a multi-step email sequence for *contact* at *company*.

    *template* can be ``"enterprise"``, ``"smb"``, or ``"standard"``.

    Returns a list of dicts, each with: step, subject, body, delay_days.
    """
    log.info(
        "draft_email_sequence  contact=%s  company=%s  template=%s  ts=%s",
        contact.get("email"), company.get("domain"), template, _ts(),
    )

    first = contact.get("first_name", "there")
    company_name = company.get("company_name", "your company")
    industry = company.get("industry", "your industry")
    title = contact.get("title", "")

    if template == "enterprise":
        return [
            {
                "step": 1,
                "delay_days": 0,
                "subject": f"{first}, a strategic question about {company_name}'s digital roadmap",
                "body": (
                    f"Hi {first},\n\n"
                    f"I noticed {company_name} has been investing heavily in digital transformation "
                    f"across the {industry} space. Given your role as {title}, I imagine you're "
                    f"evaluating how to consolidate your martech stack while scaling personalization.\n\n"
                    f"We recently helped a Fortune-500 retailer reduce CAC by 34% while doubling "
                    f"pipeline velocity. I'd love to share the playbook — would a 20-minute call "
                    f"this week work?\n\nBest,\nYour SDR"
                ),
            },
            {
                "step": 2,
                "delay_days": 3,
                "subject": f"Re: {company_name}'s digital roadmap",
                "body": (
                    f"Hi {first},\n\n"
                    f"Following up on my earlier note. I put together a brief analysis of how "
                    f"companies in {industry} are leveraging AI-driven outreach to improve "
                    f"conversion rates by 2-3x.\n\n"
                    f"Happy to walk through it — even 15 minutes would be valuable.\n\nBest,\nYour SDR"
                ),
            },
            {
                "step": 3,
                "delay_days": 7,
                "subject": f"Quick resource for {company_name}",
                "body": (
                    f"Hi {first},\n\n"
                    f"I know inboxes get crowded, so I'll keep this short. Attached is a one-page "
                    f"ROI model customized for {industry} enterprises.\n\n"
                    f"If the numbers resonate, I'd welcome a conversation. If not, no hard feelings "
                    f"— I appreciate your time either way.\n\nBest,\nYour SDR"
                ),
            },
        ]

    if template == "smb":
        return [
            {
                "step": 1,
                "delay_days": 0,
                "subject": f"{first}, quick win for {company_name}",
                "body": (
                    f"Hey {first},\n\n"
                    f"Congrats on the momentum at {company_name}! I work with growth-stage "
                    f"{industry} teams and noticed you might benefit from automating your outbound "
                    f"pipeline.\n\n"
                    f"We have a free 14-day trial — zero commitment. Want me to set one up?\n\n"
                    f"Cheers,\nYour SDR"
                ),
            },
            {
                "step": 2,
                "delay_days": 4,
                "subject": f"Re: quick win for {company_name}",
                "body": (
                    f"Hey {first},\n\n"
                    f"Just bumping this up. A 10-minute walkthrough is usually enough to show "
                    f"the value. Would tomorrow or Thursday work?\n\nCheers,\nYour SDR"
                ),
            },
        ]

    # standard fallback
    return [
        {
            "step": 1,
            "delay_days": 0,
            "subject": f"{first}, exploring a fit with {company_name}",
            "body": (
                f"Hi {first},\n\n"
                f"I came across {company_name} and believe there may be a strong fit between "
                f"our platform and your {industry} team's goals.\n\n"
                f"Would you be open to a brief call this week?\n\nBest,\nYour SDR"
            ),
        },
        {
            "step": 2,
            "delay_days": 5,
            "subject": f"Re: exploring a fit with {company_name}",
            "body": (
                f"Hi {first},\n\n"
                f"Just circling back — I'd love to share a few ideas tailored to {company_name}. "
                f"Let me know if there's a good time.\n\nBest,\nYour SDR"
            ),
        },
    ]


# ===================================================================
# 5. HubSpot Task Creation
# ===================================================================

def create_hubspot_task(
    contact_id: str,
    title: str,
    due_days: int = 3,
) -> dict[str, Any]:
    """Create a follow-up task in HubSpot linked to *contact_id*.

    Returns: task_id, contact_id, title, due_date, status, timestamp.
    """
    log.info(
        "create_hubspot_task  contact_id=%s  title=%s  due_days=%d  ts=%s",
        contact_id, title, due_days, _ts(),
    )
    due_date = (datetime.now(timezone.utc) + timedelta(days=due_days)).strftime("%Y-%m-%d")

    if not USE_MOCK and HUBSPOT_API_KEY:
        try:
            import requests

            url = "https://api.hubapi.com/crm/v3/objects/tasks"
            payload = {
                "properties": {
                    "hs_task_subject": title,
                    "hs_task_body": title,
                    "hs_task_status": "NOT_STARTED",
                    "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                    "hs_task_priority": "MEDIUM",
                },
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 204}],
                    }
                ],
            }
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "task_id": data["id"],
                "contact_id": contact_id,
                "title": title,
                "due_date": due_date,
                "status": "NOT_STARTED",
                "timestamp": _ts(),
            }
        except Exception as exc:
            log.warning("HubSpot task creation failed, falling back to mock: %s", exc)

    # ----- mock fallback -----
    return {
        "task_id": f"task-{_mock_id()}",
        "contact_id": contact_id,
        "title": title,
        "due_date": due_date,
        "status": "NOT_STARTED",
        "timestamp": _ts(),
    }


# ===================================================================
# 6. Gmail Send
# ===================================================================

def send_via_gmail(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email through Gmail (or mock-send in demo mode).

    Returns: message_id, to, subject, status, timestamp.
    """
    log.info("send_via_gmail  to=%s  subject=%s  mock=%s  ts=%s", to, subject, USE_MOCK, _ts())

    if not USE_MOCK and GMAIL_CREDENTIALS and os.path.isfile(GMAIL_CREDENTIALS):
        try:
            import base64
            from email.mime.text import MIMEText

            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_file(GMAIL_CREDENTIALS)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            service = build("gmail", "v1", credentials=creds)

            mime = MIMEText(body)
            mime["to"] = to
            mime["subject"] = subject
            raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()

            sent = (
                service.users()
                .messages()
                .send(userId="me", body={"raw": raw})
                .execute()
            )
            return {
                "message_id": sent["id"],
                "to": to,
                "subject": subject,
                "status": "SENT",
                "timestamp": _ts(),
            }
        except Exception as exc:
            log.warning("Gmail API call failed, falling back to mock: %s", exc)

    # ----- mock fallback -----
    return {
        "message_id": f"msg-{_mock_id()}",
        "to": to,
        "subject": subject,
        "status": "MOCK_SENT",
        "timestamp": _ts(),
    }
