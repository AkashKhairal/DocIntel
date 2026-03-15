"""Google Drive webhook handler for push notifications."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Request, Response

from config.settings import get_settings, CONFIG_DIR

logger = logging.getLogger(__name__)

router = APIRouter()

PAGE_TOKEN_FILE = CONFIG_DIR / "page_token.json"


def _load_page_token() -> str | None:
    """Load the saved page token from disk."""
    if PAGE_TOKEN_FILE.exists():
        try:
            data = json.loads(PAGE_TOKEN_FILE.read_text())
            return data.get("page_token")
        except Exception:
            return None
    return None


def _save_page_token(token: str) -> None:
    """Persist the page token to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PAGE_TOKEN_FILE.write_text(json.dumps({"page_token": token}))


@router.post("/drive/webhook")
async def drive_webhook(request: Request):
    """Receive Google Drive push notification and dispatch processing tasks.

    Google sends two types of notifications:
    - sync: initial verification (respond 200)
    - update: actual change notification
    """
    # Google Drive sends notification metadata in headers
    channel_id = request.headers.get("X-Goog-Channel-ID", "")
    resource_state = request.headers.get("X-Goog-Resource-State", "")

    logger.info(f"Webhook received: state={resource_state}, channel={channel_id}")

    # Sync message — just acknowledge
    if resource_state == "sync":
        return Response(status_code=200)

    # For change notifications, fetch actual changes
    if resource_state == "update":
        page_token = _load_page_token()
        if not page_token:
            logger.warning("No page token saved — cannot fetch changes. Run initial sync first.")
            return Response(status_code=200)

        try:
            from drive.client import get_changes
            from workers.tasks import process_file_task, delete_file_vectors_task

            changes, new_token = get_changes(page_token)
            _save_page_token(new_token)

            for change in changes:
                file_id = change.get("fileId")
                removed = change.get("removed", False)
                file_info = change.get("file", {})
                trashed = file_info.get("trashed", False)

                if not file_id:
                    continue

                if removed or trashed:
                    logger.info(f"File removed/trashed: {file_id}")
                    delete_file_vectors_task.delay(file_id)
                else:
                    logger.info(f"File changed: {file_id} ({file_info.get('name', 'unknown')})")
                    process_file_task.delay(file_id)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)

    return Response(status_code=200)
