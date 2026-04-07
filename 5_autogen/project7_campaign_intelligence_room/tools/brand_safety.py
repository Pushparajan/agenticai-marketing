# tools/brand_safety.py
# Project 7: Campaign Intelligence Room
# Chapter Reference: Chapter 5 - AutoGen
# Description: Brand guideline and regulatory compliance checking tools
# Author: Pushparajan Ramar

"""Brand safety, guideline checking, and regulatory compliance tools.

Rule-based content review against brand guidelines and regulatory
compliance checks (GDPR, CAN-SPAM, FTC, SEC).  Returns structured
pass/fail verdicts with specific issues and remediation guidance.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

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
# Brand guideline rules
# ---------------------------------------------------------------------------

_BANNED_TERMS: list[dict[str, str]] = [
    {"pattern": r"\bcheap(est|ly)?\b",
     "issue": "Avoid 'cheap' — use 'cost-effective' or 'affordable'.", "severity": "high"},
    {"pattern": r"\bguarantee[ds]?\b",
     "issue": "Unqualified 'guarantee' claims may violate FTC guidelines.", "severity": "high"},
    {"pattern": r"\b#\s?1\b|\bnumber\s*one\b|\bbest\s+in\s+class\b",
     "issue": "Superlative claims require substantiation.", "severity": "medium"},
    {"pattern": r"\brevolut?ionary\b",
     "issue": "'revolutionary' is on the brand avoid list — use 'innovative'.", "severity": "low"},
    {"pattern": r"\bsynerg(y|ies|istic)\b",
     "issue": "Jargon 'synergy' conflicts with brand voice (plain language).", "severity": "low"},
    {"pattern": r"\b(crush|destroy|kill|annihilate)\s+(the\s+)?competition\b",
     "issue": "Aggressive competitive language violates brand tone.", "severity": "high"},
    {"pattern": r"\bfree\b(?!\s+(trial|tier|plan|edition))",
     "issue": "Unqualified 'free' may trigger FTC scrutiny.", "severity": "medium"},
]

_TONE_CHECKS: list[dict[str, str]] = [
    {"pattern": r"!!+",
     "issue": "Excessive exclamation marks conflict with professional tone.", "severity": "low"},
    {"pattern": r"\bASAP\b|\bURGENT\b|\bACT\s+NOW\b|\bLIMITED\s+TIME\b",
     "issue": "High-pressure urgency language conflicts with brand trust.", "severity": "medium"},
    {"pattern": r"[A-Z]{5,}",
     "issue": "Extended ALL-CAPS text violates typography guidelines.", "severity": "low"},
]


# ---------------------------------------------------------------------------
# Regulatory rule sets
# ---------------------------------------------------------------------------

_REGULATION_RULES: dict[str, list[dict[str, str]]] = {
    "gdpr": [
        {"pattern": r"\btrack(s|ed|ing)?\b.*\bwithout\b.*\bconsent\b",
         "issue": "GDPR: Must not imply tracking without explicit consent.", "severity": "critical"},
        {"pattern": r"\b(personal|user)\s+data\b(?!.*\b(consent|permission|opt[\s-]?in)\b)",
         "issue": "GDPR: Personal data references should mention consent.", "severity": "high"},
        {"pattern": r"\bprofile\s+(everything|all)\b",
         "issue": "GDPR: Avoid implying unlimited profiling.", "severity": "high"},
    ],
    "can_spam": [
        {"pattern": r"\bno[\s-]?reply@\b",
         "issue": "CAN-SPAM: Must not use no-reply sender addresses.", "severity": "high"},
        {"pattern": r"(?i)(?!.*unsubscribe)^.{500,}$",
         "issue": "CAN-SPAM: Must include an unsubscribe mechanism.", "severity": "critical"},
    ],
    "ftc": [
        {"pattern": r"\bguarantee[ds]?\s+(results|roi|revenue|growth)\b",
         "issue": "FTC: Guaranteed performance claims require substantiation.", "severity": "critical"},
        {"pattern": r"\b\d+x\s+(roi|return|growth|revenue)\b",
         "issue": "FTC: Multiplier claims must be substantiated with evidence.", "severity": "high"},
        {"pattern": r"\btestimonial\b(?!.*\b(typical|results\s+may\s+vary)\b)",
         "issue": "FTC: Testimonials need 'results may vary' disclaimer.", "severity": "medium"},
    ],
    "sec": [
        {"pattern": r"\b(guaranteed|assured)\s+(returns?|income|profit)\b",
         "issue": "SEC: Guaranteed financial return claims are prohibited.", "severity": "critical"},
        {"pattern": r"\binvestment\s+advice\b",
         "issue": "SEC: Avoid language construed as investment advice.", "severity": "high"},
    ],
    "general": [
        {"pattern": r"\bcure[ds]?\b|\btreat(s|ed|ment)?\b",
         "issue": "Health: Medical cure/treatment language requires FDA review.", "severity": "critical"},
        {"pattern": r"\b(children|kids|minors)\b.*\b(data|track|target)\b",
         "issue": "COPPA: Children's data references require compliance review.", "severity": "critical"},
    ],
}


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def check_brand_guidelines(content: str) -> str:
    """Check content against brand guidelines for tone, terminology, and claims.

    Args:
        content: The marketing content to check (plain text or light HTML).

    Returns:
        JSON string with pass/fail verdict and list of specific issues.
    """
    log.info(
        "check_brand_guidelines  content_len=%d  mock=%s  ts=%s",
        len(content), USE_MOCK, _ts(),
    )

    issues: list[dict[str, str]] = []

    # Check banned terms
    for rule in _BANNED_TERMS:
        if re.search(rule["pattern"], content, re.IGNORECASE):
            matches = re.findall(rule["pattern"], content, re.IGNORECASE)
            issues.append({
                "category": "banned_term",
                "severity": rule["severity"],
                "issue": rule["issue"],
                "matches_found": len(matches),
            })

    # Check tone
    for rule in _TONE_CHECKS:
        if re.search(rule["pattern"], content):
            issues.append({
                "category": "tone_violation",
                "severity": rule["severity"],
                "issue": rule["issue"],
            })

    # Check opening line length (brand guideline: headlines < 60 chars)
    first_line = content.strip().split("\n")[0].strip()
    if len(first_line) > 120:
        issues.append({"category": "formatting", "severity": "low",
                        "issue": f"Opening line is {len(first_line)} chars — aim for under 60."})

    # Determine verdict
    critical_count = sum(1 for i in issues if i["severity"] in ("critical", "high"))
    passed = critical_count == 0

    result: dict[str, Any] = {
        "verdict": "PASS" if passed else "FAIL",
        "passed": passed,
        "total_issues": len(issues),
        "critical_or_high": critical_count,
        "issues": issues,
        "content_length_chars": len(content),
        "recommendations": [],
        "checked_at": _ts(),
    }

    if not passed:
        result["recommendations"].append(
            "Revise content to address all HIGH and CRITICAL issues before publishing."
        )
    if any(i["category"] == "tone_violation" for i in issues):
        result["recommendations"].append(
            "Review brand voice guidelines: professional, confident, jargon-free."
        )
    if not issues:
        result["recommendations"].append(
            "Content passes all automated brand checks. Proceed to human review."
        )

    log.info(
        "Brand guidelines check: verdict=%s  issues=%d  critical=%d",
        result["verdict"], len(issues), critical_count,
    )
    return json.dumps(result, indent=2)


def review_compliance(content: str, regulations: str = "gdpr,ftc,can_spam") -> str:
    """Review content against regulatory compliance requirements.

    Args:
        content:     The marketing content to review (plain text or HTML).
        regulations: Comma-separated regulation sets, e.g. "gdpr,ftc,can_spam,sec".

    Returns:
        JSON string with compliance pass/fail verdict and violation details.
    """
    log.info(
        "review_compliance  content_len=%d  regulations=%s  mock=%s  ts=%s",
        len(content), regulations, USE_MOCK, _ts(),
    )

    # Parse requested regulations
    requested_regs = [
        r.strip().lower().replace("-", "_").replace(" ", "_")
        for r in regulations.split(",")
        if r.strip()
    ]
    # Always include general rules
    if "general" not in requested_regs:
        requested_regs.append("general")

    violations: list[dict[str, Any]] = []
    regulations_checked: list[str] = []

    for reg_name in requested_regs:
        rules = _REGULATION_RULES.get(reg_name, [])
        if not rules:
            log.warning("Unknown regulation set: '%s' — skipping", reg_name)
            continue
        regulations_checked.append(reg_name.upper())
        for rule in rules:
            if re.search(rule["pattern"], content, re.IGNORECASE | re.DOTALL):
                violations.append({
                    "regulation": reg_name.upper(),
                    "severity": rule["severity"],
                    "issue": rule["issue"],
                })

    critical_count = sum(1 for v in violations if v["severity"] == "critical")
    high_count = sum(1 for v in violations if v["severity"] == "high")
    passed = critical_count == 0

    result: dict[str, Any] = {
        "verdict": "PASS" if passed else "FAIL",
        "passed": passed,
        "regulations_checked": regulations_checked,
        "total_violations": len(violations),
        "critical_violations": critical_count,
        "high_violations": high_count,
        "violations": violations,
        "remediation_guidance": [],
        "reviewed_at": _ts(),
    }

    if critical_count > 0:
        result["remediation_guidance"].append(
            "CRITICAL: Content must not be published until all critical violations are resolved."
        )
    if high_count > 0:
        result["remediation_guidance"].append(
            "HIGH: Address high-severity issues before campaign launch. "
            "Consult legal team if unclear."
        )
    if not violations:
        result["remediation_guidance"].append(
            "No automated compliance issues detected. "
            "Recommend legal team review before final approval."
        )

    log.info(
        "Compliance review: verdict=%s  violations=%d  critical=%d  regulations=%s",
        result["verdict"], len(violations), critical_count, regulations_checked,
    )
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60, "\nBrand Safety Tools Demo\n", "=" * 60)
    _ok = "Discover how our platform helps enterprise teams reduce time-to-value by 40%."
    _bad = (
        "GUARANTEED RESULTS!! Our revolutionary #1 BEST IN CLASS solution will "
        "CRUSH THE COMPETITION. We track personal data without consent for 10x ROI. "
        "ACT NOW — cheapest deal ever!"
    )
    print("--- Clean Content ---")
    print(check_brand_guidelines(_ok))
    print("\n--- Problematic Content ---")
    print(check_brand_guidelines(_bad))
    print("\n--- Compliance (GDPR, FTC) ---")
    print(review_compliance(_bad, "gdpr,ftc"))
