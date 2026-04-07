# File      : email_server.py
# Stage     : All Stages
# Chapter   : 13-14
# Framework : MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Klaviyo Email MCP Server
Provides tools for email flow management, A/B testing, send optimisation,
and template operations for Consideration and Decision stages.
"""

import json
import os
import logging
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [EMAIL] %(message)s")
logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("MCP_MOCK", "true").lower() == "true"
KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY", "")

mcp = FastMCP("email-klaviyo")


@mcp.tool()
def get_flow_performance(flow_id: str) -> str:
    """Retrieve performance metrics for a Klaviyo email flow."""
    logger.info("get_flow_performance called | flow_id=%s", flow_id)
    if not USE_MOCK:
        # Real API: GET /api/flows/{flow_id}/flow-actions
        pass
    return json.dumps({
        "flow_id": flow_id,
        "flow_name": "Consideration Nurture Series",
        "status": "live",
        "period": "last_30_days",
        "metrics": {
            "emails_sent": 12480,
            "delivered": 12105,
            "delivery_rate": 0.97,
            "open_rate": 0.342,
            "click_rate": 0.087,
            "conversion_rate": 0.032,
            "unsubscribe_rate": 0.004,
            "revenue_attributed": 38400.00
        },
        "steps": [
            {"step": 1, "subject": "How teams like yours solve X", "open_rate": 0.41, "click_rate": 0.12},
            {"step": 2, "subject": "Your personalised ROI estimate", "open_rate": 0.36, "click_rate": 0.09},
            {"step": 3, "subject": "Book a 15-min strategy call", "open_rate": 0.28, "click_rate": 0.06}
        ]
    })


@mcp.tool()
def create_flow(flow_name: str, trigger_event: str, steps: str) -> str:
    """Create a new email automation flow in Klaviyo with specified trigger and steps."""
    logger.info("create_flow called | flow_name=%s trigger=%s", flow_name, trigger_event)
    if not USE_MOCK:
        # Real API: POST /api/flows
        pass
    return json.dumps({
        "flow_id": "FLW-2291",
        "flow_name": flow_name,
        "trigger_event": trigger_event,
        "steps_count": len(json.loads(steps)) if steps else 0,
        "status": "draft",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "message": "Flow created in draft mode. Review and activate when ready."
    })


@mcp.tool()
def enrol_contact(flow_id: str, email: str, properties: str) -> str:
    """Manually enrol a contact into a Klaviyo flow with optional custom properties."""
    logger.info("enrol_contact called | flow_id=%s email=%s", flow_id, email)
    if not USE_MOCK:
        # Real API: POST /api/events (trigger the flow event for the profile)
        pass
    return json.dumps({
        "enrolment_id": "ENR-6654",
        "flow_id": flow_id,
        "email": email,
        "properties": json.loads(properties) if properties else {},
        "enrolled_at": datetime.utcnow().isoformat() + "Z",
        "next_step_scheduled": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z",
        "status": "enrolled"
    })


@mcp.tool()
def pause_flow(flow_id: str, reason: str) -> str:
    """Pause a live Klaviyo flow with a reason for audit trail."""
    logger.info("pause_flow called | flow_id=%s reason=%s", flow_id, reason)
    if not USE_MOCK:
        # Real API: PATCH /api/flows/{flow_id}
        pass
    return json.dumps({
        "flow_id": flow_id,
        "previous_status": "live",
        "new_status": "paused",
        "reason": reason,
        "contacts_in_queue": 342,
        "paused_at": datetime.utcnow().isoformat() + "Z",
        "status": "success"
    })


@mcp.tool()
def get_ab_test_results(flow_id: str, step_index: int) -> str:
    """Retrieve A/B test results for a specific step in a Klaviyo flow."""
    logger.info("get_ab_test_results called | flow_id=%s step=%d", flow_id, step_index)
    if not USE_MOCK:
        # Real API: GET /api/flows/{flow_id}/flow-actions with A/B data
        pass
    return json.dumps({
        "flow_id": flow_id,
        "step_index": step_index,
        "test_type": "subject_line",
        "sample_size": 4200,
        "statistical_significance": 0.96,
        "winner": "variant_b",
        "variants": {
            "variant_a": {
                "subject": "See how Company X grew 3x",
                "open_rate": 0.31,
                "click_rate": 0.07,
                "conversion_rate": 0.024
            },
            "variant_b": {
                "subject": "Your custom growth playbook is ready",
                "open_rate": 0.39,
                "click_rate": 0.11,
                "conversion_rate": 0.038
            }
        },
        "recommendation": "Deploy variant_b to remaining audience",
        "tested_at": "2026-04-03T10:00:00Z"
    })


@mcp.tool()
def get_send_metrics(campaign_id: str) -> str:
    """Get detailed send and deliverability metrics for a Klaviyo campaign."""
    logger.info("get_send_metrics called | campaign_id=%s", campaign_id)
    if not USE_MOCK:
        # Real API: GET /api/campaigns/{campaign_id}/metrics
        pass
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "Spring Decision Accelerator",
        "sent_at": "2026-04-02T09:30:00Z",
        "metrics": {
            "total_sent": 8640,
            "delivered": 8467,
            "bounced": 173,
            "bounce_rate": 0.020,
            "opened": 3218,
            "open_rate": 0.380,
            "clicked": 812,
            "click_rate": 0.096,
            "converted": 94,
            "conversion_rate": 0.011,
            "revenue": 14100.00,
            "spam_complaints": 3,
            "unsubscribed": 28
        }
    })


@mcp.tool()
def optimise_send_time(segment_id: str, timezone: str) -> str:
    """Calculate the optimal email send time for a segment based on historical engagement."""
    logger.info("optimise_send_time called | segment_id=%s timezone=%s", segment_id, timezone)
    if not USE_MOCK:
        # Real API: Klaviyo Smart Send Time
        pass
    return json.dumps({
        "segment_id": segment_id,
        "timezone": timezone,
        "optimal_send_time": "09:15",
        "optimal_day": "Tuesday",
        "confidence": 0.87,
        "analysis": {
            "best_hours": ["09:00-10:00", "13:00-14:00", "19:00-20:00"],
            "best_days": ["Tuesday", "Thursday", "Wednesday"],
            "worst_hours": ["22:00-06:00"],
            "data_points_analysed": 42000
        },
        "recommendation": "Schedule for Tuesday 09:15 in target timezone for peak engagement",
        "computed_at": datetime.utcnow().isoformat() + "Z"
    })


@mcp.tool()
def clone_template(template_id: str, new_name: str, modifications: str) -> str:
    """Clone an existing Klaviyo email template with optional modifications."""
    logger.info("clone_template called | template_id=%s new_name=%s", template_id, new_name)
    if not USE_MOCK:
        # Real API: POST /api/templates (clone)
        pass
    return json.dumps({
        "original_template_id": template_id,
        "new_template_id": "TPL-8847",
        "new_name": new_name,
        "modifications_applied": json.loads(modifications) if modifications else {},
        "created_at": datetime.utcnow().isoformat() + "Z",
        "preview_url": "https://klaviyo.com/templates/TPL-8847/preview",
        "status": "draft"
    })


if __name__ == "__main__":
    mcp.run()
