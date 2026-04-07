# crew.py
# Project 4: Demand Gen Pipeline Crew
# Chapter Reference: Chapter 4 -- CrewAI Framework
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
# Description: CrewAI Crew with hierarchical process, manager LLM, and Flow wrapper

"""Demand Gen Pipeline Crew -- orchestrates audience analysis, campaign
strategy, copy generation, and multi-platform activation.

Uses CrewAI's hierarchical process with a manager LLM that coordinates
task delegation.  A CrewAI Flow wraps the crew execution, providing
start/listen event hooks and a full audit trail with timestamps.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.flow.flow import Flow, listen, start
from dotenv import load_dotenv

from tools.hubspot_tools import (
    activate_hubspot_workflow,
    export_segment_cohort,
    score_audience_propensity,
)
from tools.klaviyo_tools import create_klaviyo_flow, set_google_ads_audience

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MANAGER_MODEL: str = os.getenv("MANAGER_MODEL", "gpt-4o")
AGENT_MODEL: str = os.getenv("AGENT_MODEL", "gpt-4o-mini")
VERBOSE: bool = os.getenv("CREW_VERBOSE", "true").lower() == "true"

logger = logging.getLogger("demand_gen.crew")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
_AGENTS_YAML = os.path.join(_CONFIG_DIR, "agents.yaml")
_TASKS_YAML = os.path.join(_CONFIG_DIR, "tasks.yaml")


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Audit trail helper
# ---------------------------------------------------------------------------

class AuditTrail:
    """In-memory audit trail that records timestamped events."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def log(self, agent: str, action: str, detail: str = "") -> None:
        """Append a timestamped event to the trail."""
        entry = {
            "timestamp": _ts(),
            "agent": agent,
            "action": action,
            "detail": detail[:500],
        }
        self.entries.append(entry)
        logger.info("AUDIT | agent=%s | action=%s | detail=%s", agent, action, detail[:120])

    def to_json(self, indent: int = 2) -> str:
        """Serialize the full trail as a JSON string."""
        return json.dumps(self.entries, indent=indent)

    def summary(self) -> str:
        """Return a human-readable summary of all events."""
        return "\n".join(
            f"[{e['timestamp']}]  {e['agent']:25s}  {e['action']}" for e in self.entries
        )


# ---------------------------------------------------------------------------
# Crew builder
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_agent(cfg: dict, tools: list, audit: AuditTrail, name: str) -> Agent:
    """Create an Agent from YAML config, assign tools, and log to audit."""
    agent = Agent(
        role=cfg["role"].strip(),
        goal=cfg["goal"].strip(),
        backstory=cfg["backstory"].strip(),
        tools=tools,
        llm=AGENT_MODEL,
        verbose=VERBOSE,
        allow_delegation=False,
    )
    audit.log(name, "agent_created", agent.role)
    return agent


def build_demand_gen_crew(
    segment_name: str,
    budget: str,
    channels: str,
    timeline: str,
    audit: AuditTrail | None = None,
) -> Crew:
    """Construct the Demand Gen Pipeline Crew from YAML config files.

    Args:
        segment_name: Target audience segment name.
        budget: Campaign budget string (e.g., '50000').
        channels: Comma-separated channel list.
        timeline: Campaign timeline (e.g., '4 weeks').
        audit: Optional AuditTrail instance for logging.

    Returns:
        A fully configured CrewAI Crew ready to kick off.
    """
    if audit is None:
        audit = AuditTrail()
    audit.log("system", "crew_build_start", f"segment={segment_name}")

    agents_cfg = _load_yaml(_AGENTS_YAML)
    tasks_cfg = _load_yaml(_TASKS_YAML)

    # ---- Build Agents ----
    segment_analyst = _build_agent(
        agents_cfg["segment_analyst"],
        [export_segment_cohort, score_audience_propensity],
        audit, "segment_analyst",
    )
    campaign_strategist = _build_agent(
        agents_cfg["campaign_strategist"], [], audit, "campaign_strategist",
    )
    copy_generator = _build_agent(
        agents_cfg["copy_generator"], [], audit, "copy_generator",
    )
    campaign_publisher = _build_agent(
        agents_cfg["campaign_publisher"],
        [activate_hubspot_workflow, create_klaviyo_flow, set_google_ads_audience],
        audit, "campaign_publisher",
    )

    # ---- Template interpolation ----
    tvars = {"segment_name": segment_name, "budget": budget,
             "channels": channels, "timeline": timeline}

    def _interp(text: str) -> str:
        result = text
        for k, v in tvars.items():
            result = result.replace("{" + k + "}", v)
        return result

    # ---- Build Tasks ----
    analyze_segments_task = Task(
        description=_interp(tasks_cfg["analyze_segments_task"]["description"]),
        expected_output=tasks_cfg["analyze_segments_task"]["expected_output"].strip(),
        agent=segment_analyst,
    )
    audit.log("segment_analyst", "task_created", "analyze_segments_task")

    design_campaign_task = Task(
        description=_interp(tasks_cfg["design_campaign_task"]["description"]),
        expected_output=tasks_cfg["design_campaign_task"]["expected_output"].strip(),
        agent=campaign_strategist,
        context=[analyze_segments_task],
    )
    audit.log("campaign_strategist", "task_created", "design_campaign_task")

    generate_copy_task = Task(
        description=_interp(tasks_cfg["generate_copy_task"]["description"]),
        expected_output=tasks_cfg["generate_copy_task"]["expected_output"].strip(),
        agent=copy_generator,
        context=[analyze_segments_task, design_campaign_task],
    )
    audit.log("copy_generator", "task_created", "generate_copy_task")

    publish_campaign_task = Task(
        description=_interp(tasks_cfg["publish_campaign_task"]["description"]),
        expected_output=tasks_cfg["publish_campaign_task"]["expected_output"].strip(),
        agent=campaign_publisher,
        context=[analyze_segments_task, design_campaign_task, generate_copy_task],
    )
    audit.log("campaign_publisher", "task_created", "publish_campaign_task")

    # ---- Assemble Crew (hierarchical with manager LLM) ----
    crew = Crew(
        agents=[segment_analyst, campaign_strategist, copy_generator, campaign_publisher],
        tasks=[analyze_segments_task, design_campaign_task,
               generate_copy_task, publish_campaign_task],
        process=Process.hierarchical,
        manager_llm=MANAGER_MODEL,
        verbose=VERBOSE,
    )
    audit.log("system", "crew_assembled", f"process=hierarchical manager={MANAGER_MODEL}")
    return crew


# ---------------------------------------------------------------------------
# CrewAI Flow
# ---------------------------------------------------------------------------

class DemandGenFlow(Flow):
    """CrewAI Flow wrapping the Demand Gen Pipeline Crew.

    Provides @start and @listen hooks for event-driven execution and
    maintains a complete audit trail of every agent action.
    """

    def __init__(
        self,
        segment_name: str = "high-intent-saas-buyers",
        budget: str = "50000",
        channels: str = "email,google_ads,linkedin",
        timeline: str = "4 weeks",
    ) -> None:
        super().__init__()
        self.segment_name = segment_name
        self.budget = budget
        self.channels = channels
        self.timeline = timeline
        self.audit = AuditTrail()

    @start()
    def run_demand_gen_pipeline(self) -> str:
        """Build and kick off the demand gen crew."""
        self.audit.log("flow", "pipeline_started", (
            f"segment={self.segment_name} budget={self.budget} "
            f"channels={self.channels} timeline={self.timeline}"
        ))
        crew = build_demand_gen_crew(
            segment_name=self.segment_name,
            budget=self.budget,
            channels=self.channels,
            timeline=self.timeline,
            audit=self.audit,
        )
        self.audit.log("flow", "crew_kickoff", "Starting hierarchical execution")
        result = crew.kickoff()
        self.audit.log("flow", "crew_completed", str(result)[:300])
        return str(result)

    @listen(run_demand_gen_pipeline)
    def finalize_audit(self, crew_output: str) -> dict[str, Any]:
        """Compile the final audit report after crew execution."""
        self.audit.log("flow", "finalize_started", "Compiling audit report")
        report: dict[str, Any] = {
            "crew_output": crew_output,
            "audit_trail": self.audit.entries,
            "total_events": len(self.audit.entries),
            "completed_at": _ts(),
        }
        self.audit.log("flow", "pipeline_finished", f"total_events={len(self.audit.entries)}")
        logger.info("Pipeline complete. Total audit events: %d", len(self.audit.entries))
        return report
