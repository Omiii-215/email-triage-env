"""FastAPI server for the Email Triage environment.

Exposes the OpenEnv-standard endpoints: /reset, /step, /state, /health.
Also includes /tasks for listing available tasks.
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .environment import EmailTriageEnvironment
from ..tasks import list_tasks

# ── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_triage_env")

# ── Request/Response Models ────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = "easy_triage"


class StepRequest(BaseModel):
    category: str
    priority: int
    department: str
    summary: str


# ── Session management ────────────────────────────────────────────────
# Simple single-session for now (OpenEnv standard)

_env: Optional[EmailTriageEnvironment] = None


def get_env() -> EmailTriageEnvironment:
    global _env
    if _env is None:
        _env = EmailTriageEnvironment()
    return _env


# ── App ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize environment on startup."""
    logger.info("Email Triage Environment starting up...")
    get_env()
    yield
    logger.info("Email Triage Environment shutting down.")


app = FastAPI(
    title="Email Triage Environment",
    description="OpenEnv-compliant email triage simulation for training and evaluating AI agents.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Endpoints ──────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Redirect to API documentation."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/tasks")
async def get_tasks():
    """List all available tasks."""
    return {"tasks": list_tasks()}


@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()):
    """Reset the environment and start a new episode."""
    env = get_env()
    try:
        result = env.reset(task_id=request.task_id)
        logger.info(f"Reset with task_id={request.task_id}, episode={result['info']['episode_id']}")
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
async def step(request: StepRequest):
    """Execute an action (triage decision) in the environment."""
    env = get_env()
    action_data = request.model_dump()
    result = env.step(action_data)
    logger.info(
        f"Step {result['info']['step_count']}: "
        f"reward={result['reward']:.3f}, done={result['done']}, "
        f"cumulative={result['info']['cumulative_score']:.3f}"
    )
    return JSONResponse(content=result)


@app.get("/state")
async def state():
    """Get the current episode state."""
    env = get_env()
    return JSONResponse(content=env.state)
