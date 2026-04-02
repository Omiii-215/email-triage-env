---
title: Email Triage Env
emoji: 📧
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Email Triage Environment — OpenEnv

A real-world **email triage simulation** built on the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework. An AI agent receives emails and must **categorize**, **prioritize**, **route**, and **summarize** each one — just like a knowledge worker managing a corporate inbox.

## Why Email Triage?

Every professional triages email daily. It requires:
- **Reading comprehension** — understanding email content and intent
- **Classification** — distinguishing urgency, action items, meetings, and spam
- **Contextual reasoning** — interpreting reply chains, sender authority, and phishing signals
- **Summarization** — distilling emails into one-line summaries

This makes it an ideal benchmark for evaluating LLM agent capabilities on a genuinely useful task.

## Action Space

The agent provides a structured triage decision for each email:

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `category` | string | `urgent`, `action_required`, `informational`, `spam`, `meeting` | Email classification |
| `priority` | int | 1–5 | 1 = critical, 5 = low |
| `department` | string | `engineering`, `sales`, `hr`, `legal`, `support`, `executive`, `trash` | Routing destination |
| `summary` | string | free text | One-line email summary |

## Observation Space

Each observation contains the current email to triage:

| Field | Type | Description |
|-------|------|-------------|
| `current_email.sender` | string | Sender email address |
| `current_email.sender_title` | string | Sender's role/title |
| `current_email.subject` | string | Email subject line |
| `current_email.body` | string | Full email body |
| `current_email.has_attachments` | bool | Whether email has files attached |
| `current_email.reply_chain_length` | int | Depth of the reply chain |
| `current_email.cc_list` | list | CC'd recipients |
| `current_email.is_forwarded` | bool | Whether the email was forwarded |
| `emails_remaining` | int | Emails left in the batch |
| `last_reward` | float | Reward from previous action |
| `last_feedback` | string | Grading feedback from previous action |

## Reward Function

Per-email score computed from weighted components:

| Component | Weight | Scoring |
|-----------|--------|---------|
| Category match | 35% | Exact = 1.0, close = 0.3, wrong = 0.0 |
| Priority match | 25% | Exact = 1.0, ±1 = 0.5, ±2 = 0.25, else = 0.0 |
| Department match | 25% | Exact = 1.0, same division = 0.3, wrong = 0.0 |
| Summary quality | 15% | Keyword overlap with ground-truth key terms |

**Penalties**: -0.1 for malformed actions, -0.05 for identical consecutive summaries.

## Tasks

| Task ID | Emails | Difficulty | Description |
|---------|--------|------------|-------------|
| `easy_triage` | 5 | Easy | Clear-cut emails with obvious signals |
| `medium_triage` | 10 | Medium | Mixed difficulty, requires careful reading |
| `hard_triage` | 15 | Hard | Reply chains, phishing, competing urgency cues |

## Setup & Usage

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn email_triage_env.server.app:app --host 0.0.0.0 --port 7860

# Test health
curl http://localhost:7860/health

# Reset with a task
curl -X POST http://localhost:7860/reset \
  -H 'Content-Type: application/json' \
  -d '{"task_id": "easy_triage"}'

# Submit a triage action
curl -X POST http://localhost:7860/step \
  -H 'Content-Type: application/json' \
  -d '{"category":"spam","priority":5,"department":"trash","summary":"Nigerian prince scam email"}'
```

### Docker

```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

### Run Inference (baseline agent)

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct
export HF_TOKEN=your_token_here
export ENV_URL=http://localhost:7860

python inference.py
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_BASE_URL` | Yes | LLM API endpoint |
| `MODEL_NAME` | Yes | Model identifier |
| `HF_TOKEN` | Yes | HuggingFace / API key |
| `ENV_URL` | No | Environment server URL (default: `http://localhost:7860`) |

## Expected Baseline Scores

Approximate scores with a frontier model (varies by model):

| Task | Expected Score |
|------|---------------|
| `easy_triage` | ~0.80–0.90 |
| `medium_triage` | ~0.60–0.70 |
| `hard_triage` | ~0.40–0.55 |

## Project Structure

```
├── Dockerfile                        # Container definition
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Package config
├── openenv.yaml                      # OpenEnv manifest
├── inference.py                      # Baseline inference script
├── README.md                         # This file
└── email_triage_env/
    ├── __init__.py                   # Package exports
    ├── models.py                     # Pydantic Action/Observation/State
    ├── email_generator.py            # 40+ email templates with ground truth
    ├── tasks.py                      # Task definitions & graders
    ├── client.py                     # HTTP client
    └── server/
        ├── __init__.py
        ├── environment.py            # Core step/reset/state logic
        └── app.py                    # FastAPI server
```

## License

MIT
