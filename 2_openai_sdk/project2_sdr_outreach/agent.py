"""
Project 2 — Autonomous SDR Outreach Agent
File: agent.py
Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
Framework: OpenAI Agents SDK

Multi-agent orchestration for autonomous SDR outreach.

Architecture:  Triage Agent -> Enterprise BDR Agent (500+ employees)
                             -> SMB Nurture Agent   (< 500 employees)

Both specialists enrich, look up CRM data, draft sequences, run guardrails,
send step-1, schedule follow-ups, and log everything to CSV.
"""
from __future__ import annotations

import asyncio, csv, json, logging, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

try:
    from agents import Agent, Runner, function_tool, trace
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False

from guardrails import compliance_check, brand_voice_validator, run_all_guardrails
from tools import (
    create_hubspot_task, draft_email_sequence, enrich_firmographics,
    get_hubspot_contact, get_recent_activity, send_via_gmail,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  [%(levelname)s]  %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S%z")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration & CSV logger
# ---------------------------------------------------------------------------
CSV_OUTPUT: Path = Path(__file__).parent / "outreach_log.csv"
CSV_HEADERS: list[str] = [
    "timestamp", "agent", "email", "domain", "company_name",
    "employee_count", "template", "emails_sent", "tasks_created",
    "guardrail_passed", "guardrail_issues",
]
ENTERPRISE_THRESHOLD: int = 500


def _log_to_csv(row: dict[str, Any]) -> None:
    """Append a result row to the outreach CSV log (create header if needed)."""
    write_header = not CSV_OUTPUT.exists()
    with open(CSV_OUTPUT, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_HEADERS)
        if write_header:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in CSV_HEADERS})
    log.info("Logged result to %s", CSV_OUTPUT)


# ---------------------------------------------------------------------------
# Compliance footer helper
# ---------------------------------------------------------------------------
def _append_compliance_footer(body: str, region: str) -> str:
    """Append CAN-SPAM / GDPR footer if required elements are missing."""
    parts: list[str] = []
    bl = body.lower()
    if "unsubscribe" not in bl:
        parts.append("If you'd prefer not to receive future emails, reply "
                      "'unsubscribe' and we'll remove you immediately.")
    if not any(m in bl for m in ("street", "avenue", "blvd", "road", "suite", "floor")):
        parts.append("Sent by AgenticAI Inc., 100 Innovation Drive, Suite 400, "
                      "San Francisco, CA 94105")
    if region in ("EU", "UK", "EEA", "DE", "FR", "ES", "IT", "NL", "BE"):
        if "privacy" not in bl and "gdpr" not in bl:
            parts.append("We're contacting you based on legitimate interest. "
                         "View our privacy policy: https://example.com/privacy")
    return body.rstrip() + "\n\n---\n" + "\n".join(parts) if parts else body


# ===================================================================
# Core deterministic pipeline
# ===================================================================
def process_lead(email: str, domain: str, agent_label: str = "auto") -> dict[str, Any]:
    """End-to-end SDR outreach for a single lead: enrich, draft, validate, send, log."""
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log.info("===== Processing lead: %s @ %s =====", email, domain)

    company = enrich_firmographics(domain)
    contact = get_hubspot_contact(email)
    activity = get_recent_activity(contact["contact_id"])
    emp = company.get("employee_count", 0)

    if agent_label == "auto":
        agent_label = "enterprise_bdr" if emp >= ENTERPRISE_THRESHOLD else "smb_nurture"
    template = "enterprise" if agent_label == "enterprise_bdr" else "smb"
    log.info("Route -> %s  (employees=%d)", agent_label, emp)

    sequence = draft_email_sequence(contact, company, template)
    region = contact.get("region", "US")

    # Guardrails on every step — auto-fix with footer on failure
    guardrail_results, final_sequence = [], []
    for step in sequence:
        body = step["body"]
        gr = run_all_guardrails(body, region)
        if not gr["passed"]:
            body = _append_compliance_footer(body, region)
            gr = run_all_guardrails(body, region)
        guardrail_results.append(gr)
        final_sequence.append({**step, "body": body})

    all_passed = all(g["passed"] for g in guardrail_results)
    all_issues = [i for g in guardrail_results for i in g["issues"]]

    # Send step 1, create CRM tasks for the rest
    emails_sent: list[dict] = []
    tasks_created: list[dict] = []
    if final_sequence:
        emails_sent.append(send_via_gmail(email, final_sequence[0]["subject"],
                                          final_sequence[0]["body"]))
        for s in final_sequence[1:]:
            tasks_created.append(create_hubspot_task(
                contact["contact_id"],
                f"Send step {s['step']}: {s['subject']}", s["delay_days"]))

    _log_to_csv({"timestamp": ts, "agent": agent_label, "email": email,
                  "domain": domain, "company_name": company["company_name"],
                  "employee_count": emp, "template": template,
                  "emails_sent": len(emails_sent),
                  "tasks_created": len(tasks_created),
                  "guardrail_passed": all_passed,
                  "guardrail_issues": "; ".join(all_issues)})

    return {"lead": {"email": email, "domain": domain}, "company": company,
            "contact": contact, "activity": activity, "agent": agent_label,
            "template": template, "sequence": final_sequence,
            "guardrails": {"all_passed": all_passed, "issues": all_issues},
            "emails_sent": emails_sent, "tasks_created": tasks_created,
            "timestamp": ts}


# ===================================================================
# OpenAI Agents SDK wiring
# ===================================================================
def _build_agents() -> "Agent | None":
    """Build Triage -> Enterprise / SMB agent graph (None if SDK missing)."""
    if not AGENTS_SDK_AVAILABLE:
        log.warning("openai-agents SDK not installed — standalone mode only.")
        return None

    @function_tool
    def tool_enrich_firmographics(domain: str) -> str:
        """Look up firmographic data for a company domain."""
        return json.dumps(enrich_firmographics(domain))

    @function_tool
    def tool_get_hubspot_contact(email: str) -> str:
        """Fetch a CRM contact record by email address."""
        return json.dumps(get_hubspot_contact(email))

    @function_tool
    def tool_get_recent_activity(contact_id: str) -> str:
        """Get recent CRM engagement events for a contact."""
        return json.dumps(get_recent_activity(contact_id))

    @function_tool
    def tool_draft_email_sequence(contact_json: str, company_json: str, template: str) -> str:
        """Draft a multi-step email sequence (contact/company as JSON strings)."""
        return json.dumps(draft_email_sequence(json.loads(contact_json),
                                               json.loads(company_json), template))

    @function_tool
    def tool_create_hubspot_task(contact_id: str, title: str, due_days: int) -> str:
        """Create a follow-up task in HubSpot for a contact."""
        return json.dumps(create_hubspot_task(contact_id, title, due_days))

    @function_tool
    def tool_send_via_gmail(to: str, subject: str, body: str) -> str:
        """Send an email via Gmail (mock in demo mode)."""
        return json.dumps(send_via_gmail(to, subject, body))

    @function_tool
    def tool_compliance_check(email_content: str, recipient_region: str) -> str:
        """Validate email content for CAN-SPAM / GDPR compliance."""
        return json.dumps(compliance_check(email_content, recipient_region))

    @function_tool
    def tool_brand_voice_validator(content: str) -> str:
        """Check email content against brand voice guidelines."""
        return json.dumps(brand_voice_validator(content))

    full_tools = [tool_enrich_firmographics, tool_get_hubspot_contact,
                  tool_get_recent_activity, tool_draft_email_sequence,
                  tool_create_hubspot_task, tool_send_via_gmail,
                  tool_compliance_check, tool_brand_voice_validator]
    smb_tools = [t for t in full_tools if t is not tool_create_hubspot_task]

    enterprise_bdr = Agent(
        name="Enterprise BDR Agent", model="gpt-4o", tools=full_tools,
        instructions=(
            "You are an Enterprise BDR handling 500+ employee companies.\n"
            "Workflow: enrich -> CRM lookup -> recent activity -> draft 'enterprise' "
            "sequence -> compliance_check + brand_voice_validator on each email -> "
            "send step 1 -> create_hubspot_task for remaining steps -> return JSON summary."))

    smb_nurture = Agent(
        name="SMB Nurture Agent", model="gpt-4o", tools=smb_tools,
        instructions=(
            "You are an SMB Nurture Rep handling < 500 employee companies.\n"
            "Workflow: enrich -> CRM lookup -> recent activity -> draft 'smb' sequence "
            "-> compliance_check + brand_voice_validator on each email -> send step 1 "
            "-> return JSON summary. Keep outreach light and friendly."))

    triage = Agent(
        name="SDR Triage Agent", model="gpt-4o",
        tools=[tool_enrich_firmographics],
        handoffs=[enterprise_bdr, smb_nurture],
        instructions=(
            "You are the SDR Triage Agent. Call enrich_firmographics to get "
            "employee_count, then hand off:\n"
            "- employee_count >= 500 -> Enterprise BDR Agent\n"
            "- employee_count <  500 -> SMB Nurture Agent\n"
            "Pass the lead's email and domain to the specialist."))

    return triage


triage_agent: "Agent | None" = _build_agents()


# ===================================================================
# Public API
# ===================================================================
async def run_agent_pipeline(email: str, domain: str) -> dict[str, Any]:
    """Run the agent pipeline (SDK if available, else deterministic fallback)."""
    if AGENTS_SDK_AVAILABLE and triage_agent and os.getenv("OPENAI_API_KEY"):
        log.info("Running via OpenAI Agents SDK (LLM routing)")
        with trace("SDR Outreach Pipeline"):
            result = await Runner.run(
                triage_agent,
                f"Process lead: email={email}  domain={domain}. "
                f"Follow your full workflow and return a JSON summary.")
            log.info("Pipeline done. Final agent: %s", result.last_agent.name)
            try:
                parsed = json.loads(result.final_output)
            except (json.JSONDecodeError, TypeError):
                parsed = {"raw_output": result.final_output}
            process_lead(email, domain)  # ensure CSV logging
            parsed["csv_logged"] = True
            return parsed
    log.info("Running in standalone mode (deterministic pipeline)")
    return process_lead(email, domain)


def run_agent_pipeline_sync(email: str, domain: str) -> dict[str, Any]:
    """Synchronous wrapper around ``run_agent_pipeline``."""
    return asyncio.run(run_agent_pipeline(email, domain))
