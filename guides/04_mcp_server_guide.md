# MCP Server Guide

## Overview

The capstone project (Chapter 8) uses 6 MCP (Model Context Protocol) servers, each wrapping a marketing platform:

| Server | File | Tools Exposed |
|--------|------|---------------|
| CRM | `servers/crm_server.py` | 8 HubSpot tools |
| CDP | `servers/cdp_server.py` | 8 Segment tools |
| Email | `servers/email_server.py` | 8 Klaviyo tools |
| Paid Media | `servers/paid_media_server.py` | 8 Google Ads tools |
| Analytics | `servers/analytics_server.py` | 6 Amplitude tools |
| Content | `servers/content_server.py` | 6 Contentful tools |

## Running a Server

```bash
cd 6_mcp/servers
python crm_server.py
```

Each server runs on stdio transport by default (designed for MCP client integration).

## Testing with MCP Inspector

```bash
# Install MCP inspector
pip install mcp

# Inspect available tools
mcp inspect 6_mcp/servers/crm_server.py
```

## Using in the Capstone Project

The `mcp_client.py` in `project8_command_centre/` connects to all 6 servers and exposes their tools to the LangGraph agents. See the capstone project README for the full architecture.

## Mock Mode

All servers check for `USE_MOCK_APIS=true` and return realistic marketing data. You can run and test every server without real API credentials.

## Adding Custom Servers

To add your own MCP server:

1. Create a new file in `servers/`
2. Use the `mcp` SDK to define tools
3. Each tool should have real + mock implementations
4. Register the server in `project8_command_centre/mcp_client.py`
