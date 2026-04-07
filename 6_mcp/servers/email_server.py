"""
File: email_server.py
Project: Marketing Operations Command Centre — Chapter 8
Description: MCP server for Klaviyo email marketing
Author: Pushparajan Ramar
"""
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
logger = logging.getLogger(__name__)
USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

mcp = FastMCP("klaviyo-email")


@mcp.tool()
def get_flow_performance(flow_id: str) -> str:
    """Retrieve performance metrics for a Klaviyo email flow.

    Args:
        flow_id: The Klaviyo flow identifier.

    Returns:
        JSON string with open rates, click rates, revenue, and per-step
        breakdown for the flow.
    """
    logger.info("[%s] get_flow_performance: %s", datetime.now().isoformat(), flow_id)
    if not USE_MOCK:
        # Real API: from klaviyo_api import KlaviyoAPI
        # client = KlaviyoAPI(os.getenv("KLAVIYO_API_KEY"))
        # client.Flows.get_flow(flow_id)
        pass
    # MOCK MODE
    return json.dumps({
        "flow_id": flow_id,
        "name": "Post-Demo Nurture Sequence",
        "status": "live",
        "total_recipients": 2841,
        "overall_metrics": {
            "open_rate": 0.412,
            "click_rate": 0.087,
            "conversion_rate": 0.034,
            "revenue_attributed": 28450.00,
            "unsubscribe_rate": 0.006,
        },
        "steps": [
            {"step": 1, "subject": "Thanks for your demo — here's what's next",
             "sent": 2841, "open_rate": 0.62, "click_rate": 0.14},
            {"step": 2, "subject": "3 ways teams like yours use our platform",
             "sent": 2604, "open_rate": 0.45, "click_rate": 0.09},
            {"step": 3, "subject": "Your personalised ROI estimate",
             "sent": 2210, "open_rate": 0.38, "click_rate": 0.07},
        ],
        "period": "last_90_days",
    })


@mcp.tool()
def create_flow(name: str, trigger_event: str, steps: int = 3) -> str:
    """Create a new automated email flow in Klaviyo.

    Args:
        name: Human-readable name for the flow.
        trigger_event: The event that triggers the flow (e.g. 'demo_completed').
        steps: Number of email steps in the flow.

    Returns:
        JSON string with the created flow configuration.
    """
    logger.info("[%s] create_flow: %s (trigger=%s)", datetime.now().isoformat(), name, trigger_event)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "flow_id": "FLOW-29481",
        "name": name,
        "trigger_event": trigger_event,
        "status": "draft",
        "steps_created": steps,
        "steps": [
            {"step": i + 1, "type": "email", "delay_hours": (i * 48),
             "subject": f"Step {i + 1} — placeholder subject"}
            for i in range(steps)
        ],
        "created_at": datetime.now().isoformat(),
        "created_by": "marketing-ops-agent",
    })


@mcp.tool()
def enrol_contact(flow_id: str, email: str) -> str:
    """Manually enrol a contact into a Klaviyo flow.

    Args:
        flow_id: The flow to enrol the contact into.
        email: The contact's email address.

    Returns:
        JSON string confirming the enrolment.
    """
    logger.info("[%s] enrol_contact: %s -> %s", datetime.now().isoformat(), email, flow_id)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "enrolment_id": "ENR-71923",
        "flow_id": flow_id,
        "email": email,
        "status": "enrolled",
        "first_email_scheduled": "2026-04-07T10:00:00Z",
        "enrolled_at": datetime.now().isoformat(),
    })


@mcp.tool()
def get_ab_test_results(campaign_id: str) -> str:
    """Retrieve A/B test results for a Klaviyo email campaign.

    Args:
        campaign_id: The campaign identifier with an active A/B test.

    Returns:
        JSON string with variant performance and statistical significance.
    """
    logger.info("[%s] get_ab_test_results: %s", datetime.now().isoformat(), campaign_id)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "campaign_id": campaign_id,
        "campaign_name": "Spring Product Launch",
        "test_type": "subject_line",
        "total_recipients": 24800,
        "variants": [
            {
                "variant": "A",
                "subject": "Introducing our most powerful feature yet",
                "sent": 12400,
                "open_rate": 0.341,
                "click_rate": 0.062,
                "conversion_rate": 0.021,
                "revenue": 6480.00,
            },
            {
                "variant": "B",
                "subject": "You asked, we built it — see what's new",
                "sent": 12400,
                "open_rate": 0.398,
                "click_rate": 0.081,
                "conversion_rate": 0.029,
                "revenue": 8920.00,
            },
        ],
        "winner": "B",
        "statistical_significance": 0.96,
        "confidence_level": 0.95,
        "test_duration_hours": 48,
    })


@mcp.tool()
def pause_flow(flow_id: str, reason: str = "manual pause") -> str:
    """Pause a live Klaviyo flow.

    Args:
        flow_id: The flow to pause.
        reason: Reason for pausing the flow.

    Returns:
        JSON string confirming the flow has been paused.
    """
    logger.info("[%s] pause_flow: %s (reason=%s)", datetime.now().isoformat(), flow_id, reason)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "flow_id": flow_id,
        "name": "Post-Demo Nurture Sequence",
        "previous_status": "live",
        "new_status": "paused",
        "reason": reason,
        "contacts_in_flow": 842,
        "paused_at": datetime.now().isoformat(),
        "paused_by": "marketing-ops-agent",
    })


@mcp.tool()
def get_send_metrics(date_from: str, date_to: str) -> str:
    """Retrieve aggregate email send metrics across all campaigns.

    Args:
        date_from: Start date in YYYY-MM-DD format.
        date_to: End date in YYYY-MM-DD format.

    Returns:
        JSON string with aggregate send, open, click, and revenue metrics.
    """
    logger.info("[%s] get_send_metrics: %s to %s", datetime.now().isoformat(), date_from, date_to)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "period": {"from": date_from, "to": date_to},
        "total_sent": 184320,
        "total_delivered": 179841,
        "delivery_rate": 0.9757,
        "total_opens": 68742,
        "unique_open_rate": 0.3823,
        "total_clicks": 14289,
        "unique_click_rate": 0.0795,
        "total_conversions": 3841,
        "conversion_rate": 0.0214,
        "revenue_attributed": 142800.00,
        "unsubscribes": 412,
        "spam_complaints": 18,
        "bounce_rate": 0.0243,
        "top_performing_campaign": {
            "name": "Spring Product Launch — Variant B",
            "open_rate": 0.398,
            "click_rate": 0.081,
        },
    })


@mcp.tool()
def optimise_send_time(segment_id: str) -> str:
    """Calculate optimal send times for an audience segment.

    Args:
        segment_id: The audience segment to analyse.

    Returns:
        JSON string with recommended send windows by day of week.
    """
    logger.info("[%s] optimise_send_time: %s", datetime.now().isoformat(), segment_id)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "segment_id": segment_id,
        "segment_name": "High-Intent Enterprise Buyers",
        "analysis_period": "last_90_days",
        "sample_size": 14280,
        "optimal_windows": [
            {"day": "Tuesday", "time_utc": "14:00", "expected_open_rate": 0.44},
            {"day": "Thursday", "time_utc": "10:00", "expected_open_rate": 0.41},
            {"day": "Wednesday", "time_utc": "15:00", "expected_open_rate": 0.39},
        ],
        "worst_windows": [
            {"day": "Saturday", "time_utc": "08:00", "expected_open_rate": 0.18},
            {"day": "Monday", "time_utc": "07:00", "expected_open_rate": 0.21},
        ],
        "timezone_distribution": {"US_Eastern": 0.42, "US_Pacific": 0.28, "EU_Central": 0.18, "Other": 0.12},
        "computed_at": datetime.now().isoformat(),
    })


@mcp.tool()
def clone_template(template_id: str, new_name: str) -> str:
    """Clone an existing Klaviyo email template with a new name.

    Args:
        template_id: The source template identifier.
        new_name: Name for the cloned template.

    Returns:
        JSON string with the new template details.
    """
    logger.info("[%s] clone_template: %s -> %s", datetime.now().isoformat(), template_id, new_name)
    if not USE_MOCK:
        pass
    # MOCK MODE
    return json.dumps({
        "source_template_id": template_id,
        "new_template_id": "TPL-88241",
        "name": new_name,
        "html_size_kb": 42.3,
        "sections": ["header", "hero_image", "body_copy", "cta_button", "footer"],
        "dynamic_blocks": 4,
        "mobile_responsive": True,
        "created_at": datetime.now().isoformat(),
        "status": "draft",
    })


if __name__ == "__main__":
    mcp.run()
