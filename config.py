"""Configuration for sprint demo automation. Keys and IDs are loaded from .env only."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (all keys and folder IDs belong in .env)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

# Google Drive folder IDs — set in .env only (no defaults)
TEAM_DEMOS_FOLDER_ID = os.getenv("TEAM_DEMOS_FOLDER_ID", "")
PRESENT_FOLDER_ID = os.getenv("PRESENT_FOLDER_ID", "")
OLD_FOLDER_ID = os.getenv("OLD_FOLDER_ID", "")

# Template name pattern (partial match in Team demos root)
TEMPLATE_NAME_PATTERN = os.getenv(
    "TEMPLATE_NAME_PATTERN",
    "TEMPLATE for Integration Team Sprint",
)
# Demo file name pattern: "Integration Team Sprint N Demo"
DEMO_NAME_PREFIX = "Integration Team Sprint "
DEMO_NAME_SUFFIX = " Demo"

# Default sprint number when present/ and old/ are empty (first run)
DEFAULT_SPRINT_NUMBER = int(os.getenv("DEFAULT_SPRINT_NUMBER", "305"))

# Service account JSON path — set in .env (for cron/unattended runs)
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# Use OAuth (your account) for Drive instead of service account (avoids 0 MB quota).
# Set DRIVE_USE_OAUTH=true and run scripts/auth_drive_oauth.py once to create the token.
DRIVE_USE_OAUTH = os.getenv("DRIVE_USE_OAUTH", "").strip().lower() in ("1", "true", "yes")
GOOGLE_DRIVE_OAUTH_CREDENTIALS = os.getenv("GOOGLE_DRIVE_OAUTH_CREDENTIALS", "")  # path to client secret JSON
GOOGLE_DRIVE_TOKEN_PATH = os.getenv("GOOGLE_DRIVE_TOKEN_PATH", "")  # path to token.json (created by auth script)

# LLM for the agent: "openai", "gemini", or "deepseek". Set in .env.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()

# OpenAI — set in .env when LLM_PROVIDER=openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# DeepSeek — set in .env when LLM_PROVIDER=deepseek (OpenAI-compatible API)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Gemini (Google AI) — set GOOGLE_API_KEY or GEMINI_API_KEY in .env when LLM_PROVIDER=gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
