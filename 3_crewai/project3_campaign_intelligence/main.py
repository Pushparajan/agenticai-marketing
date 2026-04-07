# main.py
# Project 3: Campaign Intelligence Crew
# Chapter Reference: Chapter 3 - CrewAI
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
#
# Entry point for the Campaign Intelligence Crew.
# Accepts campaign parameters, kicks off the sequential crew pipeline,
# and saves deliverables to the output/ directory.

"""Campaign Intelligence Crew — entry point.

Usage:
    python main.py

    # Override defaults via environment variables:
    CAMPAIGN_INDUSTRY=ecommerce CAMPAIGN_AUDIENCE=enterprise_decision_makers python main.py

The crew executes three sequential tasks:
    1. Audience segment analysis  (-> output/campaign_brief.md context)
    2. Campaign brief creation    (-> output/campaign_brief.md)
    3. Campaign copy generation   (-> output/campaign_copy.md)
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger("campaign_intel.main")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
OUTPUT_DIR: Path = BASE_DIR / "output"


def ensure_output_dir() -> None:
    """Create the output directory if it does not exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Campaign parameters
# ---------------------------------------------------------------------------

def get_campaign_inputs() -> dict[str, str]:
    """Build the campaign input dictionary from env vars or defaults.

    Returns:
        Dictionary with keys expected by the task YAML templates:
        - industry
        - audience_name
        - channels
    """
    return {
        "industry": os.getenv("CAMPAIGN_INDUSTRY", "saas"),
        "audience_name": os.getenv("CAMPAIGN_AUDIENCE", "high_value_saas_buyers"),
        "channels": os.getenv("CAMPAIGN_CHANNELS", "email, linkedin, paid_search"),
    }


# ---------------------------------------------------------------------------
# Output persistence
# ---------------------------------------------------------------------------

def save_output(filename: str, content: str) -> Path:
    """Write content to a file in the output directory.

    Args:
        filename: Name of the file to create (e.g. "campaign_brief.md").
        content: The string content to write.

    Returns:
        Path to the written file.
    """
    ensure_output_dir()
    filepath = OUTPUT_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    logger.info("Saved output: %s (%d chars)", filepath, len(content))
    return filepath


def _build_brief_header(inputs: dict[str, str]) -> str:
    """Create a metadata header for the campaign brief file."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"---\n"
        f"generated: {ts}\n"
        f"industry: {inputs['industry']}\n"
        f"audience: {inputs['audience_name']}\n"
        f"channels: {inputs['channels']}\n"
        f"---\n\n"
    )


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def run() -> None:
    """Instantiate the Campaign Intelligence Crew, kick off execution,
    and persist all deliverables to the output/ directory.
    """
    # Lazy import so the module can be inspected without triggering
    # CrewAI initialisation (helpful for testing and documentation).
    from crew import CampaignIntelligenceCrew

    inputs = get_campaign_inputs()

    logger.info("=" * 60)
    logger.info("Campaign Intelligence Crew — Starting")
    logger.info("=" * 60)
    logger.info("Industry   : %s", inputs["industry"])
    logger.info("Audience   : %s", inputs["audience_name"])
    logger.info("Channels   : %s", inputs["channels"])
    logger.info("Output dir : %s", OUTPUT_DIR)
    logger.info("=" * 60)

    # Build and run the crew
    campaign_crew = CampaignIntelligenceCrew()
    result = campaign_crew.crew().kickoff(inputs=inputs)

    # ------------------------------------------------------------------
    # Persist deliverables
    # ------------------------------------------------------------------

    # The copy_task has output_file configured, so campaign_copy.md is
    # written automatically by CrewAI.  We also save the intermediate
    # brief and a combined output for convenience.

    header = _build_brief_header(inputs)

    # Extract individual task outputs when available
    task_outputs = getattr(result, "tasks_output", [])

    brief_content = ""
    copy_content = ""

    if len(task_outputs) >= 2:
        # task_outputs[0] = segment analysis, [1] = brief, [2] = copy
        segment_raw = str(task_outputs[0])
        brief_raw = str(task_outputs[1])
        brief_content = header + brief_raw

        if len(task_outputs) >= 3:
            copy_content = header + str(task_outputs[2])
    else:
        # Fallback: use the final crew output for both files
        final_output = str(result)
        brief_content = header + final_output
        copy_content = header + final_output

    # Save the campaign brief (segment analysis + strategy)
    brief_path = save_output("campaign_brief.md", brief_content)

    # Save the campaign copy (may also be written by CrewAI output_file)
    if copy_content:
        copy_path = save_output("campaign_copy.md", copy_content)
    else:
        copy_path = OUTPUT_DIR / "campaign_copy.md"

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Campaign Intelligence Crew — Complete")
    logger.info("=" * 60)
    logger.info("Campaign Brief : %s", brief_path)
    logger.info("Campaign Copy  : %s", copy_path)

    if hasattr(result, "token_usage"):
        usage = result.token_usage
        logger.info(
            "Token usage — prompt: %s  completion: %s  total: %s",
            getattr(usage, "prompt_tokens", "N/A"),
            getattr(usage, "completion_tokens", "N/A"),
            getattr(usage, "total_tokens", "N/A"),
        )

    logger.info("=" * 60)

    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user.")
        sys.exit(130)
    except Exception:
        logger.exception("Campaign Intelligence Crew failed with an error.")
        sys.exit(1)
