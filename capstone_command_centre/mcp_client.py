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
import logging, os, uuid
from datetime import datetime, timezone
from typing import Any, Callable

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"
logger = logging.getLogger(__name__)
_call_log: list[dict[str, Any]] = []

def get_call_log() -> list[dict[str, Any]]:
    return list(_call_log)

def _log_call(server: str, tool: str, stage: str, args: dict) -> None:
    _call_log.append({"timestamp": datetime.now(timezone.utc).isoformat(),
                      "server": server, "tool": tool, "stage": stage,
                      "args_summary": {k: str(v)[:80] for k, v in args.items()}})
    logger.info("MCP call  %-18s / %-28s  stage=%s", server, tool, stage)

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uid() -> str:
    return str(uuid.uuid4())[:8]

# -- CRM Server (HubSpot) --------------------------------------------------
_CRM = {
    "get_contact": lambda email="", **k: {
        "found": True, "contact_id": "C-1001", "email": email,
        "firstname": "Alex", "lastname": "Rivera", "company": "Acme Corp",
        "stage": "customer", "ltv": 48_000, "nps": 9, "tenure_months": 14},
    "update_lifecycle_stage": lambda contact_id="", stage="", **k: {
        "contact_id": contact_id, "stage": stage, "updated": True},
    "create_contact": lambda email="", **k: {
        "contact_id": _uid(), "email": email, "stage": "subscriber", "created": True},
    "log_journey_event": lambda contact_id="", event="", **k: {
        "logged": True, "contact_id": contact_id, "event": event, "ts": _ts()},
    "get_deal": lambda deal_id="", **k: {
        "deal_id": deal_id, "value": 24_000, "stage": "proposal_sent",
        "days_open": 12, "probability": 0.72},
    "update_deal_stage": lambda deal_id="", stage="", **k: {
        "deal_id": deal_id, "stage": stage, "updated": True},
    "create_task": lambda contact_id="", title="", **k: {
        "task_id": _uid(), "contact_id": contact_id, "title": title, "created": True},
    "bulk_export_contacts": lambda segment="all", **k: {
        "exported": 47, "segment": segment, "file": "export_mock.csv"},
}
# -- CDP Server (Segment) --------------------------------------------------
_CDP = {
    "get_contact_events": lambda email="", **k: {"email": email, "events": [
        {"event": "page_view", "page": "/pricing", "ts": _ts()},
        {"event": "content_download", "asset": "roi_guide.pdf", "ts": _ts()}]},
    "compute_intent_score": lambda email="", **k: {
        "email": email, "intent_score": 78, "tier": "high"},
    "get_audience_segment": lambda segment_id="high_intent", **k: {
        "segment_id": segment_id, "size": 342, "description": "High-intent MQLs"},
    "get_journey_stage": lambda email="", **k: {
        "email": email, "current_stage": "consideration", "days_in_stage": 5},
    "identify_churn_risk_cohort": lambda **k: {
        "cohort_size": 23, "avg_risk_score": 0.71,
        "top_signals": ["usage_decline", "support_tickets"]},
    "get_ltv_prediction": lambda email="", **k: {
        "email": email, "predicted_ltv": 52_000, "confidence": 0.84},
    "merge_identity_graph": lambda email="", **k: {
        "email": email, "merged_profiles": 2, "unified_id": "UID-3301"},
    "export_segment": lambda segment_id="default", **k: {
        "segment_id": segment_id, "exported": 342, "destination": "crm"},
}
# -- Email Server (Klaviyo) ------------------------------------------------
_EMAIL = {
    "get_flow_performance": lambda flow_id="nurture_v2", **k: {
        "flow_id": flow_id, "sent": 1240, "opened": 446,
        "clicked": 178, "open_rate": 0.36, "ctr": 0.14},
    "create_flow": lambda name="new_flow", **k: {
        "flow_id": _uid(), "name": name, "created": True},
    "enrol_contact": lambda contact_id="", flow_id="", **k: {
        "enrolled": True, "contact_id": contact_id, "flow_id": flow_id},
    "pause_flow": lambda flow_id="", **k: {"flow_id": flow_id, "paused": True},
    "get_ab_test_results": lambda test_id="ab_01", **k: {
        "test_id": test_id, "winner": "variant_b", "lift": 0.18, "confidence": 0.96},
    "get_send_metrics": lambda **k: {
        "total_sent": 4820, "bounced": 34, "unsubscribed": 12},
    "optimise_send_time": lambda contact_id="", **k: {
        "contact_id": contact_id, "optimal_hour_utc": 14, "day": "Tuesday"},
    "clone_template": lambda template_id="", **k: {
        "new_template_id": _uid(), "cloned_from": template_id},
}
# -- Analytics Server (Amplitude) ------------------------------------------
_ANALYTICS = {
    "get_funnel_metrics": lambda **k: {
        "awareness_to_consideration": 0.32, "consideration_to_decision": 0.48,
        "decision_to_closed": 0.41, "overall": 0.063},
    "get_stage_conversion_rates": lambda **k: {
        "awareness": 0.32, "consideration": 0.48, "decision": 0.41,
        "onboarding": 0.88, "retention": 0.79},
    "get_attribution_report": lambda **k: {"top_channels": [
        {"channel": "organic_search", "conversions": 124, "revenue": 312_000},
        {"channel": "paid_social", "conversions": 87, "revenue": 198_000}]},
    "get_cohort_retention": lambda **k: {
        "month_1": 0.92, "month_3": 0.81, "month_6": 0.74, "month_12": 0.68},
    "get_time_to_value": lambda contact_id="", **k: {
        "contact_id": contact_id, "days_to_value": 8, "benchmark": 14},
    "get_ltv_by_segment": lambda **k: {
        "enterprise": 96_000, "mid_market": 42_000, "smb": 12_000},
}
# -- Advocacy Server (G2/Capterra) -----------------------------------------
_ADVOCACY = {
    "identify_advocates": lambda **k: {"advocates": [
        {"email": "alex@acmecorp.com", "nps": 9, "ltv": 48_000, "eligible": True},
        {"email": "dana@bigco.org", "nps": 10, "ltv": 62_000, "eligible": True}]},
    "request_g2_review": lambda email="", **k: {
        "email": email, "review_requested": True, "platform": "G2"},
    "request_capterra_review": lambda email="", **k: {
        "email": email, "review_requested": True, "platform": "Capterra"},
    "trigger_referral_programme": lambda email="", **k: {
        "email": email, "referral_code": "REF-" + uuid.uuid4().hex[:6].upper(),
        "enrolled": True},
    "invite_to_community": lambda email="", **k: {
        "email": email, "community_invite_sent": True},
    "request_case_study": lambda email="", **k: {
        "email": email, "case_study_requested": True, "status": "pending_approval"},
    "get_nps_distribution": lambda **k: {
        "promoters": 64, "passives": 22, "detractors": 14, "nps_score": 50},
    "get_referral_pipeline": lambda **k: {
        "active_referrals": 18, "converted": 7, "pipeline_value": 84_000},
}

# ---------------------------------------------------------------------------
# Server -> tool registry
# ---------------------------------------------------------------------------
_MOCK_REGISTRY: dict[str, dict[str, Callable[..., dict]]] = {
    "crm_server": _CRM, "cdp_server": _CDP, "email_server": _EMAIL,
    "analytics_server": _ANALYTICS, "advocacy_server": _ADVOCACY,
}

_SERVER_PORTS = {"crm_server": 5100, "cdp_server": 5101, "email_server": 5102,
                 "paid_media_server": 5103, "analytics_server": 5104,
                 "advocacy_server": 5105}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_tool(server_name: str, tool_name: str, *,
             stage: str = "unknown") -> Callable[..., dict]:
    """Return a callable for *tool_name* on *server_name*.

    In mock mode the callable is a direct function wrapper.  In live mode
    it connects to the MCP server over HTTP (requires running servers).
    Every invocation is logged with stage attribution.
    """
    if USE_MOCK:
        server_tools = _MOCK_REGISTRY.get(server_name)
        if not server_tools:
            raise ValueError(f"Unknown MCP server: {server_name}")
        fn = server_tools.get(tool_name)
        if not fn:
            raise ValueError(f"Unknown tool '{tool_name}' on '{server_name}'. "
                             f"Available: {list(server_tools)}")
        def _wrapper(**kwargs: Any) -> dict:
            _log_call(server_name, tool_name, stage, kwargs)
            try:
                return fn(**kwargs)
            except Exception as exc:
                logger.error("Tool %s/%s failed: %s", server_name, tool_name, exc)
                return {"error": str(exc)}
        return _wrapper

    # Live MCP mode
    def _live(**kwargs: Any) -> dict:
        _log_call(server_name, tool_name, stage, kwargs)
        try:
            import httpx
            port = _SERVER_PORTS.get(server_name, 5100)
            r = httpx.post(f"http://localhost:{port}/call_tool",
                           json={"tool": tool_name, "args": kwargs}, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            logger.error("Live MCP %s/%s failed: %s", server_name, tool_name, exc)
            return {"error": str(exc), "server": server_name, "tool": tool_name}
    return _live

def list_servers() -> list[str]:
    """Return the names of all known MCP servers."""
    return list(_MOCK_REGISTRY)

def list_tools(server_name: str) -> list[str]:
    """Return the tool names available on a given server."""
    return list(_MOCK_REGISTRY.get(server_name, {}))
