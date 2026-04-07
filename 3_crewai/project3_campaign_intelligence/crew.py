# crew.py
# Project 3: Campaign Intelligence Crew
# Chapter Reference: Chapter 3 - CrewAI
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
#
# CrewAI Crew definition that wires agents, tasks, and tools into a
# sequential pipeline: Audience Intelligence -> Campaign Strategy -> Copy.

"""Campaign Intelligence Crew — CrewAI orchestration module.

Loads agent and task definitions from YAML configuration files,
assigns specialised tools to each agent, and assembles the crew
for sequential execution.

Pipeline:
    1. Audience Intelligence Analyst  -> segment_task
    2. Campaign Strategy Director     -> brief_task
    3. Conversion Copywriter          -> copy_task
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Tool imports
# ---------------------------------------------------------------------------
from tools.segment_cdp import query_segment_cdp
from tools.competitor_intel import search_competitor_campaigns
from tools.content_publisher import publish_to_notion

logger = logging.getLogger("campaign_intel.crew")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
CONFIG_DIR: Path = BASE_DIR / "config"
OUTPUT_DIR: Path = BASE_DIR / "output"


# ---------------------------------------------------------------------------
# Crew definition (decorator-based)
# ---------------------------------------------------------------------------

@CrewBase
class CampaignIntelligenceCrew:
    """Campaign Intelligence Crew — sequential multi-agent pipeline.

    Agents
    ------
    - audience_intelligence_analyst : Pulls and analyses CDP segment data.
    - campaign_strategy_director    : Creates a campaign brief from insights.
    - conversion_copywriter         : Produces channel-specific copy.

    Process
    -------
    Sequential — each task's output feeds into the next task as context.
    """

    agents_config: str = str(CONFIG_DIR / "agents.yaml")
    tasks_config: str = str(CONFIG_DIR / "tasks.yaml")

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    @agent
    def audience_intelligence_analyst(self) -> Agent:
        """Audience Intelligence Analyst — CDP data expert."""
        return Agent(
            config=self.agents_config["audience_intelligence_analyst"],
            tools=[query_segment_cdp],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def campaign_strategy_director(self) -> Agent:
        """Campaign Strategy Director — brief and positioning expert."""
        return Agent(
            config=self.agents_config["campaign_strategy_director"],
            tools=[search_competitor_campaigns],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def conversion_copywriter(self) -> Agent:
        """Conversion Copywriter — high-converting copy specialist."""
        return Agent(
            config=self.agents_config["conversion_copywriter"],
            tools=[publish_to_notion],
            verbose=True,
            allow_delegation=False,
        )

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task
    def segment_task(self) -> Task:
        """Analyse audience segments from the CDP."""
        return Task(
            config=self.tasks_config["segment_task"],
        )

    @task
    def brief_task(self) -> Task:
        """Create a campaign brief from segment insights."""
        return Task(
            config=self.tasks_config["brief_task"],
        )

    @task
    def copy_task(self) -> Task:
        """Generate campaign copy from the brief."""
        return Task(
            config=self.tasks_config["copy_task"],
            output_file=str(OUTPUT_DIR / "campaign_copy.md"),
        )

    # ------------------------------------------------------------------
    # Crew assembly
    # ------------------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """Assemble and return the Campaign Intelligence Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
