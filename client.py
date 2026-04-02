"""Wrapper for root-level client.py validation checks."""
from email_triage_env.client import EmailTriageClient

# Export for openenv tools
HTTPEnvClient = EmailTriageClient
