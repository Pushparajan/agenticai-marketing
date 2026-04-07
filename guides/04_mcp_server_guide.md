# MCP Server Guide

## Overview

Six MCP servers expose the full marketing stack for the capstone and advanced stages:

| Server | Platform | Tools | Used By |
|--------|----------|-------|---------|
| `crm_server.py` | HubSpot | 8 | All stages |
| `cdp_server.py` | Segment | 8 | Awareness, Retention |
| `email_server.py` | Klaviyo | 8 | Consideration, Decision |
| `paid_media_server.py` | Google Ads | 8 | Awareness |
| `analytics_server.py` | Amplitude | 8 | All stages |
| `advocacy_server.py` | G2/Capterra | 8 | Advocacy |

## Running a Server

```bash
cd mcp_servers
python crm_server.py
```

Servers use stdio transport by default (designed for MCP client integration).

## Testing

```bash
pip install mcp
mcp inspect mcp_servers/crm_server.py
```

## Mock Mode

All servers return realistic marketing data when `USE_MOCK_APIS=true`. No real API credentials needed.

## Configuration

See `mcp_servers/server_config.yaml` for server names, descriptions, and tool listings.

## Using in the Capstone

The `capstone_command_centre/mcp_client.py` connects to all 6 servers and exposes tools to LangGraph agents.
