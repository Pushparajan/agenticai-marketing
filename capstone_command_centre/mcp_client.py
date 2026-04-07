# File      : mcp_client.py
# Stage     : Capstone — All Stages
# Chapter   : 13–14
# Framework : LangGraph + MCP
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Unified MCP client for the Capstone Command Centre.

Provides ``get_tool(server_name, tool_name)`` to obtain a callable that
forwards to the appropriate MCP server.  In mock / demo mode every tool
returns realistic synthetic data without needing running servers.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

logger = logging.getLogger(__name__)

# Stage attribution tracker — every tool call is logged here
_call_log: list[dict[str, Any]] = []


def get_call_log() -> list[dict[str, Any]]:
    """Return the full list of logged tool calls."""
    return list(_call_log)


def _log_call(server: str, tool: str, stage: str, args: dict) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": server,
        "tool": tool,
        "stage": stage,
        "args_summary": {k: str(v)[:80] for k, v in args.items()},
    }
    _call_log.append(entry)
    logger.info("MCP call  %-18s / %-28s  stage=%s", server, tool, stage)


# ---------------------------------------------------------------------------
# Mock tool implementations — grouped by server
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- CRM Server (HubSpot) ------------------------------------------------

def _crm_get_contact(email: str, **kw: Any) -> dict:
    return {"found": True, "contact_id": "C-1001", "email": email,
            "firstname": "Alex", "lastname": "Rivera",
            "company": "Acme Corp", "stage": "customer",
            "ltv": 48_000, "nps": 9, "tenure_months": 14}

def _crm_update_lifecycle_stage(contact_id: str, stage: str, **kw: Any) -> dict:
    return {"contact_id": contact_id, "stage": stage, "updated": True}

def _crm_create_contact(email: str, firstname: str = "", lastname: str = "",
                         company: str = "", source: str = "", **kw: Any) -> dict:
    return {"contact_id": str(uuid.uuid4())[:8], "email": email,
            "stage": "subscriber", "created": True}

def _crm_log_journey_event(contact_id: str, event: str, **kw: Any) -> dict:
    return {"logged": True, "contact_id": contact_id, "event": event, "ts": _ts()}

def _crm_get_deal(deal_id: str, **kw: Any) -> dict:
    return {"deal_id": deal_id, "value": 24_000, "stage": "proposal_sent",
            "days_open": 12, "probability": 0.72}

def _crm_update_deal_stage(deal_id: str, stage: str, **kw: Any) -> dict:
    return {"deal_id": deal_id, "stage": stage, "updated": True}

def _crm_create_task(contact_id: str, title: str, **kw: Any) -> dict:
    return {"task_id": str(uuid.uuid4())[:8], "contact_id": contact_id,
            "title": title, "created": True}

def _crm_bulk_export_contacts(segment: str = "all", **kw: Any) -> dict:
    return {"exported": 47, "segment": segment, "file": "export_mock.csv"}

# ---- CDP Server (Segment) ------------------------------------------------

def _cdp_get_contact_events(email: str, **kw: Any) -> dict:
    return {"email": email, "events": [
        {"event": "page_view", "page": "/pricing", "ts": _ts()},
        {"event": "content_download", "asset": "roi_guide.pdf", "ts": _ts()},
    ]}

def _cdp_compute_intent_score(email: str, **kw: Any) -> dict:
    return {"email": email, "intent_score": 78, "tier": "high"}

def _cdp_get_audience_segment(segment_id: str = "high_intent", **kw: Any) -> dict:
    return {"segment_id": segment_id, "size": 342, "description": "High-intent MQLs"}

def _cdp_get_journey_stage(email: str, **kw: Any) -> dict:
    return {"email": email, "current_stage": "consideration", "days_in_stage": 5}

def _cdp_identify_churn_risk_cohort(**kw: Any) -> dict:
    return {"cohort_size": 23, "avg_risk_score": 0.71,
            "top_signals": ["usage_decline", "support_tickets"]}

def _cdp_get_ltv_prediction(email: str, **kw: Any) -> dict:
    return {"email": email, "predicted_ltv": 52_000, "confidence": 0.84}

def _cdp_merge_identity_graph(email: str, **kw: Any) -> dict:
    return {"email": email, "merged_profiles": 2, "unified_id": "UID-3301"}

def _cdp_export_segment(segment_id: str = "default", **kw: Any) -> dict:
    return {"segment_id": segment_id, "exported": 342, "destination": "crm"}

# ---- Email Server (Klaviyo) ----------------------------------------------

def _email_get_flow_performance(flow_id: str = "nurture_v2", **kw: Any) -> dict:
    return {"flow_id": flow_id, "sent": 1_240, "opened": 446,
            "clicked": 178, "open_rate": 0.36, "ctr": 0.14}

def _email_create_flow(name: str = "new_flow", **kw: Any) -> dict:
    return {"flow_id": str(uuid.uuid4())[:8], "name": name, "created": True}

def _email_enrol_contact(contact_id: str, flow_id: str, **kw: Any) -> dict:
    return {"enrolled": True, "contact_id": contact_id, "flow_id": flow_id}

def _email_pause_flow(flow_id: str, **kw: Any) -> dict:
    return {"flow_id": flow_id, "paused": True}

def _email_get_ab_test_results(test_id: str = "ab_subject_01", **kw: Any) -> dict:
    return {"test_id": test_id, "winner": "variant_b",
            "lift": 0.18, "confidence": 0.96}

def _email_get_send_metrics(**kw: Any) -> dict:
    return {"total_sent": 4_820, "bounced": 34, "unsubscribed": 12}

def _email_optimise_send_time(contact_id: str, **kw: Any) -> dict:
    return {"contact_id": contact_id, "optimal_hour_utc": 14, "day": "Tuesday"}

def _email_clone_template(template_id: str, **kw: Any) -> dict:
    return {"new_template_id": str(uuid.uuid4())[:8], "cloned_from": template_id}

# ---- Analytics Server (Amplitude) ----------------------------------------

def _analytics_get_funnel_metrics(**kw: Any) -> dict:
    return {"awareness_to_consideration": 0.32, "consideration_to_decision": 0.48,
            "decision_to_closed": 0.41, "overall": 0.063}

def _analytics_get_stage_conversion_rates(**kw: Any) -> dict:
    return {"awareness": 0.32, "consideration": 0.48,
            "decision": 0.41, "onboarding": 0.88, "retention": 0.79}

def _analytics_get_attribution_report(**kw: Any) -> dict:
    return {"top_channels": [
        {"channel": "organic_search", "conversions": 124, "revenue": 312_000},
        {"channel": "paid_social", "conversions": 87, "revenue": 198_000},
    ]}

def _analytics_get_cohort_retention(**kw: Any) -> dict:
    return {"month_1": 0.92, "month_3": 0.81, "month_6": 0.74, "month_12": 0.68}

def _analytics_get_time_to_value(contact_id: str = "", **kw: Any) -> dict:
    return {"contact_id": contact_id, "days_to_value": 8, "benchmark": 14}

def _analytics_get_ltv_by_segment(**kw: Any) -> dict:
    return {"enterprise": 96_000, "mid_market": 42_000, "smb": 12_000}

# ---- Advocacy Server (G2/Capterra) ---------------------------------------

def _advocacy_identify_advocates(**kw: Any) -> dict:
    return {"advocates": [
        {"email": "alex@acmecorp.com", "nps": 9, "ltv": 48_000, "eligible": True},
        {"email": "dana@bigco.org", "nps": 10, "ltv": 62_000, "eligible": True},
    ]}

def _advocacy_request_g2_review(email: str, **kw: Any) -> dict:
    return {"email": email, "review_requested": True, "platform": "G2"}

def _advocacy_request_capterra_review(email: str, **kw: Any) -> dict:
    return {"email": email, "review_requested": True, "platform": "Capterra"}

def _advocacy_trigger_referral_programme(email: str, **kw: Any) -> dict:
    return {"email": email, "referral_code": "REF-" + uuid.uuid4().hex[:6].upper(),
            "enrolled": True}

def _advocacy_invite_to_community(email: str, **kw: Any) -> dict:
    return {"email": email, "community_invite_sent": True}

def _advocacy_request_case_study(email: str, **kw: Any) -> dict:
    return {"email": email, "case_study_requested": True, "status": "pending_approval"}

def _advocacy_get_nps_distribution(**kw: Any) -> dict:
    return {"promoters": 64, "passives": 22, "detractors": 14, "nps_score": 50}

def _advocacy_get_referral_pipeline(**kw: Any) -> dict:
    return {"active_referrals": 18, "converted": 7, "pipeline_value": 84_000}


# ---------------------------------------------------------------------------
# Server → tool registry
# ---------------------------------------------------------------------------

_MOCK_REGISTRY: dict[str, dict[str, Callable[..., dict]]] = {
    "crm_server": {
        "get_contact": _crm_get_contact,
        "update_lifecycle_stage": _crm_update_lifecycle_stage,
        "create_contact": _crm_create_contact,
        "log_journey_event": _crm_log_journey_event,
        "get_deal": _crm_get_deal,
        "update_deal_stage": _crm_update_deal_stage,
        "create_task": _crm_create_task,
        "bulk_export_contacts": _crm_bulk_export_contacts,
    },
    "cdp_server": {
        "get_contact_events": _cdp_get_contact_events,
        "compute_intent_score": _cdp_compute_intent_score,
        "get_audience_segment": _cdp_get_audience_segment,
        "get_journey_stage": _cdp_get_journey_stage,
        "identify_churn_risk_cohort": _cdp_identify_churn_risk_cohort,
        "get_ltv_prediction": _cdp_get_ltv_prediction,
        "merge_identity_graph": _cdp_merge_identity_graph,
        "export_segment": _cdp_export_segment,
    },
    "email_server": {
        "get_flow_performance": _email_get_flow_performance,
        "create_flow": _email_create_flow,
        "enrol_contact": _email_enrol_contact,
        "pause_flow": _email_pause_flow,
        "get_ab_test_results": _email_get_ab_test_results,
        "get_send_metrics": _email_get_send_metrics,
        "optimise_send_time": _email_optimise_send_time,
        "clone_template": _email_clone_template,
    },
    "analytics_server": {
        "get_funnel_metrics": _analytics_get_funnel_metrics,
        "get_stage_conversion_rates": _analytics_get_stage_conversion_rates,
        "get_attribution_report": _analytics_get_attribution_report,
        "get_cohort_retention": _analytics_get_cohort_retention,
        "get_time_to_value": _analytics_get_time_to_value,
        "get_ltv_by_segment": _analytics_get_ltv_by_segment,
    },
    "advocacy_server": {
        "identify_advocates": _advocacy_identify_advocates,
        "request_g2_review": _advocacy_request_g2_review,
        "request_capterra_review": _advocacy_request_capterra_review,
        "trigger_referral_programme": _advocacy_trigger_referral_programme,
        "invite_to_community": _advocacy_invite_to_community,
        "request_case_study": _advocacy_request_case_study,
        "get_nps_distribution": _advocacy_get_nps_distribution,
        "get_referral_pipeline": _advocacy_get_referral_pipeline,
    },
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_tool(
    server_name: str,
    tool_name: str,
    *,
    stage: str = "unknown",
) -> Callable[..., dict]:
    """Return a callable for *tool_name* on *server_name*.

    In mock mode the callable is a direct function wrapper.  In live mode
    it would connect to the MCP server over stdio/SSE (placeholder).

    Every invocation is logged with stage attribution.
    """

    if USE_MOCK:
        server_tools = _MOCK_REGISTRY.get(server_name)
        if server_tools is None:
            raise ValueError(f"Unknown MCP server: {server_name}")
        fn = server_tools.get(tool_name)
        if fn is None:
            raise ValueError(
                f"Unknown tool '{tool_name}' on server '{server_name}'. "
                f"Available: {list(server_tools.keys())}"
            )

        def _wrapper(**kwargs: Any) -> dict:
            _log_call(server_name, tool_name, stage, kwargs)
            try:
                return fn(**kwargs)
            except Exception as exc:
                logger.error("Tool %s/%s failed: %s", server_name, tool_name, exc)
                return {"error": str(exc)}

        return _wrapper

    # ----- Live MCP mode (requires running servers) -----
    def _live_wrapper(**kwargs: Any) -> dict:
        _log_call(server_name, tool_name, stage, kwargs)
        try:
            import httpx
            port = {
                "crm_server": 5100, "cdp_server": 5101,
                "email_server": 5102, "paid_media_server": 5103,
                "analytics_server": 5104, "advocacy_server": 5105,
            }.get(server_name, 5100)
            resp = httpx.post(
                f"http://localhost:{port}/call_tool",
                json={"tool": tool_name, "args": kwargs},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("Live MCP call %s/%s failed: %s",
                         server_name, tool_name, exc)
            return {"error": str(exc), "server": server_name, "tool": tool_name}

    return _live_wrapper


def list_servers() -> list[str]:
    """Return the names of all known MCP servers."""
    return list(_MOCK_REGISTRY.keys())


def list_tools(server_name: str) -> list[str]:
    """Return the tool names available on a given server."""
    return list(_MOCK_REGISTRY.get(server_name, {}).keys())
