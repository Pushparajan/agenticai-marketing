# Journey Simulator — Full End-to-End Walkthrough

Simulate one prospect travelling through all 6 customer journey stages using mock data. Runs in under 10 minutes with `USE_MOCK_APIS=true`.

## Prospect Profile

- **Name:** Alex Rivera
- **Company:** Acme Corp (180 employees, B2B SaaS, Series B)
- **Industry:** Revenue Intelligence
- **Entry point:** Google Ads click on "revenue forecasting for SaaS"

## Prerequisites

```bash
cd agenticai-marketing
export USE_MOCK_APIS=true
```

## Stage 1 — Awareness (Day 0)

**Trigger:** Ad click → HubSpot contact created

```bash
cd stage1_awareness/project_demand_gen
python main.py
```

**Expected output:**
- Intent score: 42 (mid-range — pricing page not yet visited)
- Triage decision: Enrol in nurture sequence
- CRM contact created with `lifecyclestage=subscriber`
- Nurture flow: 4-touch educational sequence selected

## Stage 2 — Consideration (Day 3)

**Trigger:** Downloads comparison guide → intent rises to 61 → lifecycle → MQL

```bash
cd ../../stage2_consideration/project_campaign_crew
python main.py
```

**Expected output:**
- Market research brief: competitive landscape in Revenue Intelligence
- Nurture strategy: 4-touch personalised sequence
- Copy generated: emails tailored to Acme Corp's pain points
- Published to Klaviyo flow + HubSpot updated

## Stage 3 — Decision (Day 10–18)

**Trigger:** Demo completed, pricing page viewed 3×

```bash
cd ../../stage3_decision/project_conversion_graph
python main.py
```

**Expected output:**
- Day 10: Intent score 82, deal created
- Day 15: Competitor "Clari" named → battlecard dispatched
- Day 18: Proposal viewed → close offer generated
- HITL approval requested (deal value > £50k threshold)

## Stage 4 — Onboarding (Day 20–32)

**Trigger:** Deal closed-won

```bash
cd ../../stage4_onboarding/project_onboarding_room
python main.py
```

**Expected output:**
- Onboarding plan: 30-day activation timeline
- Aha feature identified: "Pipeline Forecasting Dashboard"
- Milestones: data connection (Day 2), first report (Day 5), team invite (Day 10)
- Risk flags: none (smooth onboarding path)

## Stage 5 — Retention (Day 32+)

**Trigger:** Feature adoption at 78%, NPS submitted

```bash
cd ../../stage5_retention/project_retention_room
python main.py
```

**Expected output:**
- Churn risk: LOW (score 15/100)
- NPS: 9 (Promoter)
- No intervention needed — flagged for advocacy

## Stage 6 — Advocacy (Day 32+)

**Trigger:** NPS >= 9, high LTV, active user

```bash
cd ../../stage6_advocacy/project_advocacy_agent
python main.py
```

**Expected output:**
- Advocate identified: Alex Rivera (NPS 9, LTV above tier threshold)
- Actions triggered:
  - G2 review request sent (personalised note)
  - Referral programme invitation
  - Case study participation request
- Cooldown check passed (no recent review requests)

## Capstone — Full Orchestration

Run all stages through the command centre:

```bash
cd ../../capstone_command_centre
python orchestrator.py
```

**Expected output:**
- All 6 stage agents execute concurrently
- MarketingOpsDirector reviews 3 spend-impacting actions
- Final execution report with per-stage summaries

## CRM State Changes (Cumulative)

| Day | Event | Lifecycle Stage | Intent Score |
|-----|-------|----------------|--------------|
| 0 | Ad click | subscriber | 42 |
| 3 | Content download | lead | 61 |
| 8 | Webinar attend | MQL | 74 |
| 10 | Demo + pricing | SQL | 82 |
| 18 | Proposal viewed | opportunity | 92 |
| 20 | Deal closed | customer | — |
| 32 | NPS 9 | evangelist | — |

## Total Time

With `USE_MOCK_APIS=true`, the full simulation completes in approximately 2–5 minutes depending on your machine.
