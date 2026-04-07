# MCP Servers for Agentic AI Customer Journey Marketing

> Companion code for **"Mastering Agentic AI for Customer Journey Marketing"** by Pushparajan Ramar
> Chapters 13-14 | Framework: Model Context Protocol (MCP)

## Overview

Six MCP servers expose 48 tools that span every stage of the customer journey. Each server wraps a real marketing platform API behind a mock-first design, allowing safe local development and testing before connecting live credentials.

| Server | Platform | Stages Served | Tools | Port |
|--------|----------|---------------|-------|------|
| `crm_server.py` | HubSpot | All Stages | 8 | 5100 |
| `cdp_server.py` | Segment | Awareness, Retention | 8 | 5101 |
| `email_server.py` | Klaviyo | Consideration, Decision | 8 | 5102 |
| `paid_media_server.py` | Google Ads | Awareness | 8 | 5103 |
| `analytics_server.py` | Amplitude | All Stages | 8 | 5104 |
| `advocacy_server.py` | G2/Capterra | Advocacy | 8 | 5105 |

## Prerequisites

```bash
pip install mcp pyyaml
```

## Configuration

All server metadata is defined in `server_config.yaml`. Each entry includes the server name, description, port, platform, applicable journey stages, and the list of tools it exposes.

## Tools by Server

### crm_server.py (HubSpot)
| Tool | Description |
|------|-------------|
| `get_contact` | Retrieve a contact record by email |
| `update_lifecycle_stage` | Move a contact to a new lifecycle stage |
| `create_contact` | Create a new CRM contact |
| `log_journey_event` | Log a journey event against a contact |
| `get_deal` | Retrieve a deal by ID |
| `update_deal_stage` | Move a deal to a new pipeline stage |
| `create_task` | Create a follow-up task linked to a contact |
| `bulk_export_contacts` | Export contacts filtered by lifecycle stage |

### cdp_server.py (Segment)
| Tool | Description |
|------|-------------|
| `get_contact_events` | Retrieve recent events for a user |
| `compute_intent_score` | Compute real-time intent score (0-100) |
| `get_audience_segment` | Get metadata and size for a named segment |
| `get_journey_stage` | Determine current journey stage from behaviour |
| `identify_churn_risk_cohort` | Find users at churn risk above a threshold |
| `get_ltv_prediction` | Get predicted lifetime value for a user |
| `merge_identity_graph` | Merge two identity profiles |
| `export_segment` | Export a segment to a downstream destination |

### email_server.py (Klaviyo)
| Tool | Description |
|------|-------------|
| `get_flow_performance` | Get performance metrics for an email flow |
| `create_flow` | Create a new email automation flow |
| `enrol_contact` | Enrol a contact into a flow |
| `pause_flow` | Pause a live flow with audit reason |
| `get_ab_test_results` | Get A/B test results for a flow step |
| `get_send_metrics` | Get deliverability metrics for a campaign |
| `optimise_send_time` | Calculate optimal send time for a segment |
| `clone_template` | Clone an email template with modifications |

### paid_media_server.py (Google Ads)
| Tool | Description |
|------|-------------|
| `get_campaign_performance` | Get campaign metrics over a date range |
| `adjust_bid` | Adjust bid for an ad group |
| `create_audience` | Create a custom audience from CRM or web data |
| `pause_campaign` | Pause a campaign with documented reason |
| `get_roas` | Calculate return on ad spend |
| `allocate_budget` | Allocate budget across campaigns by strategy |
| `get_keyword_intent_data` | Get intent classification for keywords |
| `create_retargeting_list` | Create a retargeting list from URL patterns |

### analytics_server.py (Amplitude)
| Tool | Description |
|------|-------------|
| `get_funnel_metrics` | Get funnel conversion metrics |
| `get_stage_conversion_rates` | Get stage-to-stage conversion rates |
| `get_attribution_report` | Generate multi-touch attribution report |
| `get_cohort_retention` | Get retention curve for a signup cohort |
| `get_revenue_attribution` | Revenue attribution by grouping |
| `get_ltv_by_segment` | LTV analysis by segment type |
| `query_custom_event` | Query custom event data with filters |
| `get_time_to_value` | Calculate median time-to-value |

### advocacy_server.py (G2/Capterra)
| Tool | Description |
|------|-------------|
| `identify_advocates` | Find advocates by NPS, usage, and tenure |
| `request_g2_review` | Send personalised G2 review request |
| `request_capterra_review` | Send personalised Capterra review request |
| `trigger_referral_programme` | Enrol customer in referral programme |
| `invite_to_community` | Invite customer to brand community |
| `request_case_study` | Request case study participation |
| `get_nps_distribution` | Get NPS distribution and trends |
| `get_referral_pipeline` | Get referral programme pipeline data |

## Running a Server

Each server runs as a standalone MCP process using stdio transport:

```bash
# Run with mock data (default)
python crm_server.py

# Run with live API credentials
export MCP_MOCK=false
export HUBSPOT_API_KEY=your-key-here
python crm_server.py
```

## Testing with MCP Inspector

Use the MCP Inspector CLI to test individual tools:

```bash
# Install the inspector
npx @modelcontextprotocol/inspector

# Connect to a server
npx @modelcontextprotocol/inspector python crm_server.py
```

This opens a web UI where you can browse available tools, invoke them with parameters, and inspect the JSON responses.

## Testing with Python

```python
import subprocess
import json

# Start server as a subprocess and send JSON-RPC requests
# via stdin/stdout (stdio transport)
proc = subprocess.Popen(
    ["python", "crm_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Send an initialize request followed by a tool call
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "get_contact",
        "arguments": {"email": "test@example.com"}
    }
}
proc.stdin.write(json.dumps(request).encode() + b"\n")
proc.stdin.flush()
```

## Environment Variables

| Variable | Server | Description |
|----------|--------|-------------|
| `MCP_MOCK` | All | Set to `false` to use live APIs (default: `true`) |
| `HUBSPOT_API_KEY` | crm_server | HubSpot private app token |
| `SEGMENT_API_KEY` | cdp_server | Segment workspace API key |
| `KLAVIYO_API_KEY` | email_server | Klaviyo private API key |
| `GOOGLE_ADS_API_KEY` | paid_media_server | Google Ads API developer token |
| `AMPLITUDE_API_KEY` | analytics_server | Amplitude API key |
| `G2_API_KEY` | advocacy_server | G2 API key |
| `CAPTERRA_API_KEY` | advocacy_server | Capterra API key |

## Architecture

```
Agent (LLM)
  |
  |-- MCP Client
        |
        |-- crm_server.py        (HubSpot)
        |-- cdp_server.py        (Segment)
        |-- email_server.py      (Klaviyo)
        |-- paid_media_server.py (Google Ads)
        |-- analytics_server.py  (Amplitude)
        |-- advocacy_server.py   (G2/Capterra)
```

Each server communicates over stdio transport using JSON-RPC 2.0. The agent discovers available tools via the `tools/list` method, then invokes them via `tools/call`. All tool responses are JSON strings that the agent can parse and reason over.
