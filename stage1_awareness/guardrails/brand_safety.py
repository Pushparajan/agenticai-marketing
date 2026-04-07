# File      : brand_safety.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Brand-safety guardrail.

Validates marketing content against brand guidelines before it is sent
to prospects. Checks for prohibited language, competitor mentions,
unsupported claims, and tone violations.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USE_MOCK = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Brand policy constants
# ---------------------------------------------------------------------------

PROHIBITED_TERMS: list[str] = [
    "guaranteed results",
    "100% guaranteed",
    "get rich",
    "risk-free",
    "no obligation",
    "act now",
    "limited time only",
    "once in a lifetime",
]

COMPETITOR_NAMES: list[str] = [
    "CompetitorA",
    "CompetitorB",
    "RivalCorp",
]

UNSUPPORTED_CLAIM_PATTERNS: list[str] = [
    r"\b\d+x\s+(faster|better|cheaper)\b",
    r"\b(#1|number one|best in class)\b",
    r"\brunmatched\b",
]

MAX_EXCLAMATION_MARKS: int = 2

# ---------------------------------------------------------------------------
# Rule checks
# ---------------------------------------------------------------------------


def _check_prohibited_terms(content: str) -> list[str]:
    """Flag any prohibited marketing terms."""
    lower = content.lower()
    return [
        f"Prohibited term found: '{term}'"
        for term in PROHIBITED_TERMS
        if term in lower
    ]


def _check_competitor_mentions(content: str) -> list[str]:
    """Flag direct competitor name mentions."""
    return [
        f"Competitor mention: '{name}'"
        for name in COMPETITOR_NAMES
        if name.lower() in content.lower()
    ]


def _check_unsupported_claims(content: str) -> list[str]:
    """Flag unsupported superlative or numeric claims."""
    issues: list[str] = []
    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            issues.append(f"Unsupported claim pattern: '{pattern}' matched")
    return issues


def _check_tone(content: str) -> list[str]:
    """Check for excessive punctuation or all-caps words."""
    issues: list[str] = []
    excl_count = content.count("!")
    if excl_count > MAX_EXCLAMATION_MARKS:
        issues.append(
            f"Excessive exclamation marks: {excl_count} "
            f"(max {MAX_EXCLAMATION_MARKS})"
        )
    caps_words = [w for w in content.split() if w.isupper() and len(w) > 3]
    if len(caps_words) > 2:
        issues.append(
            f"Too many ALL-CAPS words ({len(caps_words)}): "
            f"{', '.join(caps_words[:5])}"
        )
    return issues


# ---------------------------------------------------------------------------
# Real API check (OpenAI moderation endpoint)
# ---------------------------------------------------------------------------

def _check_moderation_real(content: str) -> list[str]:
    """Call OpenAI moderation API for content-policy violations."""
    import httpx

    api_key = os.getenv("OPENAI_API_KEY", "")
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/moderations",
            json={"input": content},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()["results"][0]
        if result.get("flagged"):
            flagged_cats = [
                cat for cat, val in result.get("categories", {}).items() if val
            ]
            return [f"OpenAI moderation flagged: {', '.join(flagged_cats)}"]
    except Exception as exc:
        logger.warning("OpenAI moderation API error: %s", exc)
    return []


def _check_moderation_mock(content: str) -> list[str]:
    """Mock moderation -- only flags obvious test phrases."""
    flagged = ["hate speech", "violence", "self-harm"]
    issues: list[str] = []
    lower = content.lower()
    for phrase in flagged:
        if phrase in lower:
            issues.append(f"Mock moderation flagged: '{phrase}'")
    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def brand_safety_check(content: str) -> dict[str, Any]:
    """Validate marketing content against brand-safety rules.

    Runs rule-based checks (prohibited terms, competitor mentions,
    unsupported claims, tone) and an optional AI moderation check.

    Args:
        content: The marketing copy to validate.

    Returns:
        Dict with:
            - ``passed`` (bool): True if no issues found.
            - ``issues`` (list[str]): List of human-readable issue descriptions.
    """
    logger.info("Running brand safety check (mock=%s, len=%d)", USE_MOCK, len(content))

    issues: list[str] = []
    issues.extend(_check_prohibited_terms(content))
    issues.extend(_check_competitor_mentions(content))
    issues.extend(_check_unsupported_claims(content))
    issues.extend(_check_tone(content))

    if USE_MOCK:
        issues.extend(_check_moderation_mock(content))
    else:
        issues.extend(_check_moderation_real(content))

    passed = len(issues) == 0

    if passed:
        logger.info("Brand safety check PASSED")
    else:
        logger.warning("Brand safety check FAILED with %d issues", len(issues))
        for issue in issues:
            logger.warning("  - %s", issue)

    return {"passed": passed, "issues": issues}
