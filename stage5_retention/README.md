# Stage 5 — Retention (AutoGen + MCP)

**Chapters 10–11** of *Mastering Agentic AI for Customer Journey Marketing*
by Pushparajan Ramar.

## Overview

The Retention Intelligence Room is a multi-agent system that detects at-risk
customers, diagnoses churn drivers, and orchestrates personalised retention
interventions. It uses Microsoft AutoGen (pyautogen >= 0.4) with the Model
Context Protocol (MCP) pattern.

## Trigger Conditions

The room activates when **any one** of these conditions fires:

| # | Trigger | Condition |
|---|---------|-----------|
| 1 | **Usage decline** | 30-day active features < 50 % of baseline |
| 2 | **NPS drop** | NPS score falls below 7 |
| 3 | **Negative tickets** | 3 consecutive negative support tickets |
| 4 | **Renewal at risk** | Renewal < 60 days with no expansion discussion |
| 5 | **Competitor mentioned** | Competitor referenced in NPS verbatim or tickets |

## Agents

| Agent | Role | Key Tools |
|-------|------|-----------|
| **Churn_Risk_Analyst** | Classifies risk (low/medium/high/critical) and identifies primary driver | `get_churn_risk_score`, `predict_churn_probability`, `get_nps_score`, `get_sentiment_trend`, `get_support_ticket_sentiment` |
| **Retention_Strategist** | Selects intervention and builds win-back sequence | `get_successful_retention_plays`, `get_similar_churned_customers`, `generate_win_back_sequence`, `get_competitive_counter_offer` |
| **Commercial_Agent** | Calculates retention offers and expansion opportunities | `get_contract_details`, `calculate_retention_offer`, `get_expansion_opportunities` |

## Churn Drivers

- `usage_gap` — Feature adoption dropped significantly
- `value_gap` — Customer does not see expected ROI
- `price` — Pricing objection
- `competitor` — Actively evaluating alternatives
- `support` — Repeated negative support experiences
- `relationship` — Engagement or CSM relationship breakdown

## Interventions

- `executive_outreach` — VP/C-level engagement
- `product_training` — Guided onboarding and feature workshops
- `commercial_offer` — Discount, credit, or contract incentive
- `competitive_repositioning` — Battle-card driven counter-strategy
- `success_story_sharing` — Peer case studies and ROI evidence

## Directory Structure

```
stage5_retention/
├── README.md
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── churn_analyst.py
│   ├── retention_strategist.py
│   └── commercial_agent.py
├── groupchats/
│   ├── __init__.py
│   └── retention_intelligence_room.py
├── tools/
│   ├── __init__.py
│   ├── churn_risk_tools.py
│   ├── nps_sentiment_tools.py
│   ├── expansion_revenue_tools.py
│   └── win_back_tools.py
├── project_retention_room/
│   ├── __init__.py
│   └── main.py
└── notebooks/
    └── retention_room_walkthrough.ipynb
```

## Quick Start

```bash
# 1. Install dependencies
pip install "pyautogen>=0.4" autogen-agentchat autogen-ext openai httpx

# 2. Set environment variables
export USE_MOCK_APIS=true        # Use mock data (no real APIs needed)
export OPENAI_API_KEY=sk-...     # Required for full room execution

# 3. Run trigger evaluation only (no LLM needed)
cd stage5_retention/project_retention_room
python main.py --triggers-only

# 4. Run full room with all three scenarios
python main.py

# 5. Run a single scenario
python main.py --scenario 1      # Usage decline
python main.py --scenario 2      # Competitor threat
python main.py --scenario 3      # Renewal at risk
```

## Demo Scenarios

| # | Scenario | Customer | Risk Level | Primary Driver |
|---|----------|----------|------------|----------------|
| 1 | Usage Decline | CUST-001 (TechCorp) | Critical | usage_gap |
| 2 | Competitor Threat | CUST-002 (FinServ Global) | High | competitor |
| 3 | Renewal at Risk | CUST-003 (RetailMax) | Medium | value_gap |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_MOCK_APIS` | Use mock data instead of real APIs | `true` |
| `OPENAI_API_KEY` | OpenAI API key for LLM agents | — |
| `OPENAI_MODEL` | Model name | `gpt-4o` |
| `CHURN_API_URL` | Internal churn prediction API | — |
| `NPS_API_URL` | NPS survey platform API | — |
| `CRM_API_URL` | CRM/billing system API | — |
| `HELPDESK_API_URL` | Helpdesk/Zendesk API | — |
| `PRICING_API_URL` | Internal pricing engine API | — |

## Output Format

The room produces an `intervention_plan` JSON:

```json
{
  "customer_id": "CUST-001",
  "risk_level": "critical",
  "primary_driver": "usage_gap",
  "triggers_fired": ["usage_decline_below_50pct_baseline", "nps_below_7"],
  "primary_intervention": "executive_outreach",
  "secondary_intervention": "product_training",
  "retention_offer": {
    "max_discount_authorised": "25%",
    "contract_extension_incentive": "2 months free on 24-month renewal",
    "expansion_credit_offer": 15000
  },
  "win_back_sequence": { "...": "..." },
  "estimated_save_probability": 0.62,
  "urgency": "immediate"
}
```
