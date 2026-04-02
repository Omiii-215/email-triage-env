"""Wrapper script to appease automated OpenEnv CLI validation."""
import sys
import os

# Add the root directory to sys.path so we can import our package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_triage_env.server.app import app

def main():
    import uvicorn
    uvicorn.run("email_triage_env.server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
