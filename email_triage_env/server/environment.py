"""Email Triage environment — core step/reset/state logic."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from ..models import (
    EmailData,
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageState,
)
from ..email_generator import generate_emails_for_task
from ..tasks import get_task, TaskDefinition


# ── Reward Scoring ─────────────────────────────────────────────────────

# Category similarity groups for partial credit
_CATEGORY_GROUPS = {
    "urgent": {"action_required"},  # close to action_required
    "action_required": {"urgent"},
    "informational": {"meeting"},
    "meeting": {"informational"},
    "spam": set(),  # spam is never close to anything
}

# Department similarity groups for partial credit
_DEPARTMENT_GROUPS = {
    "engineering": {"support"},
    "support": {"engineering", "sales"},
    "sales": {"support"},
    "hr": {"legal"},
    "legal": {"hr", "executive"},
    "executive": {"legal"},
    "trash": set(),
}

# Weights
W_CATEGORY = 0.35
W_PRIORITY = 0.25
W_DEPARTMENT = 0.25
W_SUMMARY = 0.15

PENALTY_MALFORMED = -0.1
PENALTY_REPEATED_SUMMARY = -0.05


def score_action(
    action: EmailTriageAction,
    ground_truth: Dict[str, Any],
    prev_summary: Optional[str] = None,
) -> tuple[float, str]:
    """Score a single triage action against ground truth.

    Returns (score, feedback_message) where score is in [-0.15, 1.0].
    The caller clamps the final score per-email to [0.0, 1.0].
    """
    gt_cat = ground_truth["category"]
    gt_pri = ground_truth["priority"]
    gt_dep = ground_truth["department"]
    gt_kw = [kw.lower() for kw in ground_truth["keywords"]]

    feedback_parts = []
    penalty = 0.0

    # ── Category score ─────────────────────────────────────────────
    agent_cat = action.category.lower().strip()
    if agent_cat == gt_cat:
        cat_score = 1.0
    elif agent_cat in _CATEGORY_GROUPS.get(gt_cat, set()):
        cat_score = 0.3
        feedback_parts.append(f"Category '{agent_cat}' close but expected '{gt_cat}'")
    else:
        cat_score = 0.0
        feedback_parts.append(f"Category wrong: got '{agent_cat}', expected '{gt_cat}'")

    # ── Priority score ─────────────────────────────────────────────
    pri_diff = abs(action.priority - gt_pri)
    if pri_diff == 0:
        pri_score = 1.0
    elif pri_diff == 1:
        pri_score = 0.5
        feedback_parts.append(f"Priority close: got {action.priority}, expected {gt_pri}")
    elif pri_diff == 2:
        pri_score = 0.25
        feedback_parts.append(f"Priority off by 2: got {action.priority}, expected {gt_pri}")
    else:
        pri_score = 0.0
        feedback_parts.append(f"Priority far off: got {action.priority}, expected {gt_pri}")

    # ── Department score ───────────────────────────────────────────
    agent_dep = action.department.lower().strip()
    if agent_dep == gt_dep:
        dep_score = 1.0
    elif agent_dep in _DEPARTMENT_GROUPS.get(gt_dep, set()):
        dep_score = 0.3
        feedback_parts.append(f"Department '{agent_dep}' close but expected '{gt_dep}'")
    else:
        dep_score = 0.0
        feedback_parts.append(f"Department wrong: got '{agent_dep}', expected '{gt_dep}'")

    # ── Summary score ──────────────────────────────────────────────
    summary_lower = action.summary.lower().strip()
    if not summary_lower:
        sum_score = 0.0
        feedback_parts.append("Summary is empty")
    else:
        # Keyword overlap ratio
        matched = sum(1 for kw in gt_kw if kw in summary_lower)
        sum_score = min(1.0, matched / max(1, len(gt_kw)))

    # ── Penalties ──────────────────────────────────────────────────
    # Check for repeated summary (bot detection)
    if prev_summary and summary_lower == prev_summary.lower().strip():
        penalty += PENALTY_REPEATED_SUMMARY
        feedback_parts.append("Summary identical to previous (penalty)")

    # Check for malformed values
    valid_cats = {"urgent", "action_required", "informational", "spam", "meeting"}
    valid_deps = {"engineering", "sales", "hr", "legal", "support", "executive", "trash"}
    if agent_cat not in valid_cats:
        penalty += PENALTY_MALFORMED
        feedback_parts.append(f"Invalid category '{agent_cat}' (penalty)")
    if agent_dep not in valid_deps:
        penalty += PENALTY_MALFORMED
        feedback_parts.append(f"Invalid department '{agent_dep}' (penalty)")

    # ── Final weighted score ───────────────────────────────────────
    raw_score = (
        W_CATEGORY * cat_score
        + W_PRIORITY * pri_score
        + W_DEPARTMENT * dep_score
        + W_SUMMARY * sum_score
        + penalty
    )

    if not feedback_parts:
        feedback = "Perfect triage!"
    else:
        feedback = "; ".join(feedback_parts)

    return raw_score, feedback


# ── Environment ────────────────────────────────────────────────────────

class EmailTriageEnvironment:
    """OpenEnv-compatible environment for email triage."""

    def __init__(self):
        self._state = EmailTriageState()
        self._emails: List[Dict[str, Any]] = []
        self._current_idx: int = 0
        self._per_email_scores: List[float] = []
        self._task: Optional[TaskDefinition] = None
        self._prev_summary: Optional[str] = None

    def reset(self, task_id: str = "easy_triage") -> Dict[str, Any]:
        """Start a new episode for the given task.

        Returns the initial observation as a dict.
        """
        self._task = get_task(task_id)
        self._emails = generate_emails_for_task(task_id, seed=self._task.seed)
        self._current_idx = 0
        self._per_email_scores = []
        self._prev_summary = None

        episode_id = str(uuid.uuid4())
        self._state = EmailTriageState(
            episode_id=episode_id,
            task_id=task_id,
            step_count=0,
            total_emails=len(self._emails),
            emails_processed=0,
            current_score=0.0,
            done=False,
        )

        obs = self._make_observation(
            reward=0.0,
            feedback="Episode started. Triage each email by providing category, priority, department, and summary.",
        )
        return self._obs_to_result(obs, reward=0.0, done=False)

    def step(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the agent's triage action for the current email.

        Returns observation, reward, done, info as a dict.
        """
        if self._state.done:
            obs = self._make_observation(
                reward=0.0,
                feedback="Episode is already done. Call reset() to start a new one.",
            )
            return self._obs_to_result(obs, reward=0.0, done=True)

        # Parse action
        try:
            action = EmailTriageAction(**action_data)
        except Exception as e:
            # Malformed action — penalize and skip
            self._per_email_scores.append(0.0)
            self._current_idx += 1
            self._state.step_count += 1
            self._state.emails_processed += 1

            done = self._current_idx >= len(self._emails)
            self._state.done = done
            if done:
                self._state.current_score = self._compute_final_score()

            obs = self._make_observation(
                reward=-0.1,
                feedback=f"Malformed action: {e}. Scored 0.0 for this email.",
            )
            return self._obs_to_result(obs, reward=-0.1, done=done)

        # Score the action
        current_email = self._emails[self._current_idx]
        ground_truth = current_email["ground_truth"]
        raw_score, feedback = score_action(action, ground_truth, self._prev_summary)
        clamped_score = max(0.0, min(1.0, raw_score))
        self._per_email_scores.append(clamped_score)
        self._prev_summary = action.summary

        # Advance state
        self._current_idx += 1
        self._state.step_count += 1
        self._state.emails_processed += 1
        self._state.current_score = self._compute_final_score()

        done = self._current_idx >= len(self._emails)
        self._state.done = done

        if done:
            final_score = self._state.current_score
            feedback += f" | Episode complete! Final score: {final_score:.3f}"

        obs = self._make_observation(reward=clamped_score, feedback=feedback)
        return self._obs_to_result(obs, reward=clamped_score, done=done)

    @property
    def state(self) -> Dict[str, Any]:
        """Return current episode state."""
        return self._state.model_dump()

    def _make_observation(self, reward: float, feedback: str) -> EmailTriageObservation:
        """Build the observation for the current state."""
        current_email = None
        if not self._state.done and self._current_idx < len(self._emails):
            e = self._emails[self._current_idx]
            current_email = EmailData(
                email_id=e["email_id"],
                sender=e["sender"],
                sender_title=e.get("sender_title"),
                subject=e["subject"],
                body=e["body"],
                timestamp=e["timestamp"],
                has_attachments=e.get("has_attachments", False),
                reply_chain_length=e.get("reply_chain_length", 0),
                cc_list=e.get("cc_list", []),
                is_forwarded=e.get("is_forwarded", False),
            )

        return EmailTriageObservation(
            task_description=self._task.description if self._task else "",
            current_email=current_email,
            emails_remaining=max(0, len(self._emails) - self._current_idx),
            emails_processed=self._state.emails_processed,
            last_reward=reward,
            last_feedback=feedback,
            done=self._state.done,
            cumulative_score=self._state.current_score,
        )

    def _obs_to_result(self, obs: EmailTriageObservation, reward: float, done: bool) -> Dict[str, Any]:
        """Convert observation to the standard result dict."""
        return {
            "observation": obs.model_dump(),
            "reward": reward,
            "done": done,
            "info": {
                "episode_id": self._state.episode_id,
                "step_count": self._state.step_count,
                "cumulative_score": self._state.current_score,
            },
        }

    def _compute_final_score(self) -> float:
        """Compute running average score."""
        if not self._per_email_scores:
            return 0.0
        return sum(self._per_email_scores) / len(self._per_email_scores)
