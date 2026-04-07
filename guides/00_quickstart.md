# Quick Start Guide

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

## Setup

```bash
git clone https://github.com/Pushparajan/agenticai-marketing.git
cd agenticai-marketing
uv sync                    # or: pip install -r requirements.txt
cp .env.example .env       # Edit .env or leave USE_MOCK_APIS=true
```

## Run Your First Stage

```bash
cd stage1_awareness/project_demand_gen
python main.py
```

This runs the Awareness stage agents in mock mode — scoring intent signals, triaging leads, and routing to accelerator or nurture paths.

## Run Each Stage

```bash
# Stage 1 — Awareness
cd stage1_awareness/project_demand_gen && python main.py

# Stage 2 — Consideration
cd stage2_consideration/project_campaign_crew && python main.py

# Stage 3 — Decision
cd stage3_decision/project_conversion_graph && python main.py

# Stage 4 — Onboarding
cd stage4_onboarding/project_onboarding_room && python main.py

# Stage 5 — Retention
cd stage5_retention/project_retention_room && python main.py

# Stage 6 — Advocacy
cd stage6_advocacy/project_advocacy_agent && python main.py

# Capstone — Full Journey
cd capstone_command_centre && python orchestrator.py
```

## Mock Mode

All projects run without external API keys when `USE_MOCK_APIS=true` (the default). Every tool returns realistic marketing data for learning.

## Verify Installation

```bash
python -c "import openai, anthropic, crewai, langgraph; print('All packages installed.')"
```
