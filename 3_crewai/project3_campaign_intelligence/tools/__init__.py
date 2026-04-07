# tools/__init__.py
# Project 3: Campaign Intelligence Crew — Tool Package
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar

from tools.segment_cdp import query_segment_cdp
from tools.competitor_intel import search_competitor_campaigns
from tools.content_publisher import publish_to_notion

__all__ = [
    "query_segment_cdp",
    "search_competitor_campaigns",
    "publish_to_notion",
]
