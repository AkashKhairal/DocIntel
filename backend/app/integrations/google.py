import json
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.config import get_settings

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def _client_config():
    settings = get_settings()
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def get_authorize_url(state: str | None = None):
    settings = get_settings()
    flow = Flow.from_client_config(
        client_config=_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.google_oauth_redirect_uri,
    )
    auth_url, generated_state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return auth_url, generated_state


def exchange_code(code: str) -> dict:
    settings = get_settings()
    flow = Flow.from_client_config(
        client_config=_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.google_oauth_redirect_uri,
    )
    flow.fetch_token(code=code)

    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "expiry": creds.expiry,
        "scope": creds.scopes and " ".join(sorted(creds.scopes)) or "",
    }


def refresh_access_token(refresh_token: str) -> dict:
    settings = get_settings()
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
    request = Request()
    creds.refresh(request)
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "expiry": creds.expiry,
        "scope": creds.scopes and " ".join(sorted(creds.scopes)) or "",
    }


def build_drive_service(access_token: str, refresh_token: str, expiry: datetime):
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=get_settings().google_client_id,
        client_secret=get_settings().google_client_secret,
        scopes=SCOPES,
    )

    updated = False
    if creds.expired and creds.refresh_token:
        request = Request()
        creds.refresh(request)
        updated = True

    service = build("drive", "v3", credentials=creds)
    return service, creds, updated
