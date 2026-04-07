# tools/hubspot_tools.py
# Project 4: Demand Gen Pipeline Crew
# Chapter Reference: Chapter 4 – CrewAI Framework
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
# Description: HubSpot & CDP tools with CrewAI @tool decorator and mock fallbacks

"""HubSpot and CDP integration tools for the Demand Gen Pipeline.

Provides cohort export, propensity scoring, and HubSpot workflow activation.
Each function attempts the live API when USE_MOCK is false and the relevant
API key is present, falling back to deterministic mock data otherwise.
"""

from __future__ import annotations

import json
import logging
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any

from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
HUBSPOT_API_KEY: str = os.getenv("HUBSPOT_API_KEY", "")
SEGMENT_WRITE_KEY: str = os.getenv("SEGMENT_WRITE_KEY", "")

logger = logging.getLogger("demand_gen.tools.hubspot")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mock_id() -> str:
    """Return a short unique identifier for mock objects."""
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Mock data generators
# ---------------------------------------------------------------------------

def _mock_cohort(segment_name: str) -> dict[str, Any]:
    """Generate a realistic mock cohort export result."""
    random.seed(hash(segment_name) % 2**32)
    size = random.randint(1200, 8500)
    return {
        "cohort_id": f"cohort-{_mock_id()}",
        "segment_name": segment_name,
        "cohort_size": size,
        "export_status": "completed",
        "top_industries": ["SaaS", "FinTech", "E-Commerce"],
        "avg_company_size": random.choice(["50-200", "200-1000", "1000-5000"]),
        "top_regions": ["US-West", "US-East", "EU-West"],
        "exported_at": _ts(),
    }


def _mock_propensity(cohort_id: str) -> dict[str, Any]:
    """Generate mock ML propensity scoring results."""
    random.seed(hash(cohort_id) % 2**32)
    scores = [round(random.uniform(0.05, 0.95), 3) for _ in range(200)]
    scores.sort()
    n = len(scores)
    return {
        "cohort_id": cohort_id,
        "model_version": "propensity-v3.2",
        "scored_contacts": random.randint(1200, 8500),
        "propensity_summary": {
            "min": round(scores[0], 3),
            "max": round(scores[-1], 3),
            "mean": round(sum(scores) / n, 3),
            "median": round(scores[n // 2], 3),
            "p75": round(scores[int(n * 0.75)], 3),
            "p90": round(scores[int(n * 0.90)], 3),
        },
        "high_propensity_count": sum(1 for s in scores if s >= 0.7),
        "recommended_threshold": 0.65,
        "scored_at": _ts(),
    }


def _mock_hubspot_workflow(workflow_name: str, cohort_id: str) -> dict[str, Any]:
    """Generate a mock HubSpot workflow activation result."""
    return {
        "workflow_id": f"wf-{_mock_id()}",
        "workflow_name": workflow_name,
        "cohort_id": cohort_id,
        "status": "active",
        "enrolled_contacts": random.randint(800, 5000),
        "trigger_type": "list_membership",
        "activated_at": _ts(),
    }


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

@tool
def export_segment_cohort(segment_name: str) -> str:
    """Export an audience cohort from the CDP for the given segment name.

    Queries the customer data platform (e.g., Segment or internal CDP) to
    build and export an audience cohort matching the provided segment
    criteria.  Returns cohort metadata including ID, size, top industries,
    company size distribution, and regional breakdown.

    Args:
        segment_name: The name or label of the target audience segment
                      (e.g., 'high-intent-saas-buyers').

    Returns:
        JSON string with cohort export details.
    """
    logger.info(
        "export_segment_cohort | segment=%s | mock=%s | ts=%s",
        segment_name, USE_MOCK, _ts(),
    )

    if not USE_MOCK and SEGMENT_WRITE_KEY:
        try:
            import requests

            resp = requests.post(
                "https://profiles.segment.com/v1/spaces/"
                f"{os.getenv('SEGMENT_WORKSPACE_ID', '')}/collections/users/audiences",
                headers={
                    "Authorization": f"Bearer {SEGMENT_WRITE_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": segment_name,
                    "definition": {"type": "trait", "trait": segment_name},
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            result = {
                "cohort_id": data.get("id", f"cohort-{_mock_id()}"),
                "segment_name": segment_name,
                "cohort_size": data.get("count", 0),
                "export_status": "completed",
                "exported_at": _ts(),
            }
            logger.info("Live CDP export succeeded: cohort_id=%s", result["cohort_id"])
            return json.dumps(result, indent=2)
        except Exception as exc:
            logger.warning("CDP API call failed, falling back to mock: %s", exc)

    mock = _mock_cohort(segment_name)
    logger.info("Returning mock cohort: cohort_id=%s size=%d", mock["cohort_id"], mock["cohort_size"])
    return json.dumps(mock, indent=2)


@tool
def score_audience_propensity(cohort_id: str) -> str:
    """Run ML propensity scoring on an exported audience cohort.

    Applies a purchase-propensity model to every contact in the cohort,
    returning summary statistics (min, max, mean, median, p75, p90),
    the count of high-propensity contacts, and a recommended score
    threshold for campaign targeting.

    Args:
        cohort_id: The identifier of the previously exported cohort.

    Returns:
        JSON string with propensity scoring results.
    """
    logger.info(
        "score_audience_propensity | cohort_id=%s | mock=%s | ts=%s",
        cohort_id, USE_MOCK, _ts(),
    )

    if not USE_MOCK:
        try:
            import requests

            resp = requests.post(
                f"{os.getenv('ML_SCORING_ENDPOINT', 'http://localhost:8000')}/score",
                json={"cohort_id": cohort_id},
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Live propensity scoring succeeded for cohort_id=%s", cohort_id)
            return json.dumps(result, indent=2)
        except Exception as exc:
            logger.warning("ML scoring API failed, falling back to mock: %s", exc)

    mock = _mock_propensity(cohort_id)
    logger.info(
        "Returning mock propensity: mean=%.3f high_count=%d",
        mock["propensity_summary"]["mean"],
        mock["high_propensity_count"],
    )
    return json.dumps(mock, indent=2)


@tool
def activate_hubspot_workflow(workflow_name: str, cohort_id: str) -> str:
    """Activate a HubSpot workflow that enrolls contacts from the given cohort.

    Creates or activates a HubSpot automation workflow that triggers on
    list membership for the specified cohort.  The workflow handles email
    nurture sequences, lead scoring updates, and internal notifications.

    Args:
        workflow_name: Display name for the HubSpot workflow.
        cohort_id: The cohort whose members will be enrolled.

    Returns:
        JSON string with workflow activation confirmation.
    """
    logger.info(
        "activate_hubspot_workflow | workflow=%s | cohort=%s | mock=%s | ts=%s",
        workflow_name, cohort_id, USE_MOCK, _ts(),
    )

    if not USE_MOCK and HUBSPOT_API_KEY:
        try:
            import requests

            resp = requests.post(
                "https://api.hubapi.com/automation/v4/flows",
                headers={
                    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": workflow_name,
                    "type": "CONTACT_FLOW",
                    "enabled": True,
                    "enrollmentCriteria": {
                        "listId": cohort_id,
                        "type": "LIST_MEMBERSHIP",
                    },
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            result = {
                "workflow_id": data.get("id", f"wf-{_mock_id()}"),
                "workflow_name": workflow_name,
                "cohort_id": cohort_id,
                "status": "active",
                "enrolled_contacts": data.get("enrolledCount", 0),
                "activated_at": _ts(),
            }
            logger.info("Live HubSpot workflow activated: wf_id=%s", result["workflow_id"])
            return json.dumps(result, indent=2)
        except Exception as exc:
            logger.warning("HubSpot workflow API failed, falling back to mock: %s", exc)

    mock = _mock_hubspot_workflow(workflow_name, cohort_id)
    logger.info(
        "Returning mock workflow: wf_id=%s enrolled=%d",
        mock["workflow_id"],
        mock["enrolled_contacts"],
    )
    return json.dumps(mock, indent=2)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60, "\nDemand Gen Pipeline -- HubSpot Tools Demo\n", "=" * 60)
    cohort_json = export_segment_cohort.run("high-intent-saas-buyers")
    print(cohort_json)
    cohort_data = json.loads(cohort_json)
    print(score_audience_propensity.run(cohort_data["cohort_id"]))
    print(activate_hubspot_workflow.run(
        workflow_name="Q2 SaaS Nurture Sequence", cohort_id=cohort_data["cohort_id"],
    ))
