# File      : crew.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Campaign Intelligence Crew — CrewAI Crew definition.

Uses the @CrewBase decorator pattern so that agents and tasks are loaded
from the YAML config files in ./config/.  Tools are assigned per agent
based on their research, strategy, or content-creation role.
"""

from __future__ import annotations

import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# ── Tool imports ────────────────────────────────────────────────────────
from stage2_consideration.tools.market_research_tools import (
    get_industry_benchmarks,
    get_tech_stack_signals,
    linkedin_company_lookup,
    web_search,
)
from stage2_consideration.tools.competitor_intel_tools import (
    get_competitor_positioning,
    search_competitor_campaigns,
)
from stage2_consideration.tools.segment_cdp_tools import (
    get_contact_journey_events,
    query_segment_cdp,
)
from stage2_consideration.tools.content_publisher_tools import (
    get_case_studies,
    get_content_library,
    publish_to_notion,
)


@CrewBase
class CampaignIntelligenceCrew:
    """A crew of three specialised agents that research a prospect company,
    design a multi-channel nurture strategy, and generate conversion copy.

    Config files:
        config/agents.yaml  — agent definitions
        config/tasks.yaml   — task definitions with context chaining
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ── Agents ──────────────────────────────────────────────────────────

    @agent
    def market_researcher(self) -> Agent:
        """Market Research Analyst — gathers firmographic, tech-stack,
        and competitive intelligence."""
        return Agent(
            config=self.agents_config["market_researcher"],
            tools=[
                web_search,
                linkedin_company_lookup,
                get_industry_benchmarks,
                get_tech_stack_signals,
            ],
            verbose=True,
        )

    @agent
    def nurture_strategist(self) -> Agent:
        """Nurture Strategy Architect — designs sequenced, multi-channel
        nurture programmes grounded in CDP data."""
        return Agent(
            config=self.agents_config["nurture_strategist"],
            tools=[
                query_segment_cdp,
                get_contact_journey_events,
                get_industry_benchmarks,
            ],
            verbose=True,
        )

    @agent
    def conversion_copywriter(self) -> Agent:
        """Conversion Copywriter — produces high-converting emails,
        LinkedIn messages, and webinar invitations."""
        return Agent(
            config=self.agents_config["conversion_copywriter"],
            tools=[
                get_content_library,
                get_case_studies,
                get_competitor_positioning,
                search_competitor_campaigns,
                publish_to_notion,
            ],
            verbose=True,
        )

    # ── Tasks ───────────────────────────────────────────────────────────

    @task
    def research_task(self) -> Task:
        """Deep research on the target company and industry."""
        return Task(
            config=self.tasks_config["research_task"],
        )

    @task
    def strategy_task(self) -> Task:
        """Design the multi-channel nurture strategy."""
        return Task(
            config=self.tasks_config["strategy_task"],
        )

    @task
    def copy_task(self) -> Task:
        """Generate conversion copy for every nurture touch."""
        return Task(
            config=self.tasks_config["copy_task"],
            output_file=str(
                Path(__file__).parent / "output" / "campaign_output.json"
            ),
        )

    # ── Crew assembly ───────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Assemble the Campaign Intelligence Crew with sequential
        processing so each agent builds on the previous one's output."""
        return Crew(
            agents=self.agents,   # populated by @CrewBase from @agent methods
            tasks=self.tasks,     # populated by @CrewBase from @task methods
            process=Process.sequential,
            verbose=True,
        )
