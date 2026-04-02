"""Task definitions and graders for the Email Triage environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TaskDefinition:
    """A single task with its configuration and grading criteria."""

    task_id: str
    description: str
    num_emails: int
    difficulty: str
    seed: int
    max_steps: int  # = num_emails (one step per email)

    def grade(self, per_email_scores: List[float]) -> float:
        """Compute final task score as the mean of per-email scores.

        Returns a float in [0.0, 1.0].
        """
        if not per_email_scores:
            return 0.0
        return max(0.0, min(1.0, sum(per_email_scores) / len(per_email_scores)))


# ── Task Registry ──────────────────────────────────────────────────────

TASKS: Dict[str, TaskDefinition] = {
    "easy_triage": TaskDefinition(
        task_id="easy_triage",
        description=(
            "Triage 5 clearly-categorized emails. Each email has obvious "
            "signals: explicit urgency markers, clear spam indicators, "
            "straightforward meeting invites, and unambiguous categories. "
            "A good agent should score ≥ 0.80."
        ),
        num_emails=5,
        difficulty="easy",
        seed=42,
        max_steps=5,
    ),
    "medium_triage": TaskDefinition(
        task_id="medium_triage",
        description=(
            "Triage 10 emails with mixed difficulty. Some have clear signals "
            "but others require careful reading: ambiguous senders, mixed "
            "urgency cues, and subtle category boundaries (e.g. is a vendor "
            "cold email spam or informational?). Frontier models ≈ 0.65."
        ),
        num_emails=10,
        difficulty="medium",
        seed=123,
        max_steps=10,
    ),
    "hard_triage": TaskDefinition(
        task_id="hard_triage",
        description=(
            "Triage 15 emails including the hardest cases: long reply chains "
            "requiring context tracking, subtle phishing disguised as internal "
            "IT communications, competing urgency cues, forwarded messages "
            "with ambiguous intent, and emails requiring domain-specific "
            "reasoning. Frontier models ≈ 0.45."
        ),
        num_emails=15,
        difficulty="hard",
        seed=456,
        max_steps=15,
    ),
}


def get_task(task_id: str) -> TaskDefinition:
    """Get a task by ID."""
    if task_id not in TASKS:
        raise ValueError(
            f"Unknown task_id: '{task_id}'. Available: {list(TASKS.keys())}"
        )
    return TASKS[task_id]


def list_tasks() -> List[Dict]:
    """List all available tasks with metadata."""
    return [
        {
            "task_id": t.task_id,
            "description": t.description,
            "num_emails": t.num_emails,
            "difficulty": t.difficulty,
            "max_steps": t.max_steps,
        }
        for t in TASKS.values()
    ]
