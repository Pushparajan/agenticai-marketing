# Capstone Command Centre

**Chapters 13–14 — Full-Journey Orchestration with LangGraph + MCP**

The Command Centre wires all six customer-journey stages into a single
LangGraph `StateGraph`. Each stage runs as a concurrent node via the
`Send` API, and a **MarketingOpsDirector** agent reviews every proposed
action before execution (human-in-the-loop via `interrupt_before`).

---

## Architecture

```
                        ┌──────────────────────────┐
                        │     orchestrator.py       │
                        │  LangGraph StateGraph     │
                        │  CommandCentreState       │
                        └────────┬─────────────────┘
                                 │
                    fan_out (Send API – concurrent)
          ┌──────────┬──────────┼──────────┬──────────┬──────────┐
          ▼          ▼          ▼          ▼          ▼          ▼
   ┌───────────┐┌──────────┐┌─────────┐┌──────────┐┌─────────┐┌─────────┐
   │ Awareness ││Consider- ││Decision ││Onboard-  ││Retention││Advocacy │
   │   Node    ││ation Node││  Node   ││ing Node  ││  Node   ││  Node   │
   │(OpenAI)   ││(CrewAI)  ││(LangGr.)││(AutoGen) ││(AG+MCP) ││(MCP+OAI)│
   └─────┬─────┘└────┬─────┘└────┬────┘└────┬─────┘└────┬────┘└────┬────┘
         │           │           │           │           │          │
         └───────────┴───────────┴─────┬─────┴───────────┴──────────┘
                                       ▼
                          ┌────────────────────────┐
                          │  review_and_approve     │
                          │  MarketingOpsDirector   │
                          │  (interrupt_before HITL)│
                          └───────────┬────────────┘
                                      ▼
                          ┌────────────────────────┐
                          │   generate_report       │
                          │   Execution summary     │
                          └────────────────────────┘
```

### MCP Tool Layer

All stage nodes call marketing-platform tools through `mcp_client.py`,
which provides a unified `get_tool(server, tool_name)` interface to the
six MCP servers defined in `mcp_servers/server_config.yaml`:

| Server | Platform | Port | Used By Stages |
|--------|----------|------|----------------|
| `crm_server` | HubSpot | 5100 | All |
| `cdp_server` | Segment | 5101 | 1, 5 |
| `email_server` | Klaviyo | 5102 | 2, 3 |
| `paid_media_server` | Google Ads | 5103 | 1 |
| `analytics_server` | Amplitude | 5104 | All |
| `advocacy_server` | G2/Capterra | 5105 | 6 |

---

## Files

| File | Purpose |
|------|---------|
| `mcp_client.py` | Unified MCP client — mock wrappers in demo mode |
| `stage_agents/awareness_node.py` | Stage 1 discovery + triage |
| `stage_agents/consideration_node.py` | Stage 2 crew logic |
| `stage_agents/decision_node.py` | Stage 3 conversion graph |
| `stage_agents/onboarding_node.py` | Stage 4 onboarding room |
| `stage_agents/retention_node.py` | Stage 5 retention room |
| `stage_agents/advocacy_node.py` | Stage 6 advocacy agent |
| `director_agent.py` | MarketingOpsDirector — approval gate |
| `orchestrator.py` | LangGraph StateGraph — main entry point |

---

## Quick Start

```bash
# Run in mock mode (no API keys required)
export USE_MOCK_APIS=true

cd capstone_command_centre
python orchestrator.py
```

The demo processes a sample contact (`alex@acmecorp.com`) through all six
stages concurrently, submits proposed actions for director review, and
prints a full execution report.

### With real APIs

```bash
export USE_MOCK_APIS=false
export OPENAI_API_KEY=sk-...
export HUBSPOT_API_KEY=pat-...
export SEGMENT_API_TOKEN=...
export KLAVIYO_API_KEY=...
# ... see .env.example for all keys

python orchestrator.py
```

---

## Director Thresholds

The MarketingOpsDirector will flag actions for human review when:

- **Spend** exceeds £500
- **Bulk operations** target more than 100 contacts
- **High-stakes messages** (legal, pricing, contract terms)
- **Brand safety** concerns detected in generated copy
- **Frequency limits** exceeded (max 3 touches per contact per week)

---

## Author

**Pushparajan Ramar**
[github.com/Pushparajan/agenticai-marketing](https://github.com/Pushparajan/agenticai-marketing)
