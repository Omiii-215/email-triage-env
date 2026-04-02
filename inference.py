"""
Inference Script — Email Triage Environment
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables
"""

import os
import re
import json
import time
import textwrap
from typing import Dict, Any, Optional

import httpx
from openai import OpenAI

# ── Configuration ──────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")

# Environment server URL (local or HF Space)
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

TEMPERATURE = 0.1
MAX_TOKENS = 300

TASKS = ["easy_triage", "medium_triage", "hard_triage"]

# ── System Prompt ──────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""
You are an expert email triage assistant. For each email, analyze the content
and provide a triage decision as a JSON object with exactly these fields:

{
    "category": "<one of: urgent, action_required, informational, spam, meeting>",
    "priority": <integer 1-5, where 1=critical and 5=low>,
    "department": "<one of: engineering, sales, hr, legal, support, executive, trash>",
    "summary": "<one-line summary of the email>"
}

Guidelines:
- "urgent": Time-critical issues requiring immediate attention (system outages, security incidents, executive escalations)
- "action_required": Tasks that need a response/action but aren't time-critical (code reviews, approvals, form submissions)
- "informational": FYI emails, newsletters, announcements (no action needed)
- "spam": Unsolicited emails, phishing attempts, cold outreach from unknown parties
- "meeting": Calendar invites, meeting requests, scheduling discussions

- Priority 1: Business-critical, immediate action needed
- Priority 2: High importance, respond within hours
- Priority 3: Normal business priority
- Priority 4: Low priority, read when available
- Priority 5: Minimal importance, can safely ignore

- Route "spam" to "trash" department
- Consider sender domain and title when assessing legitimacy
- Watch for phishing: suspicious domains, urgency manipulation, credential requests

Respond ONLY with the JSON object. No explanation, no markdown formatting.
""").strip()


def build_user_prompt(email_data: Dict[str, Any]) -> str:
    """Build the user prompt from an email observation."""
    email = email_data
    cc = ", ".join(email.get("cc_list", [])) if email.get("cc_list") else "None"
    fwd = "Yes" if email.get("is_forwarded", False) else "No"
    attachments = "Yes" if email.get("has_attachments", False) else "No"

    prompt = textwrap.dedent(f"""
    Triage the following email:

    From: {email['sender']}
    Title/Role: {email.get('sender_title', 'Unknown')}
    Subject: {email['subject']}
    CC: {cc}
    Forwarded: {fwd}
    Attachments: {attachments}
    Reply Chain Depth: {email.get('reply_chain_length', 0)}
    Timestamp: {email.get('timestamp', 'Unknown')}

    Body:
    {email['body']}

    Respond with a JSON object containing: category, priority, department, summary.
    """).strip()

    return prompt


def parse_model_response(response_text: str) -> Dict[str, Any]:
    """Parse the model's response into a triage action dict."""
    if not response_text:
        return _fallback_action()

    # Try direct JSON parse
    try:
        result = json.loads(response_text.strip())
        return _validate_action(result)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            return _validate_action(result)
        except json.JSONDecodeError:
            pass

    # Try finding any JSON object
    json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            return _validate_action(result)
        except json.JSONDecodeError:
            pass

    return _fallback_action()


def _validate_action(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize the parsed action."""
    valid_categories = {"urgent", "action_required", "informational", "spam", "meeting"}
    valid_departments = {"engineering", "sales", "hr", "legal", "support", "executive", "trash"}

    category = str(data.get("category", "informational")).lower().strip()
    if category not in valid_categories:
        category = "informational"

    priority = data.get("priority", 3)
    try:
        priority = int(priority)
        priority = max(1, min(5, priority))
    except (ValueError, TypeError):
        priority = 3

    department = str(data.get("department", "engineering")).lower().strip()
    if department not in valid_departments:
        department = "engineering"

    summary = str(data.get("summary", "No summary provided"))

    return {
        "category": category,
        "priority": priority,
        "department": department,
        "summary": summary,
    }


def _fallback_action() -> Dict[str, Any]:
    """Return a safe fallback action."""
    return {
        "category": "informational",
        "priority": 3,
        "department": "engineering",
        "summary": "Could not parse email content",
    }


def run_task(client: OpenAI, env_client: httpx.Client, task_id: str) -> float:
    """Run a single task and return the final score."""
    print(f"\n{'='*60}")
    print(f"  TASK: {task_id}")
    print(f"{'='*60}")

    # Reset
    resp = env_client.post("/reset", json={"task_id": task_id})
    resp.raise_for_status()
    result = resp.json()

    observation = result["observation"]
    done = result["done"]
    step = 0

    while not done:
        step += 1
        email = observation.get("current_email")
        if email is None:
            break

        # Build prompt
        user_prompt = build_user_prompt(email)

        # Query LLM
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as e:
            print(f"  Step {step}: Model error: {e}")
            response_text = ""

        # Parse action
        action = parse_model_response(response_text)

        # Step
        resp = env_client.post("/step", json=action)
        resp.raise_for_status()
        result = resp.json()

        observation = result["observation"]
        reward = result["reward"]
        done = result["done"]

        print(
            f"  Step {step}: [{email['subject'][:40]}...] "
            f"→ {action['category']}/{action['priority']}/{action['department']} "
            f"| reward={reward:.3f}"
        )

    # Get final state
    resp = env_client.get("/state")
    resp.raise_for_status()
    state = resp.json()
    final_score = state.get("current_score", 0.0)

    print(f"\n  Final score for {task_id}: {final_score:.3f}")
    return final_score


def main() -> None:
    """Run inference on all tasks and report scores."""
    if not API_KEY:
        print("ERROR: Set OPENAI_API_KEY, HF_TOKEN, or API_KEY environment variable")
        return

    print(f"API Base URL: {API_BASE_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"Environment: {ENV_URL}")

    # Initialize clients
    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env_client = httpx.Client(base_url=ENV_URL, timeout=30.0)

    # Check health
    try:
        health = env_client.get("/health")
        health.raise_for_status()
        print(f"Environment health: {health.json()}")
    except Exception as e:
        print(f"ERROR: Cannot connect to environment at {ENV_URL}: {e}")
        print("Make sure the server is running: uvicorn email_triage_env.server.app:app --port 7860")
        return

    # Run all tasks
    scores = {}
    start_time = time.time()

    for task_id in TASKS:
        task_score = run_task(llm_client, env_client, task_id)
        scores[task_id] = task_score

    elapsed = time.time() - start_time

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    for task_id, score in scores.items():
        print(f"  {task_id:20s}: {score:.3f}")
    avg = sum(scores.values()) / len(scores) if scores else 0.0
    print(f"  {'Average':20s}: {avg:.3f}")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"{'='*60}")

    env_client.close()


if __name__ == "__main__":
    main()
