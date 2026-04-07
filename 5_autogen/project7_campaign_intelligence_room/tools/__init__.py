# tools/__init__.py
# Project 7: Campaign Intelligence Room
# Chapter Reference: Chapter 5 - AutoGen
# Description: Tool package for campaign intelligence agents
# Author: Pushparajan Ramar

"""Campaign Intelligence Room tool package.

Exports all tool functions used by the four specialist agents:
- Market research tools  (MarketAnalyst, CompetitiveIntelAgent)
- Budget modelling tools (CampaignStrategist)
- Brand safety tools     (BrandSafetyReviewer)
"""

from tools.market_research import analyze_competitor, search_market_trends
from tools.budget_model import calculate_roi_projection, forecast_budget
from tools.brand_safety import check_brand_guidelines, review_compliance

__all__ = [
    "search_market_trends",
    "analyze_competitor",
    "forecast_budget",
    "calculate_roi_projection",
    "check_brand_guidelines",
    "review_compliance",
]
