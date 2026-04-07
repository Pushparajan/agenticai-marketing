# File      : intent_scoring.py
# Stage     : 1 — Awareness
# Chapter   : 3–4
# Framework : OpenAI Agents SDK
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing

"""
Intent-signal scoring engine.

Aggregates behavioural signals (page views, Segment events, G2 intent data)
into a single 0-100 intent score using a weighted model.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
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

# Weights for each signal type (max contribution shown in parentheses)
SIGNAL_WEIGHTS: dict[str, int] = {
    "pricing_page": 25,       # (25) Visited pricing page
    "demo_page": 20,          # (20) Visited demo / book-a-call page
    "content_download": 15,   # (15) Downloaded whitepaper / ebook
    "g2_research": 10,        # (10) G2 / Bombora intent signal
    "email_open": 5,          # (5)  Opened a marketing email
}

# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

_MOCK_SIGNALS: dict[str, dict[str, int]] = {
    "alice@techcorp.com": {
        "pricing_page": 3,
        "demo_page": 2,
        "content_download": 1,
        "g2_research": 1,
        "email_open": 4,
    },
    "bob@startup.io": {
        "pricing_page": 1,
        "demo_page": 0,
        "content_download": 2,
        "g2_research": 1,
        "email_open": 3,
    },
    "charlie@bigco.org": {
        "pricing_page": 0,
        "demo_page": 0,
        "content_download": 0,
        "g2_research": 0,
        "email_open": 2,
    },
}


# ---------------------------------------------------------------------------
# Helper — compute score from raw signal counts
# ---------------------------------------------------------------------------

def _compute_score(signals: dict[str, int]) -> int:
    """Return a 0-100 score by summing min(count, cap) * weight / cap."""
    total = 0.0
    for signal_name, weight in SIGNAL_WEIGHTS.items():
        count = signals.get(signal_name, 0)
        # Cap each signal contribution at its weight ceiling
        cap = 3 if signal_name != "email_open" else 5
        normalised = min(count / cap, 1.0)
        total += normalised * weight
    # Total maximum is sum of all weights = 75; scale to 0-100
    max_possible = sum(SIGNAL_WEIGHTS.values())
    return min(int(round((total / max_possible) * 100)), 100)


# ---------------------------------------------------------------------------
# Real API integration (Segment + G2/Bombora)
# ---------------------------------------------------------------------------

def _fetch_signals_real(contact_email: str) -> dict[str, int]:
    """Fetch behavioural signals from Segment and G2 APIs."""
    import httpx

    segment_token = os.getenv("SEGMENT_API_TOKEN", "")
    g2_api_key = os.getenv("G2_API_KEY", "")

    signals: dict[str, int] = {k: 0 for k in SIGNAL_WEIGHTS}

    # --- Segment profile traits / events ---
    try:
        resp = httpx.get(
            "https://profiles.segment.io/v1/namespaces/default/profiles",
            params={"email": contact_email, "limit": 50},
            headers={"Authorization": f"Bearer {segment_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        events = resp.json().get("data", [])
        for evt in events:
            etype = evt.get("event", "")
            if "pricing" in etype.lower():
                signals["pricing_page"] += 1
            elif "demo" in etype.lower():
                signals["demo_page"] += 1
            elif "download" in etype.lower():
                signals["content_download"] += 1
            elif "email" in etype.lower() and "open" in etype.lower():
                signals["email_open"] += 1
    except Exception as exc:
        logger.warning("Segment API error for %s: %s", contact_email, exc)

    # --- G2 / Bombora intent ---
    try:
        domain = contact_email.split("@")[1]
        resp = httpx.get(
            "https://intent.g2.com/api/v1/signals",
            params={"domain": domain},
            headers={"Authorization": f"Bearer {g2_api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        g2_data = resp.json()
        signals["g2_research"] = g2_data.get("signal_count", 0)
    except Exception as exc:
        logger.warning("G2 API error for %s: %s", contact_email, exc)

    return signals


def _fetch_signals_mock(contact_email: str) -> dict[str, int]:
    """Return deterministic mock signals for testing."""
    return _MOCK_SIGNALS.get(
        contact_email,
        {k: 0 for k in SIGNAL_WEIGHTS},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_intent_signals(contact_email: str) -> dict[str, Any]:
    """Score a contact's intent signals and return an IntentProfile dict.

    Args:
        contact_email: The email address of the contact to score.

    Returns:
        A dictionary with keys:
            - profile_id (str): Unique identifier for this scoring event.
            - email (str): The scored contact email.
            - signals (dict): Raw signal counts per channel.
            - score (int): Composite intent score 0-100.
            - tier (str): "high" | "mid" | "cold".
            - scored_at (str): ISO-8601 timestamp.
    """
    logger.info("Scoring intent signals for %s (mock=%s)", contact_email, USE_MOCK)

    if USE_MOCK:
        signals = _fetch_signals_mock(contact_email)
    else:
        signals = _fetch_signals_real(contact_email)

    score = _compute_score(signals)

    if score > 80:
        tier = "high"
    elif score >= 40:
        tier = "mid"
    else:
        tier = "cold"

    profile: dict[str, Any] = {
        "profile_id": str(uuid.uuid4()),
        "email": contact_email,
        "signals": signals,
        "score": score,
        "tier": tier,
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Intent score for %s: %d (%s)", contact_email, score, tier
    )
    return profile
