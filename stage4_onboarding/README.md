# Stage 4 -- Onboarding

**Book**: *Mastering Agentic AI for Customer Journey Marketing*
**Author**: Pushparajan Ramar
**Chapter**: 9
**Framework**: AutoGen (pyautogen >= 0.4)

---

## Overview

Stage 4 covers the **Onboarding** phase of the customer journey. An agentic
system analyses new customers within their first 30 days, identifies the
"aha" feature most likely to drive stickiness, evaluates adoption health and
support sentiment, and produces a structured onboarding action plan that is
dispatched to the Customer Success team.

---

## Architecture

```
                         +-------------------------+
  New Customer Signup -> | OnboardingTrigger       |
  (first 30 days)        | (UserProxyAgent)        |
                         +-------------------------+
                                    |
                    RoundRobinGroupChat (max 8 rounds)
                        /           |           \
                       v            v            v
          +------------------+ +------------------+ +----------------------+
          | ProductSpecialist| | CustomerSuccess  | | Onboarding           |
          |                  | | Agent            | | Coordinator          |
          | - usage heatmap  | | - adoption score | | - synthesise JSON    |
          | - feature compl. | | - support tickets| |   onboarding plan    |
          | - friction pts   | | - sentiment      | |                      |
          | -> aha feature   | | - TTV metrics    | | {aha_feature,        |
          +------------------+ | - checklist      | |  activation_sequence,|
                               | -> activation    | |  first_check_in_date,|
                               |    sequence      | |  risk_flags,         |
                               +------------------+ |  recommended_content,|
                                                     |  owner}             |
                                                     +----------------------+
                                                              |
                                              +---------------+---------------+
                                              |                               |
                                              v                               v
                                    Email to CS Team              HubSpot Task Created
```

---

## Trigger Events

| Event                     | Source            | Action                          |
|---------------------------|-------------------|---------------------------------|
| Customer signs up         | Product / CRM     | Start 30-day onboarding watch   |
| First-week usage data     | Analytics engine  | Trigger intelligence room       |
| Support ticket created    | Help-desk         | Feed into CS Agent analysis     |
| Milestone completed       | Product events    | Update checklist status         |
| Adoption score drops      | Scoring pipeline  | Re-trigger risk assessment      |

---

## Quick Start

```bash
# 1. Install dependencies
pip install pyautogen httpx pydantic rich

# 2. Set environment variables (optional -- mock mode is the default)
export USE_MOCK=true               # flip to "false" for real APIs
export OPENAI_API_KEY=sk-...       # required only when USE_MOCK=false

# 3. Run the onboarding intelligence room demo
python -m stage4_onboarding.project_onboarding_room.main
```

---

## Expected Outputs

When you run `main.py` with mock mode enabled you will see console output
similar to:

```
============================================================
  STAGE 4 — ONBOARDING INTELLIGENCE ROOM
  Framework: AutoGen (pyautogen >= 0.4)
  Mode: MOCK
============================================================

  Running in pure mock mode (no LLM calls).

============================================================
  Onboarding Intelligence Room — CUST-1001
  TechNova Solutions | SaaS / Technology
  Scenario: SMOOTH ONBOARDING
============================================================

  [ProductSpecialist] Aha feature identified: 'dashboard'
  [ProductSpecialist] Completion rate: 67%
  [ProductSpecialist] Friction points: 1

  [CustomerSuccessAgent] Adoption score: 0.72
  [CustomerSuccessAgent] Sentiment: positive
  [CustomerSuccessAgent] Open tickets: 0
  [CustomerSuccessAgent] Time-to-value: ahead_of_benchmark

  CUST-1001:
    Aha Feature     : dashboard
    Risk Flags      : 1
    Check-in Date   : 2026-04-12
    Owner           : James Lee (CS Associate)

============================================================
  Onboarding Intelligence Room — CUST-1002
  RetailEdge Inc. | Retail / E-commerce
  Scenario: STRUGGLING ONBOARDING
============================================================

  [ProductSpecialist] Aha feature identified: 'dashboard'
  [ProductSpecialist] Completion rate: 17%
  [ProductSpecialist] Friction points: 3

  [CustomerSuccessAgent] Adoption score: 0.18
  [CustomerSuccessAgent] Sentiment: negative
  [CustomerSuccessAgent] Open tickets: 2
  [CustomerSuccessAgent] Time-to-value: at_risk

  CUST-1002:
    Aha Feature     : dashboard
    Risk Flags      : 7
    Check-in Date   : 2026-04-08
    Owner           : Sarah Kim (Senior CS Manager)
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `agents/product_specialist.py` | Product Specialist -- aha feature identification |
| `agents/cs_agent.py` | Customer Success Agent -- activation sequence design |
| `agents/onboarding_coordinator.py` | Coordinator -- synthesises final JSON plan |
| `tools/product_usage_tools.py` | Usage heatmap, adoption score, feature completion, friction |
| `tools/onboarding_milestone_tools.py` | Checklist, milestone status, time-to-value |
| `tools/support_ticket_tools.py` | Tickets, task creation, sentiment scoring |
| `groupchats/onboarding_intelligence_room.py` | RoundRobinGroupChat orchestration |
| `project_onboarding_room/main.py` | Demo entry point (2 sample customers) |
| `notebooks/onboarding_room_walkthrough.ipynb` | Interactive walkthrough notebook |
