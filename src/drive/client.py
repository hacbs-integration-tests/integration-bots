"""Google Drive API client: OAuth (user) or service account credentials."""
from pathlib import Path

from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    GOOGLE_APPLICATION_CREDENTIALS,
    DRIVE_USE_OAUTH,
    GOOGLE_DRIVE_OAUTH_CREDENTIALS,
    GOOGLE_DRIVE_TOKEN_PATH,
)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/presentations",
]


def _oauth_creds():
    """Load or refresh OAuth credentials from token file and client secret."""
    token_path = Path(GOOGLE_DRIVE_TOKEN_PATH).expanduser().resolve()
    creds_path = Path(GOOGLE_DRIVE_OAUTH_CREDENTIALS).expanduser().resolve()
    if not creds_path.is_file():
        raise FileNotFoundError(
            f"OAuth credentials file not found: {creds_path}. "
            "Download from GCP Console (APIs & Services > Credentials > OAuth 2.0 Client ID)."
        )
    creds = None
    if token_path.is_file():
        creds = OAuthCredentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return creds


def get_drive_service():
    """Build and return a Drive API v3 service. Uses OAuth if DRIVE_USE_OAUTH=true, else service account."""
    if DRIVE_USE_OAUTH:
        if not GOOGLE_DRIVE_OAUTH_CREDENTIALS or not GOOGLE_DRIVE_TOKEN_PATH:
            raise ValueError(
                "When DRIVE_USE_OAUTH=true, set GOOGLE_DRIVE_OAUTH_CREDENTIALS and GOOGLE_DRIVE_TOKEN_PATH in .env. "
                "Run scripts/auth_drive_oauth.py once to create the token."
            )
        creds = _oauth_creds()
    else:
        if not GOOGLE_APPLICATION_CREDENTIALS:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS must be set in .env to the path of your service account JSON key."
            )
        creds = ServiceAccountCredentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS,
            scopes=SCOPES,
        )
    return build("drive", "v3", credentials=creds)


def get_slides_service():
    """Build and return a Slides API v1 service (same credentials as Drive). Enable Google Slides API in GCP."""
    if DRIVE_USE_OAUTH:
        if not GOOGLE_DRIVE_OAUTH_CREDENTIALS or not GOOGLE_DRIVE_TOKEN_PATH:
            raise ValueError(
                "When DRIVE_USE_OAUTH=true, set GOOGLE_DRIVE_OAUTH_CREDENTIALS and GOOGLE_DRIVE_TOKEN_PATH in .env."
            )
        creds = _oauth_creds()
    else:
        if not GOOGLE_APPLICATION_CREDENTIALS:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS must be set in .env to the path of your service account JSON key."
            )
        creds = ServiceAccountCredentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS,
            scopes=SCOPES,
        )
    return build("slides", "v1", credentials=creds)
