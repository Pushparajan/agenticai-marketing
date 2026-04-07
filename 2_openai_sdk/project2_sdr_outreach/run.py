"""
Project 2 — Autonomous SDR Outreach Agent
File: run.py
Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
Framework: OpenAI Agents SDK

CLI runner for the SDR outreach agent.

Usage
-----
    # Demo mode — process 3 built-in sample leads
    python run.py

    # Single lead via command-line arguments
    python run.py --email jdoe@acmecorp.com --domain acmecorp.com

    # Interactive mode
    python run.py --interactive
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from agent import process_lead, run_agent_pipeline_sync
from tools import USE_MOCK

# ---------------------------------------------------------------------------
# Sample leads for demo mode
# ---------------------------------------------------------------------------

SAMPLE_LEADS: list[dict[str, str]] = [
    {
        "email": "jdoe@acmecorp.com",
        "domain": "acmecorp.com",
        "description": "Enterprise manufacturing VP — high intent signals",
    },
    {
        "email": "alex@startuphq.io",
        "domain": "startuphq.io",
        "description": "SMB SaaS growth lead — single ad click",
    },
    {
        "email": "chen.wei@globalretail.com",
        "domain": "globalretail.com",
        "description": "Enterprise retail CDO — multi-touch engagement",
    },
]


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

_DIVIDER = "=" * 72
_SUB_DIVIDER = "-" * 72


def _print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{_DIVIDER}")
    print(f"  {title}")
    print(_DIVIDER)


def _print_result(result: dict[str, Any]) -> None:
    """Print a structured summary of a single lead's outreach result."""
    lead = result.get("lead", {})
    company = result.get("company", {})
    contact = result.get("contact", {})
    activity = result.get("activity", [])
    guardrails = result.get("guardrails", {})
    emails_sent = result.get("emails_sent", [])
    tasks_created = result.get("tasks_created", [])
    sequence = result.get("sequence", [])

    print(f"\n{_SUB_DIVIDER}")
    print(f"  LEAD: {lead.get('email', 'N/A')}  @  {lead.get('domain', 'N/A')}")
    print(_SUB_DIVIDER)

    # Company info
    print(f"\n  Company:        {company.get('company_name', 'N/A')}")
    print(f"  Industry:       {company.get('industry', 'N/A')}")
    print(f"  Employees:      {company.get('employee_count', 'N/A')}")
    print(f"  Revenue:        {company.get('annual_revenue', 'N/A')}")
    print(f"  HQ:             {company.get('headquarters', 'N/A')}")
    print(f"  Tech stack:     {', '.join(company.get('tech_stack', []))}")
    print(f"  Funding:        {company.get('funding_stage', 'N/A')}")

    # Contact info
    print(f"\n  Contact:        {contact.get('first_name', '')} {contact.get('last_name', '')}")
    print(f"  Title:          {contact.get('title', 'N/A')}")
    print(f"  Lifecycle:      {contact.get('lifecycle_stage', 'N/A')}")
    print(f"  Lead status:    {contact.get('lead_status', 'N/A')}")
    print(f"  Region:         {contact.get('region', 'N/A')}")

    # Activity
    print(f"\n  Recent activity ({len(activity)} events):")
    for evt in activity:
        print(f"    - [{evt.get('type', '?')}] {evt.get('description', '')}")

    # Routing
    print(f"\n  Agent routed:   {result.get('agent', 'N/A')}")
    print(f"  Template:       {result.get('template', 'N/A')}")

    # Guardrails
    passed = guardrails.get("all_passed", "N/A")
    issues = guardrails.get("issues", [])
    status_label = "PASSED" if passed else f"ISSUES ({len(issues)})"
    print(f"\n  Guardrails:     {status_label}")
    if issues:
        for issue in issues:
            print(f"    ! {issue}")

    # Emails sent
    print(f"\n  Emails sent:    {len(emails_sent)}")
    for em in emails_sent:
        print(f"    - [{em.get('status', '?')}] To: {em.get('to', '?')}  "
              f"Subject: {em.get('subject', '?')}")
        print(f"      Message ID: {em.get('message_id', '?')}")

    # Sequence preview
    print(f"\n  Full sequence ({len(sequence)} steps):")
    for step in sequence:
        print(f"    Step {step.get('step', '?')} (delay: {step.get('delay_days', 0)}d):")
        print(f"      Subject: {step.get('subject', '?')}")
        body_preview = step.get("body", "")[:120].replace("\n", " ")
        print(f"      Body:    {body_preview}...")

    # Tasks
    print(f"\n  Follow-up tasks: {len(tasks_created)}")
    for task in tasks_created:
        print(f"    - [{task.get('status', '?')}] {task.get('title', '?')}  "
              f"due: {task.get('due_date', '?')}")
        print(f"      Task ID: {task.get('task_id', '?')}")

    print()


def _print_summary(results: list[dict[str, Any]]) -> None:
    """Print aggregate summary after processing all leads."""
    _print_header("AGGREGATE SUMMARY")
    total_leads = len(results)
    total_emails = sum(len(r.get("emails_sent", [])) for r in results)
    total_tasks = sum(len(r.get("tasks_created", [])) for r in results)
    enterprise_count = sum(1 for r in results if r.get("agent") == "enterprise_bdr")
    smb_count = sum(1 for r in results if r.get("agent") == "smb_nurture")
    guardrail_clean = sum(
        1 for r in results if r.get("guardrails", {}).get("all_passed", False)
    )

    print(f"\n  Leads processed:      {total_leads}")
    print(f"  Enterprise leads:     {enterprise_count}")
    print(f"  SMB leads:            {smb_count}")
    print(f"  Emails dispatched:    {total_emails}")
    print(f"  CRM tasks created:    {total_tasks}")
    print(f"  Guardrail-clean:      {guardrail_clean}/{total_leads}")
    print(f"  Mock mode:            {USE_MOCK}")
    print(f"\n  CSV log: outreach_log.csv")
    print()


# ---------------------------------------------------------------------------
# CLI modes
# ---------------------------------------------------------------------------

def _run_demo() -> list[dict[str, Any]]:
    """Process built-in sample leads and return results."""
    _print_header("SDR OUTREACH AGENT — DEMO MODE")
    print(f"\n  Processing {len(SAMPLE_LEADS)} sample leads...")
    print(f"  Mock mode: {USE_MOCK}\n")

    results: list[dict[str, Any]] = []
    for idx, lead in enumerate(SAMPLE_LEADS, start=1):
        print(f"\n  [{idx}/{len(SAMPLE_LEADS)}] {lead['description']}")
        result = process_lead(lead["email"], lead["domain"])
        results.append(result)
        _print_result(result)

    _print_summary(results)
    return results


def _run_single(email: str, domain: str) -> dict[str, Any]:
    """Process a single lead from CLI arguments."""
    _print_header("SDR OUTREACH AGENT — SINGLE LEAD")
    print(f"\n  Email:  {email}")
    print(f"  Domain: {domain}")
    print(f"  Mock mode: {USE_MOCK}\n")

    result = run_agent_pipeline_sync(email, domain)
    _print_result(result)
    _print_summary([result])
    return result


def _run_interactive() -> list[dict[str, Any]]:
    """Prompt for leads interactively until the user quits."""
    _print_header("SDR OUTREACH AGENT — INTERACTIVE MODE")
    print("\n  Enter lead details below. Type 'quit' or 'q' to stop.\n")

    results: list[dict[str, Any]] = []
    while True:
        try:
            email = input("  Email (or 'q' to quit): ").strip()
            if email.lower() in ("q", "quit", "exit", ""):
                break
            domain = input("  Domain: ").strip()
            if not domain:
                # Auto-derive domain from email
                domain = email.split("@")[-1]
                print(f"  (auto-detected domain: {domain})")

            result = process_lead(email, domain)
            results.append(result)
            _print_result(result)

        except (KeyboardInterrupt, EOFError):
            print("\n\n  Interrupted. Exiting.\n")
            break

    if results:
        _print_summary(results)
    return results


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="sdr_outreach",
        description=(
            "Autonomous SDR Outreach Agent — enrich leads, draft sequences, "
            "validate compliance, and dispatch emails."
        ),
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Lead email address (requires --domain).",
    )
    parser.add_argument(
        "--domain",
        type=str,
        help="Lead company domain (e.g., acmecorp.com).",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode — prompt for leads one at a time.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output raw JSON instead of formatted text.",
    )
    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the SDR outreach CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.interactive:
        results = _run_interactive()
    elif args.email:
        domain = args.domain or args.email.split("@")[-1]
        result = _run_single(args.email, domain)
        results = [result]
    else:
        results = _run_demo()

    # Optional JSON dump
    if args.json_output and results:
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
