# Stage 3 — Decision

**Chapters 7-8 | Framework: LangGraph**

## Overview

Stage 3 of the customer journey focuses on the **Decision** phase — the critical
moment when prospects evaluate final options, raise objections, compare
competitors, and ultimately decide whether to purchase.

This stage implements an agentic AI graph using **LangGraph** that orchestrates
decision-stage marketing workflows: objection handling, competitive
battle-cards, close-offer generation, urgency reactivation for stalled deals,
and human-in-the-loop approval for high-value deals.

## Architecture

```
evaluate_decision_signals
            |
    route_decision_action (conditional)
       /    |     |      \         \
 close  objection  battlecard  urgency  nurture
 offer  response   dispatch    reactivate
       \    |     |      /         /
            v
      (human review gate for deals > $50k)
```

## Directory Layout

```
stage3_decision/
  graph/
    state.py           # DecisionJourneyState TypedDict
    nodes.py           # Async node functions
    routing.py         # Conditional edge logic
    graph.py           # StateGraph wiring + MemorySaver
  tools/
    objection_handler_tools.py
    competitive_battlecard_tools.py
    close_offer_tools.py
    deal_crm_tools.py
  project_conversion_graph/
    main.py            # Entry-point demo
    demo_runner.py     # 21-day simulation for 3 deal types
  notebooks/
    decision_graph_walkthrough.ipynb
```

## Quick Start

```bash
# Mock mode (no API keys needed)
USE_MOCK=true python -m stage3_decision.project_conversion_graph.main

# With real APIs
export OPENAI_API_KEY=sk-...
export HUBSPOT_ACCESS_TOKEN=pat-...
python -m stage3_decision.project_conversion_graph.main
```

## Deal Scenarios (demo_runner.py)

| # | Scenario         | Behaviour                                          |
|---|------------------|----------------------------------------------------|
| 1 | Clean close      | High intent, proposal viewed, straight to offer    |
| 2 | Competitive      | Competitor named, battlecard dispatched first       |
| 3 | Stalled          | Goes cold after 14 days, urgency reactivation      |

## Key Concepts

- **USE_MOCK pattern** — every tool checks `os.getenv("USE_MOCK", "true")`;
  set to `"false"` when real API credentials are available.
- **Human-in-the-loop** — deals above $50,000 pause at `pause_for_human_review`
  via LangGraph's `interrupt_before` mechanism.
- **MemorySaver** — graph state persists across invocations for multi-turn
  decision journeys.

## Author

Pushparajan Ramar
https://github.com/Pushparajan/agenticai-marketing
