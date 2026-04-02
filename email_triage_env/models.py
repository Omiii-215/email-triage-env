"""Typed Pydantic models for the Email Triage environment."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class EmailCategory(str, Enum):
    URGENT = "urgent"
    ACTION_REQUIRED = "action_required"
    INFORMATIONAL = "informational"
    SPAM = "spam"
    MEETING = "meeting"


class Department(str, Enum):
    ENGINEERING = "engineering"
    SALES = "sales"
    HR = "hr"
    LEGAL = "legal"
    SUPPORT = "support"
    EXECUTIVE = "executive"
    TRASH = "trash"


# ── Action ─────────────────────────────────────────────────────────────

class EmailTriageAction(BaseModel):
    """Agent's triage decision for the current email."""

    category: str = Field(
        ...,
        description="Email category: urgent, action_required, informational, spam, meeting",
    )
    priority: int = Field(
        ...,
        ge=1,
        le=5,
        description="Priority level 1 (critical) to 5 (low)",
    )
    department: str = Field(
        ...,
        description="Routing department: engineering, sales, hr, legal, support, executive, trash",
    )
    summary: str = Field(
        ...,
        description="One-line summary of the email content",
    )


# ── Observation ────────────────────────────────────────────────────────

class EmailData(BaseModel):
    """An individual email presented to the agent."""

    email_id: str
    sender: str
    sender_title: Optional[str] = None
    subject: str
    body: str
    timestamp: str
    has_attachments: bool = False
    reply_chain_length: int = 0
    cc_list: List[str] = Field(default_factory=list)
    is_forwarded: bool = False


class EmailTriageObservation(BaseModel):
    """What the agent sees after each step."""

    task_description: str = ""
    current_email: Optional[EmailData] = None
    emails_remaining: int = 0
    emails_processed: int = 0
    last_reward: float = 0.0
    last_feedback: str = ""
    done: bool = False
    cumulative_score: float = 0.0


# ── State ──────────────────────────────────────────────────────────────

class EmailTriageState(BaseModel):
    """Episode metadata accessible via state()."""

    episode_id: str = ""
    task_id: str = ""
    step_count: int = 0
    total_emails: int = 0
    emails_processed: int = 0
    current_score: float = 0.0
    done: bool = False
