"""
Project 2 — Autonomous SDR Outreach Agent
File: guardrails.py
Book: "Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar
Framework: OpenAI Agents SDK

Brand-safety and regulatory-compliance guardrails applied to every
outgoing email before it is dispatched.

Two public functions:
    compliance_check   — validates CAN-SPAM (US) and GDPR (EU) requirements
    brand_voice_validator — enforces brand tone, banned phrases, and length limits

Both return {"passed": bool, "issues": list[str]} so the agent can
either proceed or revise the draft before sending.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# CAN-SPAM requires a physical mailing address and an unsubscribe mechanism.
_UNSUBSCRIBE_PATTERNS: list[str] = [
    r"(?i)unsubscribe",
    r"(?i)opt[\s-]?out",
    r"(?i)manage\s+(your\s+)?preferences",
    r"(?i)stop\s+receiving",
]

_PHYSICAL_ADDRESS_PATTERN: str = (
    r"\d{1,5}\s+\w+.*(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr"
    r"|Lane|Ln|Way|Court|Ct|Suite|Ste|Floor|Fl)\b"
)

# GDPR requires explicit consent language when emailing EU contacts for
# the first time (cold outreach).  We look for a "legitimate interest"
# or "consent" reference.
_GDPR_CONSENT_PATTERNS: list[str] = [
    r"(?i)legitimate\s+interest",
    r"(?i)consent",
    r"(?i)right\s+to\s+(be\s+)?forget",
    r"(?i)data\s+subject\s+rights",
    r"(?i)privacy\s+policy",
    r"(?i)gdpr",
]

# Brand-voice constraints
_BANNED_PHRASES: list[str] = [
    "buy now",
    "act now",
    "limited time offer",
    "guaranteed",
    "no obligation",
    "click here",
    "free money",
    "once in a lifetime",
    "you've been selected",
    "congratulations",
    "dear friend",
    "100% free",
    "risk-free",
    "urgent",
    "winner",
]

_MAX_SUBJECT_LENGTH: int = 120
_MAX_BODY_LENGTH: int = 5000
_MIN_BODY_LENGTH: int = 50

# Tone: we flag overly aggressive or salesy all-caps runs (>= 4 consecutive
# uppercase words).
_ALLCAPS_RUN_PATTERN: str = r"(?:\b[A-Z]{2,}\b\s*){4,}"


# ===================================================================
# 1. Compliance Check  (CAN-SPAM / GDPR)
# ===================================================================

def compliance_check(
    email_content: str,
    recipient_region: str = "US",
) -> dict[str, Any]:
    """Validate an email draft against CAN-SPAM and GDPR regulations.

    Parameters
    ----------
    email_content:
        The full email body text to validate.
    recipient_region:
        ISO-style region hint — ``"US"``, ``"EU"``, ``"UK"``, ``"CA"``, etc.
        Determines which regulation set is primary.

    Returns
    -------
    dict with keys ``passed`` (bool) and ``issues`` (list[str]).
    """
    issues: list[str] = []
    region = recipient_region.upper().strip()
    log.info("compliance_check  region=%s  content_length=%d", region, len(email_content))

    # --- Universal checks ---------------------------------------------------

    # 1. Deceptive subject-line heuristic: "Re:" or "Fwd:" when this is the
    #    first email.  We flag it as a warning (CAN-SPAM prohibits deceptive
    #    headers).
    if re.match(r"^(Re|Fwd):", email_content.strip()):
        issues.append(
            "CAN-SPAM: Subject begins with 'Re:' or 'Fwd:' which may be "
            "deceptive if this is the first outreach."
        )

    # 2. Must contain an unsubscribe / opt-out mechanism
    has_unsub = any(
        re.search(pat, email_content) for pat in _UNSUBSCRIBE_PATTERNS
    )
    if not has_unsub:
        issues.append(
            "CAN-SPAM: Email must include an unsubscribe or opt-out mechanism."
        )

    # 3. Must contain a physical mailing address
    has_address = bool(re.search(_PHYSICAL_ADDRESS_PATTERN, email_content))
    if not has_address:
        issues.append(
            "CAN-SPAM: Email must include a valid physical mailing address."
        )

    # --- GDPR-specific checks (EU / UK / EEA) ------------------------------

    if region in ("EU", "UK", "EEA", "DE", "FR", "ES", "IT", "NL", "BE"):
        has_consent_ref = any(
            re.search(pat, email_content) for pat in _GDPR_CONSENT_PATTERNS
        )
        if not has_consent_ref:
            issues.append(
                "GDPR: Email to an EU/UK recipient should reference the legal "
                "basis for contact (e.g., legitimate interest or consent) or "
                "include a link to your privacy policy."
            )

    # --- Canada CASL check --------------------------------------------------

    if region in ("CA",):
        # CASL requires express or implied consent and sender identification
        if not has_unsub:
            issues.append(
                "CASL: Canadian anti-spam law requires a clear unsubscribe "
                "mechanism."
            )

    passed = len(issues) == 0
    log.info("compliance_check  passed=%s  issues=%d", passed, len(issues))
    return {"passed": passed, "issues": issues}


# ===================================================================
# 2. Brand Voice Validator
# ===================================================================

def brand_voice_validator(content: str) -> dict[str, Any]:
    """Check that *content* adheres to brand voice and messaging guidelines.

    Validates:
    * No banned / spammy phrases
    * No excessive capitalisation runs
    * Body length within acceptable range
    * Professional greeting present
    * Sign-off present

    Parameters
    ----------
    content:
        The full email body text (may include subject line at the top).

    Returns
    -------
    dict with keys ``passed`` (bool) and ``issues`` (list[str]).
    """
    issues: list[str] = []
    log.info("brand_voice_validator  content_length=%d", len(content))

    lower_content = content.lower()

    # 1. Banned phrases
    for phrase in _BANNED_PHRASES:
        if phrase in lower_content:
            issues.append(
                f"Brand voice: Banned phrase detected — '{phrase}'. "
                f"Rewrite to sound consultative, not salesy."
            )

    # 2. Excessive caps
    if re.search(_ALLCAPS_RUN_PATTERN, content):
        issues.append(
            "Brand voice: Avoid long runs of ALL-CAPS words. "
            "Use sentence case for a professional tone."
        )

    # 3. Length guard-rails
    if len(content) > _MAX_BODY_LENGTH:
        issues.append(
            f"Brand voice: Email body exceeds {_MAX_BODY_LENGTH} characters. "
            f"Keep outreach concise and scannable."
        )
    if len(content) < _MIN_BODY_LENGTH:
        issues.append(
            f"Brand voice: Email body is under {_MIN_BODY_LENGTH} characters. "
            f"Provide enough context for the recipient to understand the value."
        )

    # 4. Greeting heuristic — first line should address the recipient
    first_line = content.strip().split("\n")[0].strip()
    greeting_ok = any(
        first_line.lower().startswith(g)
        for g in ("hi ", "hey ", "hello ", "dear ", "good morning", "good afternoon")
    )
    if not greeting_ok:
        issues.append(
            "Brand voice: Email should open with a personal greeting "
            "(e.g., 'Hi Jane,' or 'Hello,')."
        )

    # 5. Sign-off heuristic
    has_signoff = any(
        marker in lower_content
        for marker in (
            "best,", "cheers,", "regards,", "thanks,", "thank you,",
            "sincerely,", "warm regards,", "best regards,", "kind regards,",
            "your sdr", "your bdr", "your rep",
        )
    )
    if not has_signoff:
        issues.append(
            "Brand voice: Email should end with a professional sign-off "
            "(e.g., 'Best,' or 'Cheers,')."
        )

    # 6. Emoji density — allow a few but flag if excessive (> 5)
    emoji_pattern = re.compile(
        "[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff"
        "\u2600-\u26ff\u2700-\u27bf]",
        flags=re.UNICODE,
    )
    emoji_count = len(emoji_pattern.findall(content))
    if emoji_count > 5:
        issues.append(
            f"Brand voice: {emoji_count} emojis detected. Limit emoji usage "
            f"to maintain a professional tone."
        )

    passed = len(issues) == 0
    log.info("brand_voice_validator  passed=%s  issues=%d", passed, len(issues))
    return {"passed": passed, "issues": issues}


# ---------------------------------------------------------------------------
# Convenience wrapper — run both checks in one call
# ---------------------------------------------------------------------------

def run_all_guardrails(
    email_body: str,
    recipient_region: str = "US",
) -> dict[str, Any]:
    """Run compliance + brand-voice checks and merge results.

    Returns
    -------
    dict with ``passed`` (bool) and ``issues`` (list[str]).
    """
    comp = compliance_check(email_body, recipient_region)
    brand = brand_voice_validator(email_body)
    all_issues = comp["issues"] + brand["issues"]
    return {"passed": len(all_issues) == 0, "issues": all_issues}
