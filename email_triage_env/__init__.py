"""Email Triage OpenEnv Environment.

A real-world email triage simulation where an AI agent must categorize,
prioritize, route, and summarize incoming emails.
"""

from .models import (
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageState,
)

__all__ = [
    "EmailTriageAction",
    "EmailTriageObservation",
    "EmailTriageState",
]
