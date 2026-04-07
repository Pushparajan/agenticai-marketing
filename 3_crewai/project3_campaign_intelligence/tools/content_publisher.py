# tools/content_publisher.py
# Project 3: Campaign Intelligence Crew
# Chapter Reference: Chapter 3 - CrewAI
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
#
# Notion content publisher tool — publishes campaign deliverables
# (briefs, copy decks) to a Notion workspace.
# Falls back to realistic mock data when USE_MOCK is enabled.

"""Notion content publisher tool with mock fallback.

Publishes structured campaign content to a Notion database page
using the Notion API.  When USE_MOCK is true (default) or the API
key is absent, returns a simulated success response with a mock
page URL for demonstration.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")

logger = logging.getLogger("campaign_intel.tools.content_publisher")


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _mock_page_id() -> str:
    """Generate a realistic Notion-style page ID."""
    return str(uuid.uuid4()).replace("-", "")


# ---------------------------------------------------------------------------
# CrewAI Tool
# ---------------------------------------------------------------------------

@tool("publish_to_notion")
def publish_to_notion(title: str, content: str) -> str:
    """Publish campaign content to a Notion workspace page.

    Creates a new page in the configured Notion database with the
    given title and Markdown content.  Useful for publishing campaign
    briefs, copy decks, and other deliverables to a shared workspace.

    Args:
        title: Title for the Notion page (e.g. "Q2 SaaS Campaign Brief").
        content: Markdown-formatted content to publish as the page body.

    Returns:
        JSON string with publication confirmation including page URL.
    """
    logger.info(
        "publish_to_notion called | title=%s | content_length=%d | mock=%s | ts=%s",
        title, len(content), USE_MOCK, _ts(),
    )

    # ---- Live Notion API path (when configured) ----
    if not USE_MOCK and NOTION_API_KEY and NOTION_DATABASE_ID:
        try:
            import requests

            # Convert Markdown content to Notion blocks (simplified)
            # In production, use a proper Markdown-to-Notion converter
            paragraphs = content.split("\n\n")
            children_blocks = []
            for para in paragraphs[:100]:  # Notion API limit per request
                para = para.strip()
                if not para:
                    continue
                if para.startswith("# "):
                    children_blocks.append({
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": para[2:]}}],
                        },
                    })
                elif para.startswith("## "):
                    children_blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": para[3:]}}],
                        },
                    })
                elif para.startswith("### "):
                    children_blocks.append({
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": para[4:]}}],
                        },
                    })
                else:
                    children_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": para[:2000]}}],
                        },
                    })

            resp = requests.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {NOTION_API_KEY}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28",
                },
                json={
                    "parent": {"database_id": NOTION_DATABASE_ID},
                    "properties": {
                        "title": {
                            "title": [{"text": {"content": title}}],
                        },
                    },
                    "children": children_blocks,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            page_id = data.get("id", _mock_page_id())
            page_url = data.get("url", f"https://notion.so/{page_id}")

            result = {
                "status": "published",
                "page_id": page_id,
                "page_url": page_url,
                "title": title,
                "content_length": len(content),
                "blocks_created": len(children_blocks),
                "published_at": _ts(),
            }
            logger.info("Notion page created: %s", page_url)
            return json.dumps(result, indent=2)
        except Exception as exc:
            logger.warning("Notion API error, falling back to mock: %s", exc)

    # ---- Mock fallback ----
    page_id = _mock_page_id()
    page_url = f"https://notion.so/workspace/Campaign-{page_id[:12]}"

    # Count content sections for realistic metadata
    lines = content.split("\n")
    heading_count = sum(1 for line in lines if line.strip().startswith("#"))
    word_count = len(content.split())

    result = {
        "status": "published",
        "page_id": page_id,
        "page_url": page_url,
        "title": title,
        "content_length": len(content),
        "word_count": word_count,
        "sections": heading_count,
        "database_id": NOTION_DATABASE_ID or "db_mock_campaign_assets",
        "published_at": _ts(),
        "source": "mock",
    }

    logger.info(
        "Returning mock Notion publish | page_id=%s | words=%d | sections=%d",
        page_id[:12], word_count, heading_count,
    )
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Notion Content Publisher Tool — Demo")
    print("=" * 60)

    sample_content = """# Q2 SaaS Campaign Brief

## Executive Summary
This campaign targets high-value SaaS buyers with a multi-channel
approach spanning email, LinkedIn, and paid search.

## Target Audience
- VP/Director-level marketing leaders
- Companies with 200-5000 employees
- SaaS, FinTech, and E-Commerce verticals

## Messaging Pillars
1. Data-driven decision making
2. Consolidate your martech stack
3. Prove marketing ROI to the C-suite

## Channel Strategy
- Email: 3-email nurture sequence
- LinkedIn: Sponsored content + lead gen forms
- Paid Search: Category and competitor keyword campaigns
"""

    result = publish_to_notion.run(
        title="Q2 SaaS Campaign Brief",
        content=sample_content,
    )
    parsed = json.loads(result)
    print(f"\n  Status: {parsed['status']}")
    print(f"  Page URL: {parsed['page_url']}")
    print(f"  Word count: {parsed['word_count']}")
    print(f"  Sections: {parsed['sections']}")
    print(f"  Published at: {parsed['published_at']}")
