# File      : main.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Entry point for the Campaign Intelligence Crew.

Runs a demo campaign-intelligence workflow for a sample prospect company.
Results are saved to the output/ directory as JSON.

Usage:
    python -m stage2_consideration.crews.campaign_intelligence_crew.main

Environment variables (all optional with defaults):
    USE_MOCK        — "true" (default) for mock data, "false" for real APIs
    OPENAI_API_KEY  — required when USE_MOCK=false
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Ensure output directory exists ──────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run() -> None:
    """Execute the Campaign Intelligence Crew with demo inputs."""
    from stage2_consideration.crews.campaign_intelligence_crew.crew import (
        CampaignIntelligenceCrew,
    )

    # Demo inputs — override via environment variables if desired
    inputs = {
        "company": os.getenv("DEMO_COMPANY", "Acme Corp"),
        "industry": os.getenv("DEMO_INDUSTRY", "B2B SaaS"),
        "channels": os.getenv("DEMO_CHANNELS", "email,linkedin,webinar"),
    }

    print("=" * 60)
    print("  Campaign Intelligence Crew — Stage 2: Consideration")
    print("=" * 60)
    print(f"  Company  : {inputs['company']}")
    print(f"  Industry : {inputs['industry']}")
    print(f"  Channels : {inputs['channels']}")
    print(f"  Mock mode: {os.getenv('USE_MOCK', 'true')}")
    print(f"  Time     : {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Build and kick off the crew
    crew_instance = CampaignIntelligenceCrew()
    result = crew_instance.crew().kickoff(inputs=inputs)

    # ── Persist results ─────────────────────────────────────────────────
    output_path = OUTPUT_DIR / "campaign_output.json"
    try:
        # If CrewOutput has a .json attribute or similar, use it
        if hasattr(result, "raw"):
            raw = result.raw
        elif hasattr(result, "json_dict"):
            raw = result.json_dict
        else:
            raw = str(result)

        # Attempt to parse as JSON for pretty-printing
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                raw = parsed
            except json.JSONDecodeError:
                pass

        payload = {
            "metadata": {
                "stage": "2 — Consideration",
                "crew": "CampaignIntelligenceCrew",
                "inputs": inputs,
                "generated_at": datetime.now().isoformat(),
                "mock_mode": os.getenv("USE_MOCK", "true"),
            },
            "result": raw,
        }
        output_path.write_text(json.dumps(payload, indent=2, default=str))
        print(f"\nResults saved to {output_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"\nWarning: could not save results — {exc}")
        print("Raw result:")
        print(result)

    print("\nDone.")


if __name__ == "__main__":
    run()
