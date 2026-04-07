# File      : consideration_journey_flow.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Consideration Journey Flow — CrewAI Flow orchestration.

This flow models the full consideration-stage pipeline:

  1. @start   — Receive an MQL trigger (e.g. HubSpot lifecycle change).
  2. @listen  — Run the Campaign Intelligence Crew on the MQL data.
  3. @listen  — Publish results to Klaviyo (nurture flow) and HubSpot (CRM).

Error handling: if the crew fails, a fallback step enrols the contact in
a generic nurture sequence so no lead is left untouched.

Usage:
    python -m stage2_consideration.flows.consideration_journey_flow
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import httpx
from crewai.flow.flow import Flow, listen, start
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


# ── State model ─────────────────────────────────────────────────────────

class ConsiderationState(BaseModel):
    """Shared state that flows between steps."""

    mql_email: str = ""
    company: str = ""
    industry: str = ""
    channels: str = "email,linkedin,webinar"
    crew_result: dict[str, Any] = Field(default_factory=dict)
    klaviyo_status: str = ""
    hubspot_status: str = ""
    error: str = ""
    fallback_used: bool = False


# ── Helper functions for real APIs ──────────────────────────────────────

def _publish_to_klaviyo(email: str, flow_id: str, properties: dict) -> dict:
    """Add a profile to a Klaviyo flow (real API)."""
    api_key = os.environ["KLAVIYO_API_KEY"]
    headers = {
        "Authorization": f"Klaviyo-API-Key {api_key}",
        "Content-Type": "application/json",
        "revision": "2024-10-15",
    }
    payload = {
        "data": {
            "type": "event",
            "attributes": {
                "profile": {"$email": email},
                "metric": {"name": "consideration_nurture_enrolled"},
                "properties": {**properties, "flow_id": flow_id},
                "time": datetime.now().isoformat(),
            },
        }
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post("https://a.klaviyo.com/api/events/", headers=headers, json=payload)
        resp.raise_for_status()
        return {"status": "success", "http_status": resp.status_code}


def _update_hubspot_contact(email: str, properties: dict) -> dict:
    """Update a HubSpot contact's properties (real API)."""
    api_key = os.environ["HUBSPOT_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"properties": properties}
    with httpx.Client(timeout=30) as client:
        # Search for contact by email first
        search_resp = client.post(
            "https://api.hubapi.com/crm/v3/objects/contacts/search",
            headers=headers,
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email,
                            }
                        ]
                    }
                ]
            },
        )
        search_resp.raise_for_status()
        results = search_resp.json().get("results", [])
        if not results:
            return {"status": "error", "message": f"Contact {email} not found"}

        contact_id = results[0]["id"]
        update_resp = client.patch(
            f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
            headers=headers,
            json=payload,
        )
        update_resp.raise_for_status()
        return {"status": "success", "contact_id": contact_id}


# ── Flow definition ─────────────────────────────────────────────────────

class ConsiderationJourneyFlow(Flow[ConsiderationState]):
    """Orchestrates the consideration stage from MQL trigger to activation."""

    # Step 1 — Receive MQL trigger
    @start()
    def receive_mql(self) -> dict:
        """Receive and validate the MQL trigger event."""
        print(f"[Flow] MQL received: {self.state.mql_email}")
        print(f"[Flow] Company: {self.state.company} | Industry: {self.state.industry}")

        if not self.state.mql_email:
            self.state.error = "No email provided in MQL trigger"
            raise ValueError(self.state.error)

        return {
            "email": self.state.mql_email,
            "company": self.state.company,
            "industry": self.state.industry,
            "channels": self.state.channels,
        }

    # Step 2 — Run the Campaign Intelligence Crew
    @listen(receive_mql)
    def run_consideration_crew(self, mql_data: dict) -> dict:
        """Execute the Campaign Intelligence Crew on the MQL data."""
        print("[Flow] Starting Campaign Intelligence Crew ...")

        try:
            from stage2_consideration.crews.campaign_intelligence_crew.crew import (
                CampaignIntelligenceCrew,
            )

            crew_instance = CampaignIntelligenceCrew()
            result = crew_instance.crew().kickoff(
                inputs={
                    "company": mql_data["company"],
                    "industry": mql_data["industry"],
                    "channels": mql_data["channels"],
                }
            )

            # Normalise crew output
            if hasattr(result, "json_dict") and result.json_dict:
                crew_output = result.json_dict
            elif hasattr(result, "raw"):
                try:
                    crew_output = json.loads(result.raw)
                except (json.JSONDecodeError, TypeError):
                    crew_output = {"raw_output": str(result.raw)}
            else:
                crew_output = {"raw_output": str(result)}

            self.state.crew_result = crew_output
            print("[Flow] Crew completed successfully.")
            return crew_output

        except Exception as exc:  # noqa: BLE001
            error_msg = f"Crew execution failed: {exc}"
            print(f"[Flow] ERROR: {error_msg}")
            self.state.error = error_msg
            # Return empty dict — the publish step will detect the error
            return {}

    # Step 3 — Publish to Klaviyo and update HubSpot
    @listen(run_consideration_crew)
    def publish_and_activate(self, crew_output: dict) -> dict:
        """Publish nurture content to Klaviyo and update HubSpot CRM.

        If the crew failed, fall back to enrolling in a generic sequence.
        """
        email = self.state.mql_email
        is_fallback = bool(self.state.error) or not crew_output

        if is_fallback:
            print("[Flow] Using FALLBACK — generic nurture sequence")
            self.state.fallback_used = True
            flow_id = "generic_consideration_nurture"
            nurture_properties = {
                "sequence_type": "generic",
                "reason": self.state.error or "empty crew output",
            }
            hubspot_props = {
                "nurture_sequence": "generic_consideration",
                "nurture_enrolled_at": datetime.now().isoformat(),
                "consideration_status": "fallback",
            }
        else:
            print("[Flow] Publishing personalised nurture sequence")
            flow_id = "personalised_consideration_nurture"
            nurture_properties = {
                "sequence_type": "personalised",
                "company": self.state.company,
                "industry": self.state.industry,
                "crew_summary": json.dumps(crew_output)[:500],
            }
            hubspot_props = {
                "nurture_sequence": "personalised_consideration",
                "nurture_enrolled_at": datetime.now().isoformat(),
                "consideration_status": "active",
                "consideration_research_complete": "true",
            }

        # ── Klaviyo ─────────────────────────────────────────────────────
        if USE_MOCK:
            self.state.klaviyo_status = "mock_success"
            print(f"[Flow][Mock] Klaviyo: enrolled {email} in {flow_id}")
        else:
            try:
                result = _publish_to_klaviyo(email, flow_id, nurture_properties)
                self.state.klaviyo_status = result.get("status", "unknown")
                print(f"[Flow] Klaviyo: {self.state.klaviyo_status}")
            except Exception as exc:  # noqa: BLE001
                self.state.klaviyo_status = f"error: {exc}"
                print(f"[Flow] Klaviyo error: {exc}")

        # ── HubSpot ────────────────────────────────────────────────────
        if USE_MOCK:
            self.state.hubspot_status = "mock_success"
            print(f"[Flow][Mock] HubSpot: updated {email} properties")
        else:
            try:
                result = _update_hubspot_contact(email, hubspot_props)
                self.state.hubspot_status = result.get("status", "unknown")
                print(f"[Flow] HubSpot: {self.state.hubspot_status}")
            except Exception as exc:  # noqa: BLE001
                self.state.hubspot_status = f"error: {exc}"
                print(f"[Flow] HubSpot error: {exc}")

        summary = {
            "email": email,
            "fallback_used": is_fallback,
            "klaviyo_status": self.state.klaviyo_status,
            "hubspot_status": self.state.hubspot_status,
            "timestamp": datetime.now().isoformat(),
        }
        print(f"[Flow] Activation complete: {json.dumps(summary, indent=2)}")
        return summary


# ── CLI entry point ─────────────────────────────────────────────────────

def main() -> None:
    """Run the consideration flow with demo data."""
    print("=" * 60)
    print("  Consideration Journey Flow — Stage 2")
    print("=" * 60)

    flow = ConsiderationJourneyFlow()

    # Seed the flow state with a demo MQL
    flow.state.mql_email = os.getenv("DEMO_EMAIL", "alex.rivera@acmecorp.com")
    flow.state.company = os.getenv("DEMO_COMPANY", "Acme Corp")
    flow.state.industry = os.getenv("DEMO_INDUSTRY", "B2B SaaS")
    flow.state.channels = os.getenv("DEMO_CHANNELS", "email,linkedin,webinar")

    result = flow.kickoff()

    print()
    print("=" * 60)
    print("  Flow completed")
    print("=" * 60)
    print(f"  Final state:")
    print(f"    Klaviyo  : {flow.state.klaviyo_status}")
    print(f"    HubSpot  : {flow.state.hubspot_status}")
    print(f"    Fallback : {flow.state.fallback_used}")
    if flow.state.error:
        print(f"    Error    : {flow.state.error}")
    print("=" * 60)


if __name__ == "__main__":
    main()
