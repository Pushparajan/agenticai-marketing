# Environment Setup Guide

## Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Git

## Step 1: Clone the Repository

```bash
git clone https://github.com/Pushparajan/agenticai-marketing.git
cd agenticai-marketing
```

## Step 2: Install Dependencies

**With uv (recommended):**
```bash
uv sync
```

**With pip:**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys. At minimum, you need one LLM provider key (OpenAI, Anthropic, or Google). All MarTech integrations work in mock mode without real keys.

## Step 4: Verify Installation

```bash
python -c "import openai, anthropic, crewai, langgraph; print('All packages installed.')"
```

## Step 5: Run Your First Project

```bash
cd 2_openai_sdk/project1_journey_twin
python app.py
```

## Mock Mode

Set `USE_MOCK_APIS=true` in your `.env` to run all projects without external MarTech API keys. Mock mode returns realistic marketing data for learning and experimentation.
