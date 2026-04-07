# tools/__init__.py
# Project 4: Demand Gen Pipeline Crew
# Re-exports all CrewAI tool functions for convenient imports.

from .hubspot_tools import (
    activate_hubspot_workflow,
    export_segment_cohort,
    score_audience_propensity,
)
from .klaviyo_tools import create_klaviyo_flow, set_google_ads_audience

__all__ = [
    "export_segment_cohort",
    "score_audience_propensity",
    "activate_hubspot_workflow",
    "create_klaviyo_flow",
    "set_google_ads_audience",
]
