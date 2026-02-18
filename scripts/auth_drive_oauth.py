"""One-time OAuth for Google Drive (your account). Run this to create token_drive.json.

Before running:
  1. Create OAuth 2.0 Client ID in GCP Console (Desktop app).
  2. Download the JSON and save as credentials_drive_oauth.json in the project root.
  3. In .env set DRIVE_USE_OAUTH=true and optionally:
     GOOGLE_DRIVE_OAUTH_CREDENTIALS=./credentials_drive_oauth.json
     GOOGLE_DRIVE_TOKEN_PATH=./token_drive.json

Then run from project root: .venv/bin/python scripts/auth_drive_oauth.py
"""
import os
import sys
from pathlib import Path

# Project root (parent of scripts/)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv(project_root / ".env")

# Defaults so script works with minimal .env
os.environ.setdefault("DRIVE_USE_OAUTH", "true")
os.environ.setdefault("GOOGLE_DRIVE_TOKEN_PATH", str(project_root / "token_drive.json"))
os.environ.setdefault(
    "GOOGLE_DRIVE_OAUTH_CREDENTIALS",
    str(project_root / "credentials_drive_oauth.json"),
)

# Import after env is set so config sees it
from src.drive.client import get_drive_service

if __name__ == "__main__":
    print("Opening browser for Google sign-in (one-time). Use the account that owns the Drive folders.")
    get_drive_service()
    print("Token saved. Run the agent with DRIVE_USE_OAUTH=true in .env.")
