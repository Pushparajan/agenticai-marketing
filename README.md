# Mastering Agentic AI for Customer Journey Marketing

**Companion code repository for the book by Pushparajan Ramar**

This book takes a journey-first approach to agentic AI in marketing technology. Instead of organising by framework, each chapter maps to a stage of the customer journey — from first touch to loyal advocate — with the AI framework best suited to that stage's unique challenges.

---

## The 6-Stage Journey Map

```
┌─────────┐   ┌──────────────┐   ┌──────────┐   ┌────────────┐   ┌───────────┐   ┌──────────┐
│AWARENESS│──▶│CONSIDERATION │──▶│ DECISION │──▶│ ONBOARDING │──▶│ RETENTION │──▶│ ADVOCACY │
│ OpenAI  │   │   CrewAI     │   │ LangGraph│   │  AutoGen   │   │AutoGen+MCP│   │MCP+OpenAI│
│  Agents │   │              │   │          │   │            │   │           │   │  Agents  │
└─────────┘   └──────────────┘   └──────────┘   └────────────┘   └───────────┘   └──────────┘
```

| Stage | Folder | Framework | Chapter | Key Metric |
|-------|--------|-----------|---------|------------|
| 1 — Awareness | `stage1_awareness/` | OpenAI Agents SDK | Ch 3–4 | Intent score, MQLs |
| 2 — Consideration | `stage2_consideration/` | CrewAI | Ch 5–6 | Engagement rate, content touches |
| 3 — Decision | `stage3_decision/` | LangGraph | Ch 7–8 | Conversion rate, days to close |
| 4 — Onboarding | `stage4_onboarding/` | AutoGen | Ch 9 | Time to value, adoption score |
| 5 — Retention | `stage5_retention/` | AutoGen + MCP | Ch 10–11 | Churn risk, NPS, expansion revenue |
| 6 — Advocacy | `stage6_advocacy/` | MCP + OpenAI Agents | Ch 12 | Reviews generated, referral pipeline |
| Capstone | `capstone_command_centre/` | LangGraph + all | Ch 13–14 | Full-journey orchestration |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Pushparajan/agenticai-marketing.git
cd agenticai-marketing

# 2. Install dependencies
uv sync                    # or: pip install -r requirements.txt

# 3. Configure
cp .env.example .env       # Edit with your API keys (or leave USE_MOCK_APIS=true)

# 4. Run your first stage
cd stage1_awareness/project_demand_gen
python main.py
```

---

## Running in Mock Mode

All projects run without any external API keys when `USE_MOCK_APIS=true` (the default):

```bash
# Every tool returns realistic marketing data in mock mode
export USE_MOCK_APIS=true
cd stage1_awareness/project_demand_gen
python main.py
```

Mock mode simulates realistic CRM records, CDP events, email metrics, ad performance, and analytics data — perfect for learning and experimentation.

---

## Stage-by-Stage Navigation

### Stage 1 — Awareness (OpenAI Agents SDK)
- **Purpose:** Score anonymous visitors and first-touch leads, route high-intent signals
- **Framework:** OpenAI Agents SDK (fast triage with handoffs)
- **Trigger:** HubSpot `contact.created` or `page_visit` webhook
- **Output:** Intent score, CRM contact, routing decision (accelerate / nurture / cold)
- **Run:** `cd stage1_awareness/project_demand_gen && python main.py`
- **Book:** Chapters 3–4

### Stage 2 — Consideration (CrewAI)
- **Purpose:** Research prospects, build nurture strategies, generate conversion copy
- **Framework:** CrewAI (multi-agent crew with sequential expertise)
- **Trigger:** Lifecycle stage → MQL in HubSpot
- **Output:** Research brief, nurture sequence, personalised content
- **Run:** `cd stage2_consideration/project_campaign_crew && python main.py`
- **Book:** Chapters 5–6

### Stage 3 — Decision (LangGraph)
- **Purpose:** Adaptive deal progression with objection handling and competitive response
- **Framework:** LangGraph (stateful graph with conditional routing)
- **Trigger:** Deal created or demo completed
- **Output:** Personalised close offers, battlecards, urgency reactivation
- **Run:** `cd stage3_decision/project_conversion_graph && python main.py`
- **Book:** Chapters 7–8

### Stage 4 — Onboarding (AutoGen)
- **Purpose:** Multi-agent collaboration for new customer activation planning
- **Framework:** AutoGen (group chat for diverse expertise)
- **Trigger:** Deal closed-won, first 30 days
- **Output:** Structured onboarding action plan with activation milestones
- **Run:** `cd stage4_onboarding/project_onboarding_room && python main.py`
- **Book:** Chapter 9

### Stage 5 — Retention (AutoGen + MCP)
- **Purpose:** Detect churn risk, design interventions, calculate commercial offers
- **Framework:** AutoGen + MCP (group chat with real-time platform data)
- **Trigger:** Usage decline, NPS drop, renewal approaching, competitor mention
- **Output:** Intervention plan with risk classification and commercial terms
- **Run:** `cd stage5_retention/project_retention_room && python main.py`
- **Book:** Chapters 10–11

### Stage 6 — Advocacy (MCP + OpenAI Agents SDK)
- **Purpose:** Identify promoters and activate advocacy programmes
- **Framework:** MCP + OpenAI Agents SDK (platform tools + intelligent matching)
- **Trigger:** NPS >= 7, high LTV, recent expansion
- **Output:** Personalised advocacy asks (reviews, referrals, case studies, community)
- **Run:** `cd stage6_advocacy/project_advocacy_agent && python main.py`
- **Book:** Chapter 12

---

## MCP Servers

Six MCP servers expose the full marketing stack:

```bash
# Start any server
python mcp_servers/crm_server.py

# Test with MCP inspector
mcp inspect mcp_servers/crm_server.py
```

| Server | Platform | Tools | Used By |
|--------|----------|-------|---------|
| `crm_server.py` | HubSpot | 8 | All stages |
| `cdp_server.py` | Segment | 8 | Awareness, Retention |
| `email_server.py` | Klaviyo | 8 | Consideration, Decision |
| `paid_media_server.py` | Google Ads | 8 | Awareness |
| `analytics_server.py` | Amplitude | 8 | All stages |
| `advocacy_server.py` | G2/Capterra | 8 | Advocacy |

See [guides/04_mcp_server_guide.md](guides/04_mcp_server_guide.md).

---

## Capstone Command Centre

The capstone orchestrates all 6 stages via a LangGraph graph with MCP connections:

```bash
cd capstone_command_centre
python orchestrator.py
```

All 6 stage agents run concurrently. A MarketingOpsDirector agent reviews any action above spend/bulk thresholds before execution. See the [capstone README](capstone_command_centre/README.md).

---

## Journey Simulator

Simulate a complete prospect journey from ad click to advocate:

```bash
# See the full walkthrough
cat guides/05_journey_simulator.md
```

This runs Alex Rivera (Acme Corp) through all 6 stages in under 10 minutes with mock data. See [guides/05_journey_simulator.md](guides/05_journey_simulator.md).

---

## MarTech Stack Setup

| Service | Free Tier | Guide |
|---------|-----------|-------|
| HubSpot | Developer sandbox | [guides/02_hubspot_setup.md](guides/02_hubspot_setup.md) |
| Klaviyo | Free ≤250 contacts | [guides/03_klaviyo_setup.md](guides/03_klaviyo_setup.md) |
| Segment | Free developer plan | See `.env.example` |
| Google Ads | Test account | See `.env.example` |

---

## Free Tier with Ollama

Run everything locally at zero API cost:

```bash
ollama pull llama3.1
# Set in .env:
# OPENAI_API_KEY=ollama
# OPENAI_BASE_URL=http://localhost:11434/v1
```

See [guides/01_free_tier_ollama.md](guides/01_free_tier_ollama.md).

---

## Author

**Pushparajan Ramar**
[github.com/Pushparajan/agenticai-marketing](https://github.com/Pushparajan/agenticai-marketing)

## License

MIT — See [LICENSE](LICENSE) for details.
