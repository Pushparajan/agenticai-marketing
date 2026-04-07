# main.py
# Project 4: Demand Gen Pipeline Crew
# Chapter Reference: Chapter 4 -- CrewAI Framework
# Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
# Description: Entry point -- instantiates and kicks off the Demand Gen crew via Flow

"""Demand Gen Pipeline -- CLI entry point.

Accepts demand generation parameters (target segment, budget, channels,
timeline), runs the full hierarchical crew via a CrewAI Flow, and prints
the execution audit trail when complete.

Usage:
    python main.py
    python main.py --segment "enterprise-decision-makers" --budget 75000
    python main.py --channels "email,google_ads,linkedin,content_syndication" --timeline "6 weeks"

Environment variables (see .env):
    USE_MOCK_APIS   - "true" to use mock tool responses (default: true)
    MANAGER_MODEL   - LLM for the hierarchical manager (default: gpt-4o)
    AGENT_MODEL     - LLM for worker agents (default: gpt-4o-mini)
    CREW_VERBOSE    - "true" for verbose agent logging (default: true)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("demand_gen.main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the demand gen pipeline.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace with segment, budget, channels, and timeline.
    """
    parser = argparse.ArgumentParser(
        description="Demand Gen Pipeline Crew -- run a full demand generation campaign",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--segment",
        type=str,
        default="high-intent-saas-buyers",
        help="Target audience segment name (default: high-intent-saas-buyers)",
    )
    parser.add_argument(
        "--budget",
        type=str,
        default="50000",
        help="Total campaign budget in USD (default: 50000)",
    )
    parser.add_argument(
        "--channels",
        type=str,
        default="email,google_ads,linkedin",
        help="Comma-separated channel list (default: email,google_ads,linkedin)",
    )
    parser.add_argument(
        "--timeline",
        type=str,
        default="4 weeks",
        help="Campaign execution timeline (default: 4 weeks)",
    )
    return parser.parse_args(argv)


def print_banner(args: argparse.Namespace) -> None:
    """Print a formatted startup banner showing configuration."""
    border = "=" * 64
    print(f"\n{border}")
    print("  Demand Gen Pipeline Crew")
    print("  Project 4 -- Mastering Agentic AI for Marketing Technology")
    print(border)
    print(f"  Segment   : {args.segment}")
    print(f"  Budget    : ${args.budget}")
    print(f"  Channels  : {args.channels}")
    print(f"  Timeline  : {args.timeline}")
    print(f"  Started at: {_ts()}")
    print(f"{border}\n")


def print_audit_trail(report: dict) -> None:
    """Print the full execution audit trail from the flow report.

    Args:
        report: Dict returned by DemandGenFlow.finalize_audit containing
                'audit_trail', 'total_events', and 'completed_at'.
    """
    border = "-" * 64
    print(f"\n{border}")
    print("  EXECUTION AUDIT TRAIL")
    print(border)

    trail = report.get("audit_trail", [])
    for entry in trail:
        ts = entry.get("timestamp", "")
        agent = entry.get("agent", "unknown")
        action = entry.get("action", "")
        detail = entry.get("detail", "")
        # Truncate detail for display
        detail_display = (detail[:80] + "...") if len(detail) > 80 else detail
        print(f"  [{ts}]  {agent:25s}  {action}")
        if detail_display:
            print(f"  {'':28s}  -> {detail_display}")

    print(border)
    print(f"  Total events : {report.get('total_events', len(trail))}")
    print(f"  Completed at : {report.get('completed_at', 'N/A')}")
    print(f"{border}\n")


def print_crew_output(report: dict) -> None:
    """Print the final crew output from the flow report.

    Args:
        report: Dict returned by DemandGenFlow.finalize_audit.
    """
    border = "=" * 64
    print(f"\n{border}")
    print("  CREW OUTPUT")
    print(border)

    output = report.get("crew_output", "")
    # Attempt to pretty-print if it looks like JSON
    try:
        parsed = json.loads(output)
        print(json.dumps(parsed, indent=2))
    except (json.JSONDecodeError, TypeError):
        print(output)

    print(f"{border}\n")


def run_pipeline(
    segment: str = "high-intent-saas-buyers",
    budget: str = "50000",
    channels: str = "email,google_ads,linkedin",
    timeline: str = "4 weeks",
) -> dict:
    """Run the Demand Gen Pipeline and return the flow report.

    This function is the primary programmatic entry point.  It constructs
    the DemandGenFlow, kicks it off, and returns the structured report
    including crew output and full audit trail.

    Args:
        segment: Target audience segment name.
        budget: Campaign budget string.
        channels: Comma-separated channel list.
        timeline: Campaign timeline description.

    Returns:
        Dict with keys: crew_output, audit_trail, total_events, completed_at.
    """
    from crew import DemandGenFlow

    logger.info(
        "run_pipeline | segment=%s | budget=%s | channels=%s | timeline=%s",
        segment, budget, channels, timeline,
    )

    flow = DemandGenFlow(
        segment_name=segment,
        budget=budget,
        channels=channels,
        timeline=timeline,
    )

    result = flow.kickoff()

    # The Flow's finalize_audit listener returns the report dict.
    # If the result is a dict (from finalize_audit), use it directly;
    # otherwise wrap the raw output.
    if isinstance(result, dict) and "audit_trail" in result:
        return result

    return {
        "crew_output": str(result),
        "audit_trail": flow.audit.entries,
        "total_events": len(flow.audit.entries),
        "completed_at": _ts(),
    }


def main() -> None:
    """CLI entry point: parse args, run pipeline, print results."""
    args = parse_args()
    print_banner(args)

    logger.info("Launching Demand Gen Pipeline Crew...")
    report = run_pipeline(
        segment=args.segment,
        budget=args.budget,
        channels=args.channels,
        timeline=args.timeline,
    )

    print_audit_trail(report)
    print_crew_output(report)

    logger.info("Pipeline finished successfully.")


if __name__ == "__main__":
    main()
