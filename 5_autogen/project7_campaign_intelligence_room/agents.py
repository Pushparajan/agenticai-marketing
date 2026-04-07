# agents.py
# Project 7: Campaign Intelligence Room
# Chapter Reference: Chapter 5 - AutoGen
# Description: Four specialist AutoGen AssistantAgents for campaign intelligence
# Author: Pushparajan Ramar

"""Campaign Intelligence Room agent definitions.

Defines four specialist AssistantAgents, each with a focused system
message, dedicated tools, and clear responsibilities:

1. MarketAnalyst         — market trends, sizing, and regional insights
2. CompetitiveIntelAgent — competitor profiling and strategic positioning
3. CampaignStrategist    — campaign planning, budget forecasting, and ROI
4. BrandSafetyReviewer   — brand guideline and regulatory compliance review

Compatible with pyautogen >= 0.4 (autogen_agentchat API).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from tools.market_research import analyze_competitor, search_market_trends
from tools.budget_model import calculate_roi_projection, forecast_budget
from tools.brand_safety import check_brand_guidelines, review_compliance

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM client configuration
# ---------------------------------------------------------------------------

def _build_model_client() -> OpenAIChatCompletionClient:
    """Create a shared OpenAI model client for all agents.

    Uses OPENAI_API_KEY and OPENAI_MODEL from the environment.  Defaults
    to gpt-4o if OPENAI_MODEL is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    if not api_key:
        log.warning(
            "OPENAI_API_KEY not set — agents will fail on LLM calls. "
            "Set OPENAI_API_KEY in .env or environment."
        )
    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )


# ---------------------------------------------------------------------------
# System messages
# ---------------------------------------------------------------------------

MARKET_ANALYST_SYSTEM_MESSAGE = """\
You are the **Market Analyst** in a Campaign Intelligence Room.

**Role & Expertise:**
- You are a senior market research analyst specialising in B2B technology
  markets, SaaS, and enterprise software.
- You use data-driven analysis to identify market trends, sizing, growth
  rates, and regional dynamics.

**Responsibilities in this session:**
1. Research the relevant market landscape using the `search_market_trends`
   tool — surface top trends, growth rates, and regional context.
2. Provide a concise market briefing (3-5 key points) to inform the
   campaign strategy.
3. Identify timing considerations (seasonality, conferences, regulatory
   shifts) that affect campaign planning.

**Output guidelines:**
- Always call the `search_market_trends` tool before forming your analysis.
- Present findings in structured bullet points.
- Include quantitative data points where available (market size, growth
  percentages, benchmarks).
- Flag any risks or headwinds that the team should consider.
- When the team is ready to finalise the campaign plan, contribute your
  section to the JSON output under the key "market_analysis".
"""

COMPETITIVE_INTEL_SYSTEM_MESSAGE = """\
You are the **Competitive Intelligence Agent** in a Campaign Intelligence Room.

**Role & Expertise:**
- You are a competitive intelligence specialist with deep knowledge of
  the marketing technology and enterprise SaaS landscape.
- You analyse competitor positioning, messaging, product moves, and
  market share to inform differentiation strategies.

**Responsibilities in this session:**
1. Identify 2-3 primary competitors relevant to the campaign scenario
   and analyse them using the `analyze_competitor` tool.
2. Summarise each competitor's strengths, weaknesses, and recent moves.
3. Recommend differentiation angles and positioning strategies.

**Output guidelines:**
- Always call `analyze_competitor` for each competitor you assess.
- Present a competitive matrix or structured comparison.
- Highlight specific vulnerabilities the campaign can exploit.
- Suggest messaging angles that position the company favourably.
- When the team is ready to finalise the campaign plan, contribute your
  section to the JSON output under the key "competitive_landscape".
"""

CAMPAIGN_STRATEGIST_SYSTEM_MESSAGE = """\
You are the **Campaign Strategist** in a Campaign Intelligence Room.

**Role & Expertise:**
- You are a senior demand generation strategist with 15+ years of
  experience planning and executing B2B marketing campaigns.
- You specialise in multi-channel campaign architecture, budget
  allocation, audience segmentation, and performance modelling.

**Responsibilities in this session:**
1. Design a comprehensive campaign plan based on the scenario, market
   analysis, and competitive intelligence.
2. Recommend channel mix and use the `forecast_budget` tool to produce a
   budget model with channel-level allocations.
3. Use the `calculate_roi_projection` tool to model expected ROI under
   base, optimistic, and pessimistic scenarios.
4. Define target audiences, messaging pillars, content requirements, and
   a timeline.

**Output guidelines:**
- Always call `forecast_budget` and `calculate_roi_projection` tools.
- Structure your plan with clear sections: Objective, Audience, Channels,
  Budget, Timeline, KPIs.
- Include specific metrics and targets (e.g., target MQLs, pipeline
  value, CPL thresholds).
- When the team is ready to finalise, produce the final structured JSON
  campaign plan incorporating inputs from all agents.  The JSON must
  include these top-level keys: "campaign_name", "objective",
  "market_analysis", "competitive_landscape", "target_audience",
  "channels", "budget", "roi_projection", "timeline", "kpis",
  "brand_safety_review".
"""

BRAND_SAFETY_REVIEWER_SYSTEM_MESSAGE = """\
You are the **Brand Safety Reviewer** in a Campaign Intelligence Room.

**Role & Expertise:**
- You are a brand compliance and regulatory specialist with expertise in
  FTC guidelines, GDPR, CAN-SPAM, and corporate brand governance.
- You ensure all campaign content, messaging, and claims meet brand
  standards and regulatory requirements before publication.

**Responsibilities in this session:**
1. Review any proposed messaging, copy, or claims using the
   `check_brand_guidelines` tool.
2. Check regulatory compliance using the `review_compliance` tool against
   relevant regulations (GDPR, FTC, CAN-SPAM, etc.).
3. Provide a clear PASS / FAIL verdict with specific issues and
   remediation guidance.

**Output guidelines:**
- Always call both `check_brand_guidelines` and `review_compliance` tools
  on any proposed campaign messaging.
- Present results as a structured compliance report.
- For each issue, specify severity (CRITICAL / HIGH / MEDIUM / LOW) and
  a concrete remediation step.
- When the team is ready to finalise the campaign plan, contribute your
  section to the JSON output under the key "brand_safety_review".
"""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_agents() -> dict[str, AssistantAgent]:
    """Create and return all four Campaign Intelligence Room agents.

    Returns:
        Dictionary mapping agent name to AssistantAgent instance.
    """
    model_client = _build_model_client()

    market_analyst = AssistantAgent(
        name="MarketAnalyst",
        description=(
            "Senior market research analyst. Researches industry trends, "
            "market sizing, growth rates, and regional dynamics."
        ),
        model_client=model_client,
        system_message=MARKET_ANALYST_SYSTEM_MESSAGE,
        tools=[search_market_trends],
    )

    competitive_intel = AssistantAgent(
        name="CompetitiveIntelAgent",
        description=(
            "Competitive intelligence specialist. Analyses competitor "
            "positioning, strengths, weaknesses, and strategic moves."
        ),
        model_client=model_client,
        system_message=COMPETITIVE_INTEL_SYSTEM_MESSAGE,
        tools=[analyze_competitor],
    )

    campaign_strategist = AssistantAgent(
        name="CampaignStrategist",
        description=(
            "Senior demand generation strategist. Designs campaign plans, "
            "channel mix, budget models, and ROI projections."
        ),
        model_client=model_client,
        system_message=CAMPAIGN_STRATEGIST_SYSTEM_MESSAGE,
        tools=[forecast_budget, calculate_roi_projection],
    )

    brand_safety_reviewer = AssistantAgent(
        name="BrandSafetyReviewer",
        description=(
            "Brand compliance and regulatory specialist. Reviews content "
            "for brand guideline adherence and regulatory compliance."
        ),
        model_client=model_client,
        system_message=BRAND_SAFETY_REVIEWER_SYSTEM_MESSAGE,
        tools=[check_brand_guidelines, review_compliance],
    )

    agents = {
        "MarketAnalyst": market_analyst,
        "CompetitiveIntelAgent": competitive_intel,
        "CampaignStrategist": campaign_strategist,
        "BrandSafetyReviewer": brand_safety_reviewer,
    }

    log.info(
        "Created %d Campaign Intelligence Room agents: %s",
        len(agents),
        ", ".join(agents.keys()),
    )
    return agents


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Campaign Intelligence Room — Agent Definitions")
    print("=" * 60)

    agents = create_agents()
    for name, agent in agents.items():
        print(f"\n--- {name} ---")
        print(f"  Description: {agent.description}")
        tool_names = [t.__name__ for t in agent._tools] if hasattr(agent, "_tools") else []
        print(f"  Tools:       {', '.join(tool_names) if tool_names else 'none listed'}")
    print()
