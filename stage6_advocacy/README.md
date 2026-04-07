# Stage 6 — Advocacy

**Chapter 12 · Framework: MCP + OpenAI Agents SDK**

Turn satisfied customers into active advocates — case-study participants,
referral partners, community moderators, and public reviewers.

## Architecture

```
project_advocacy_agent/main.py          ← entry point (3 demo customers)
agents/advocacy_activation_agent.py     ← OpenAI Agents SDK agent (gpt-4.1)
tools/
  nps_tools.py                          ← NPS score, distribution, follow-up
  review_request_tools.py               ← G2 / Capterra review requests + cooldown
  referral_programme_tools.py           ← Referral enrolment, links, pipeline
  community_invite_tools.py             ← Community invites, case-study asks
notebooks/
  advocacy_agent_walkthrough.ipynb      ← Step-by-step Jupyter walkthrough
```

## Scoring Framework

| Condition | Action |
|---|---|
| NPS ≥ 9 **and** LTV > $50 000 | Case-study participation request |
| NPS ≥ 8 **and** recent expansion | Referral programme enrolment |
| NPS ≥ 7 **and** active community | Community moderator invite |
| Any satisfied customer (NPS ≥ 7) | G2 review request (throttled, 90-day cooldown) |

## Quick Start

```bash
# Local demo (no API keys needed)
export USE_MOCK_APIS=true
python -m stage6_advocacy.project_advocacy_agent.main

# Full agent demo (requires OpenAI key)
export OPENAI_API_KEY=sk-...
python -m stage6_advocacy.project_advocacy_agent.main --agent
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `USE_MOCK_APIS` | No | `true` (default) for mock data |
| `OPENAI_API_KEY` | For agent mode | OpenAI API key for gpt-4.1 |
| `NPS_API_URL` | For real APIs | Delighted / Qualtrics endpoint |
| `NPS_API_KEY` | For real APIs | Survey platform API key |
| `G2_API_KEY` | For real APIs | G2 review platform token |
| `CRM_API_URL` | For real APIs | HubSpot / Salesforce CRM URL |
| `CRM_API_KEY` | For real APIs | CRM API key |
| `REFERRAL_API_URL` | For real APIs | Referral platform endpoint |
| `REFERRAL_API_KEY` | For real APIs | Referral platform key |
| `SLACK_BOT_TOKEN` | For real APIs | Slack bot token for invites |
| `REVIEW_COOLDOWN_DAYS` | No | Days between review asks (default 90) |

## Author

Pushparajan Ramar — *Mastering Agentic AI for Customer Journey Marketing*
