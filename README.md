# Mastering Agentic AI for Marketing Technology

**Companion code repository for the book by Pushparajan Ramar**

Build production-grade AI agents that automate the modern marketing stack — from CRM enrichment to campaign orchestration, demand generation to real-time analytics.

---

## What You'll Build

| # | Project | Framework | Folder | Chapter |
|---|---------|-----------|--------|---------|
| — | LLM Foundations | OpenAI / Claude / Gemini | `1_foundations/` | 1–2 |
| 1 | Customer Journey Digital Twin | OpenAI Agents SDK | `2_openai_sdk/project1_journey_twin/` | 3 |
| 2 | Autonomous SDR Outreach Agent | OpenAI Agents SDK | `2_openai_sdk/project2_sdr_outreach/` | 3 |
| 3 | Campaign Intelligence Crew | CrewAI | `3_crewai/project3_campaign_intelligence/` | 4 |
| 4 | Demand Gen Pipeline Crew | CrewAI | `3_crewai/project4_demand_gen/` | 5 |
| 5 | Adaptive Journey Orchestrator | LangGraph | `4_langgraph/project5_journey_orchestrator/` | 6 |
| 6 | MarTech Analyst Sidekick | LangGraph + Gradio | `4_langgraph/project6_analyst_sidekick/` | 6 |
| 7 | Campaign Intelligence Room | AutoGen | `5_autogen/project7_campaign_intelligence_room/` | 7 |
| 8 | Marketing Ops Command Centre | LangGraph + MCP | `6_mcp/project8_command_centre/` | 8 |

---

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
- API keys for LLM providers (OpenAI, Anthropic, or Google — at least one)
- Optional: HubSpot, Klaviyo, Segment accounts (all projects run in mock mode without them)

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Pushparajan/agenticai-marketing.git
cd agenticai-marketing

# 2. Install dependencies
uv sync                    # or: pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env       # Edit .env with your API keys

# 4. Run your first project
cd 2_openai_sdk/project1_journey_twin
python app.py
```

---

## Running with Free LLMs (Ollama)

Every project can run with local models via Ollama — zero API spend:

```bash
# Install Ollama (https://ollama.com)
ollama pull llama3.1

# Set in your .env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
```

See [guides/01_free_tier_ollama.md](guides/01_free_tier_ollama.md) for details.

---

## Mock Mode

All MarTech integrations (HubSpot, Klaviyo, Segment, Google Ads) include realistic mock implementations. With `USE_MOCK_APIS=true` in your `.env`, every project runs without any external API keys — perfect for learning and experimentation.

---

## MarTech Stack Setup

| Service | Free Tier | Setup Guide |
|---------|-----------|-------------|
| HubSpot | Developer sandbox (free) | [guides/02_hubspot_setup.md](guides/02_hubspot_setup.md) |
| Klaviyo | Free up to 250 contacts | [guides/03_klaviyo_setup.md](guides/03_klaviyo_setup.md) |
| Segment | Free developer plan | See `.env.example` |
| Google Ads | Test account (no spend) | See `.env.example` |

---

## MCP Servers (Chapter 8)

The capstone project includes 6 MCP servers exposing the full marketing stack:

```bash
# Start a single server
python 6_mcp/servers/crm_server.py

# Test with MCP inspector
mcp inspect 6_mcp/servers/crm_server.py
```

See [guides/04_mcp_server_guide.md](guides/04_mcp_server_guide.md) for the full guide.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Chapter 8: Capstone                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │Campaign  │ │Personal- │ │Media     │ │Performance       ││
│  │Planner   │ │isation   │ │Optimiser │ │Analyst           ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────────────┘│
│       │             │            │             │              │
│  ┌────▼─────────────▼────────────▼─────────────▼──────┐      │
│  │          Marketing Ops Director (HITL)              │      │
│  └────────────────────┬───────────────────────────────┘      │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐      │
│  │              MCP Client Layer                       │      │
│  └──┬────┬────┬────┬────┬────┬─────────────────────────┘      │
│     │    │    │    │    │    │                                │
│  ┌──▼─┐┌─▼──┐┌▼──┐┌▼──┐┌▼──┐┌▼──┐                          │
│  │CRM ││CDP ││Mail││Ads││Ana││CMS│  ← MCP Servers           │
│  └────┘└────┘└───┘└───┘└───┘└───┘                           │
└──────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `uv sync` or `pip install -r requirements.txt` |
| API key errors | Ensure `.env` exists and `USE_MOCK_APIS=true` for mock mode |
| OpenAI rate limits | Switch to Ollama (see guide) or add retry logic |
| HubSpot 401 | Check API key scopes — see [guides/02_hubspot_setup.md](guides/02_hubspot_setup.md) |
| MCP server won't start | Ensure `mcp>=1.0` is installed; check port conflicts |

---

## Author

**Pushparajan Ramar**
[github.com/Pushparajan/agenticai-marketing](https://github.com/Pushparajan/agenticai-marketing)

---

## License

MIT — See [LICENSE](LICENSE) for details.
