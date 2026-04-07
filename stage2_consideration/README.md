# Stage 2 — Consideration

**Book**: *Mastering Agentic AI for Customer Journey Marketing*
**Author**: Pushparajan Ramar
**Chapters**: 5–6
**Framework**: CrewAI

---

## Overview

Stage 2 covers the **Consideration** phase of the customer journey. A CrewAI
crew of specialised agents researches prospects, designs nurture strategies,
and generates personalised conversion copy — moving Marketing Qualified Leads
(MQLs) through the mid-funnel toward a buying decision.

---

## Architecture

```
                    ┌──────────────────────────┐
  MQL trigger ────▶ │ consideration_journey_flow│  (CrewAI Flow)
  (HubSpot)        │  @start  receive_mql      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Campaign Intelligence Crew│  (CrewAI Crew)
                    │                          │
                    │  ┌────────────────────┐  │
                    │  │ market_researcher   │  │  Step 1: Research
                    │  │ (web, LinkedIn,     │  │
                    │  │  benchmarks, tech)  │  │
                    │  └────────┬───────────┘  │
                    │           │               │
                    │  ┌────────▼───────────┐  │
                    │  │ nurture_strategist  │  │  Step 2: Strategy
                    │  │ (CDP, journey       │  │
                    │  │  events, segments)  │  │
                    │  └────────┬───────────┘  │
                    │           │               │
                    │  ┌────────▼───────────┐  │
                    │  │conversion_copywriter│  │  Step 3: Copy
                    │  │ (content library,   │  │
                    │  │  case studies,      │  │
                    │  │  competitor intel)  │  │
                    │  └────────────────────┘  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  Publish & Activate       │
                    │  • Klaviyo nurture flow   │
                    │  • HubSpot CRM update     │
                    │  • Notion content publish  │
                    └──────────────────────────┘
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install crewai pydantic pyyaml httpx python-dotenv rich

# 2. Set environment variables (optional — mock mode is the default)
export USE_MOCK=true               # flip to "false" for real APIs
export OPENAI_API_KEY=sk-...
export HUBSPOT_API_KEY=pat-...
export KLAVIYO_API_KEY=pk_...

# 3. Run the campaign intelligence crew
cd stage2_consideration/project_campaign_crew
python main.py

# 4. Or run the full consideration flow
python -m stage2_consideration.flows.consideration_journey_flow
```

---

## Expected Outputs

When you run `main.py` with mock mode enabled you will see console output
similar to:

```
[2026-04-07 10:00:00] === Campaign Intelligence Crew ===
[2026-04-07 10:00:00] Company: Acme Corp | Industry: B2B SaaS | Channels: email,linkedin,webinar
[2026-04-07 10:00:01] [market_researcher] Researching Acme Corp ...
[2026-04-07 10:00:02] [nurture_strategist] Building nurture strategy ...
[2026-04-07 10:00:03] [conversion_copywriter] Generating conversion copy ...
[2026-04-07 10:00:04] Results saved to output/campaign_output.json
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `crews/campaign_intelligence_crew/config/agents.yaml` | Agent definitions (role, goal, backstory) |
| `crews/campaign_intelligence_crew/config/tasks.yaml` | Task definitions with context chaining |
| `crews/campaign_intelligence_crew/crew.py` | CrewAI Crew wiring with @CrewBase |
| `crews/campaign_intelligence_crew/main.py` | Entry point with demo run |
| `flows/consideration_journey_flow.py` | CrewAI Flow for full consideration pipeline |
| `tools/market_research_tools.py` | Web search, LinkedIn, benchmarks, tech stack |
| `tools/competitor_intel_tools.py` | Competitor positioning and campaign search |
| `tools/segment_cdp_tools.py` | Segment CDP queries and journey events |
| `tools/content_publisher_tools.py` | Notion publish, content library, case studies |
| `project_campaign_crew/main.py` | Simplified entry point |
| `notebooks/consideration_crew_walkthrough.ipynb` | Interactive walkthrough |

---

## Mock Mode

All tools support a `USE_MOCK` environment variable (default: `true`). When
enabled, tools return realistic marketing data without calling external APIs.
This lets you explore the full crew pipeline at zero cost.

```bash
export USE_MOCK=true
python -m stage2_consideration.project_campaign_crew.main
```

---

## Key Metrics (Consideration Stage)

| Metric | Description |
|--------|-------------|
| Engagement rate | Email opens + clicks / total sends |
| Content touches | Number of distinct content pieces consumed |
| MQL-to-SQL velocity | Days from MQL to Sales Qualified Lead |
| Nurture sequence completion | % of contacts completing full sequence |
