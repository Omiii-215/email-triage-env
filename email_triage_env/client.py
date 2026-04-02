"""HTTP client for the Email Triage environment.

Can be used directly against a running server (local or HF Space).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import httpx

from .models import EmailTriageAction, EmailTriageObservation, EmailTriageState


class EmailTriageClient:
    """Synchronous HTTP client for the Email Triage environment."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def health(self) -> Dict[str, Any]:
        """Check server health."""
        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()

    def reset(self, task_id: str = "easy_triage") -> Dict[str, Any]:
        """Reset the environment with a given task."""
        response = self._client.post("/reset", json={"task_id": task_id})
        response.raise_for_status()
        return response.json()

    def step(self, action: EmailTriageAction) -> Dict[str, Any]:
        """Send an action to the environment."""
        response = self._client.post("/step", json=action.model_dump())
        response.raise_for_status()
        return response.json()

    def state(self) -> Dict[str, Any]:
        """Get the current episode state."""
        response = self._client.get("/state")
        response.raise_for_status()
        return response.json()

    def list_tasks(self) -> Dict[str, Any]:
        """List available tasks."""
        response = self._client.get("/tasks")
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
