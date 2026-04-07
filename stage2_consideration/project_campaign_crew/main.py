# File      : main.py
# Stage     : 2 — Consideration
# Chapter   : 5–6
# Framework : CrewAI
# Author    : Pushparajan Ramar
# Repo      : https://github.com/Pushparajan/agenticai-marketing
"""
Simplified entry point for the Campaign Intelligence Crew.

This is the recommended way to run the Stage 2 crew from the project root:

    cd stage2_consideration/project_campaign_crew
    python main.py

Or as a module from the repo root:

    python -m stage2_consideration.project_campaign_crew.main
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so relative imports resolve
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def main() -> None:
    """Delegate to the crew's own entry point."""
    from stage2_consideration.crews.campaign_intelligence_crew.main import run

    run()


if __name__ == "__main__":
    main()
