FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY email_triage_env/ ./email_triage_env/

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# HF Spaces uses port 7860
ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "email_triage_env.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
