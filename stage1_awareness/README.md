# Stage 1 -- Awareness

**Book**: *Mastering Agentic AI for Customer Journey Marketing*
**Author**: Pushparajan Ramar
**Chapters**: 3--4
**Framework**: OpenAI Agents SDK

---

## Overview

Stage 1 covers the **Awareness** phase of the customer journey. An agentic
system detects new visitors, scores their intent signals, and routes them
through a triage workflow that decides the optimal next action -- fast-track
demo booking, nurture-sequence enrolment, or cold-prospect logging.

---

## Architecture

```
                         +---------------------+
  Webhook / Ad Click --> | webhook_receiver.py |
                         +---------------------+
                                  |
                                  v
                         +---------------------+
                         |  discovery_agent.py  |
                         | (ICP match, enrich,  |
                         |  first-touch content)|
                         +---------------------+
                                  |
                                  v
                         +---------------------+
                         |   triage_agent.py    |
                         |  intent score router |
                         +---------------------+
                           /        |        \
                          /         |         \
                   score>80    40-79 score   score<40
                        /           |            \
                       v            v              v
          +----------------+ +-----------------+ +------------------+
          | high_intent_   | | nurture_        | | Log cold prospect|
          | accelerator.py | | enrolment_      | | 30-day re-eval   |
          |                | | agent.py        | +------------------+
          +----------------+ +-----------------+
          | demo booking   | | Klaviyo flow    |
          | priority task  | | selection       |
          | outreach email | | drip enrolment  |
          +----------------+ +-----------------+
```

---

## Trigger Events

| Event                  | Source           | Action                     |
|------------------------|------------------|----------------------------|
| `contact.created`      | HubSpot webhook  | Run discovery + triage     |
| `page_visit`           | HubSpot webhook  | Score intent, update CRM   |
| Ad click               | Google/Meta Ads  | Capture context, score     |
| G2 intent signal       | G2 / Bombora     | Boost intent score         |
| Content download       | Website / CMS    | Score + nurture enrol      |

---

## Quick Start

```bash
# 1. Install dependencies
pip install openai-agents fastapi uvicorn httpx pydantic

# 2. Set environment variables (optional -- mock mode is the default)
export USE_MOCK_APIS=true          # flip to "false" for real APIs
export OPENAI_API_KEY=sk-...
export HUBSPOT_API_KEY=pat-...

# 3. Run the demand-gen demo
python -m stage1_awareness.project_demand_gen.main

# 4. Launch the webhook receiver
uvicorn stage1_awareness.project_demand_gen.webhook_receiver:app --port 8000
```

---

## Expected Outputs

When you run `main.py` with mock mode enabled you will see console output
similar to:

```
[2026-04-07 10:00:00] Processing lead: alice@techcorp.com
[2026-04-07 10:00:00]   Intent score: 85 -> HIGH INTENT
[2026-04-07 10:00:01]   Demo booked, priority CRM task created
[2026-04-07 10:00:01] Processing lead: bob@startup.io
[2026-04-07 10:00:01]   Intent score: 55 -> NURTURE
[2026-04-07 10:00:02]   Enrolled in nurture flow: saas_eval_drip
[2026-04-07 10:00:02] Processing lead: charlie@bigco.org
[2026-04-07 10:00:02]   Intent score: 20 -> COLD
[2026-04-07 10:00:02]   Logged for 30-day re-evaluation on 2026-05-07
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `agents/discovery_agent.py` | ICP matching, enrichment, first-touch content |
| `agents/triage_agent.py` | Intent-score routing |
| `agents/high_intent_accelerator.py` | Fast-track high-intent leads |
| `agents/nurture_enrolment_agent.py` | Mid-intent nurture sequences |
| `tools/intent_scoring.py` | Weighted intent-signal scoring |
| `tools/crm_tools.py` | HubSpot CRM operations |
| `tools/web_search_tools.py` | Company / tech-stack enrichment |
| `tools/ad_platform_tools.py` | Ad click context, retargeting |
| `guardrails/brand_safety.py` | Content brand-safety validation |
| `project_demand_gen/main.py` | Demo entry point |
| `project_demand_gen/webhook_receiver.py` | FastAPI webhook listener |
| `notebooks/awareness_agent_walkthrough.ipynb` | Interactive walkthrough |
