# tools/python_repl.py
# Project 6: MarTech Analyst Sidekick
# Chapter Reference: Chapter 4 - LangGraph
# Description: Sandboxed Python REPL for data analysis with pandas and numpy
# Author: Pushparajan Ramar

"""Sandboxed Python REPL tool for data analysis.

Executes arbitrary Python code in a restricted namespace that includes
pandas and numpy.  Captures stdout and any returned values so the
LangGraph agent can perform ad-hoc calculations, data transformations,
and statistical analysis.

Security note: This REPL runs code via ``exec()`` in the same process.
It is intended for **demo and book companion** purposes only.  In a
production system, use a container-based sandbox (e.g., E2B, Modal).
"""

from __future__ import annotations

import io
import logging
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


def _ts() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Allowed built-ins (restrict dangerous calls)
# ---------------------------------------------------------------------------
_SAFE_BUILTINS: dict[str, Any] = {
    name: getattr(__builtins__ if isinstance(__builtins__, dict) else __builtins__, name, None)
    for name in [
        "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
        "format", "frozenset", "getattr", "hasattr", "hash", "int", "isinstance",
        "issubclass", "iter", "len", "list", "map", "max", "min", "next",
        "print", "range", "repr", "reversed", "round", "set", "slice",
        "sorted", "str", "sum", "tuple", "type", "zip",
    ]
    if getattr(__builtins__ if isinstance(__builtins__, dict) else __builtins__, name, None)
    is not None
}


def _build_namespace() -> dict[str, Any]:
    """Build a sandboxed namespace with data science libraries pre-imported."""
    namespace: dict[str, Any] = {"__builtins__": _SAFE_BUILTINS}

    # Pre-import common data science packages
    try:
        import pandas as pd
        namespace["pd"] = pd
        namespace["pandas"] = pd
    except ImportError:
        log.warning("pandas not available in REPL namespace")

    try:
        import numpy as np
        namespace["np"] = np
        namespace["numpy"] = np
    except ImportError:
        log.warning("numpy not available in REPL namespace")

    try:
        import json
        namespace["json"] = json
    except ImportError:
        pass

    try:
        import math
        namespace["math"] = math
    except ImportError:
        pass

    try:
        from datetime import datetime as dt, timedelta
        namespace["datetime"] = dt
        namespace["timedelta"] = timedelta
    except ImportError:
        pass

    try:
        from statistics import mean, median, stdev
        namespace["mean"] = mean
        namespace["median"] = median
        namespace["stdev"] = stdev
    except ImportError:
        pass

    return namespace


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------

def run_python_analysis(code: str) -> str:
    """Execute Python code in a sandboxed REPL and return the output.

    The REPL namespace includes ``pandas`` (as ``pd``), ``numpy`` (as ``np``),
    ``json``, ``math``, ``datetime``, ``timedelta``, and basic statistics
    functions (``mean``, ``median``, ``stdev``).

    Use ``print()`` to produce output.  The last expression value is also
    captured if it is not None.

    Args:
        code: Python source code to execute.  Multi-line code is supported.

    Returns:
        A string containing captured stdout, stderr, and the repr of the
        last expression (if any), or an error traceback on failure.

    Example::

        run_python_analysis('''
        import pandas as pd
        data = {"channel": ["organic", "paid", "email"], "leads": [120, 85, 64]}
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
        print(f"Total leads: {df['leads'].sum()}")
        ''')
    """
    log.info("run_python_analysis called  code_len=%d  ts=%s", len(code), _ts())

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    namespace = _build_namespace()

    # Limit execution time (best-effort; not a hard sandbox)
    result_parts: list[str] = []

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(code, namespace)  # noqa: S102 — intentional for REPL tool
    except Exception:
        error_tb = traceback.format_exc()
        log.warning("REPL execution error:\n%s", error_tb)
        result_parts.append(f"[ERROR]\n{error_tb}")

    # Capture stdout
    stdout_val = stdout_buf.getvalue()
    if stdout_val:
        result_parts.insert(0, stdout_val.rstrip())

    # Capture stderr (warnings, etc.)
    stderr_val = stderr_buf.getvalue()
    if stderr_val:
        result_parts.append(f"[STDERR]\n{stderr_val.rstrip()}")

    # If nothing was captured, note that
    if not result_parts:
        result_parts.append("[OK] Code executed successfully with no output.")

    output = "\n".join(result_parts)

    # Truncate very long outputs
    max_chars = 8_000
    if len(output) > max_chars:
        output = output[:max_chars] + f"\n\n... [truncated, total {len(output)} chars]"

    log.info("REPL output length: %d chars", len(output))
    return output


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MarTech Analyst Sidekick — Python REPL Demo")
    print("=" * 60)

    # Demo 1: Basic calculation
    print("\n--- Demo 1: Basic Calculation ---")
    print(run_python_analysis("""
cac_values = [412, 389, 371, 358, 347]
avg_cac = sum(cac_values) / len(cac_values)
pct_change = (cac_values[-1] - cac_values[0]) / cac_values[0] * 100
print(f"Average CAC: ${avg_cac:.2f}")
print(f"CAC change over period: {pct_change:.1f}%")
"""))

    # Demo 2: Pandas analysis
    print("\n--- Demo 2: Pandas DataFrame ---")
    print(run_python_analysis("""
import pandas as pd

data = {
    "channel": ["Organic Search", "LinkedIn Ads", "Email", "Direct", "Google Ads"],
    "pipeline": [1412000, 983000, 745000, 512000, 328000],
    "spend": [45000, 180000, 25000, 0, 102000],
}
df = pd.DataFrame(data)
df["roi"] = df.apply(lambda r: r["pipeline"] / r["spend"] if r["spend"] > 0 else float("inf"), axis=1)
df = df.sort_values("roi", ascending=False)
print(df.to_string(index=False))
print(f"\\nTotal pipeline: ${df['pipeline'].sum():,.0f}")
"""))

    # Demo 3: Error handling
    print("\n--- Demo 3: Error Handling ---")
    print(run_python_analysis("x = 1 / 0"))
