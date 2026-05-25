"""Check which ticket keys are already filled in the sprint demo deck for a given user.

Reads a JSON payload from stdin and writes a JSON result to stdout.

Input schema:
    {
        "user_name": "Kasem Alem",
        "sprint_number": 313,
        "ticket_keys": ["STONEINTG-1642", "STONEINTG-1641"]
    }

Output schema (always valid JSON on stdout):
    {
        "status": "ok",
        "already_in_deck": ["STONEINTG-1642"],
        "missing": ["STONEINTG-1641"],
        "deck_url": "https://..."
    }
    {"status": "error", "message": "..."}

Exit codes: 0 = ok, 1 = error.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
from src.drive import get_drive_service, get_slides_service  # noqa: E402
from src.drive.fill_tools import find_deck_in_present, get_user_existing_ticket_keys  # noqa: E402

SLIDES_URL_TEMPLATE = "https://docs.google.com/presentation/d/{file_id}/edit"


def _fail(message: str) -> None:
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        _fail(f"Invalid JSON input: {e}")
        return

    user_name = payload.get("user_name", "").strip()
    sprint_number = payload.get("sprint_number")
    ticket_keys = payload.get("ticket_keys", [])

    if not user_name:
        _fail("user_name is required.")
        return
    if not isinstance(sprint_number, int) or sprint_number <= 0:
        _fail("sprint_number must be a positive integer.")
        return
    if not ticket_keys:
        _fail("ticket_keys list is empty.")
        return

    try:
        drive_svc = get_drive_service()
        slides_svc = get_slides_service()
    except Exception as e:
        _fail(f"Failed to initialise Google Drive/Slides: {e}")
        return

    try:
        presentation_id, deck_url = find_deck_in_present(drive_svc, sprint_number)
    except ValueError as e:
        _fail(str(e))
        return

    try:
        existing = get_user_existing_ticket_keys(slides_svc, presentation_id, user_name)
    except ValueError as e:
        _fail(str(e))
        return

    already = [k for k in ticket_keys if k in existing]
    missing = [k for k in ticket_keys if k not in existing]

    print(json.dumps({
        "status": "ok",
        "already_in_deck": already,
        "missing": missing,
        "deck_url": deck_url,
    }))


if __name__ == "__main__":
    main()
