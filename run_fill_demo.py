"""CLI entry point for filling sprint demo slides with Jira ticket content.

Reads a JSON payload from stdin and writes a JSON result to stdout.

Input schema:
    {
        "user_name": "Kasem Alem",
        "sprint_number": 313,
        "tickets": [
            {
                "key": "KONFLUX-123",
                "summary": "Fix snapshot creation race condition",
                "problem": "Concurrent snapshot creation caused data overwrites.",
                "solution": "Added a mutex lock around the snapshot creation path.",
                "benefits": "Eliminates data loss under high concurrency.",
                "downsides": "None"
            }
        ]
    }

Output schema (always valid JSON on stdout):
    {"status": "ok",           "slides_added": 1, "deck_url": "...", "message": "..."}
    {"status": "already_filled","message": "...", "deck_url": "..."}
    {"status": "error",        "message": "..."}

Exit codes: 0 = ok or already_filled, 1 = error.
"""
import json
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402 — must be after sys.path insert
from src.drive import get_drive_service, get_slides_service  # noqa: E402
from src.drive.fill_tools import add_tickets_to_deck  # noqa: E402


def _fail(message: str) -> None:
    print(json.dumps({"status": "error", "message": message}))
    sys.exit(1)


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        _fail(f"Invalid JSON input: {e}")
        return

    user_name = payload.get("user_name", "").strip()
    sprint_number = payload.get("sprint_number")
    tickets = payload.get("tickets", [])

    if not user_name:
        _fail("user_name is required in the input payload.")
        return
    if not isinstance(sprint_number, int) or sprint_number <= 0:
        _fail("sprint_number must be a positive integer.")
        return
    if not tickets:
        _fail("tickets list is empty — nothing to add.")
        return

    required_ticket_fields = {"key", "summary", "problem", "solution", "benefits", "downsides"}
    for i, ticket in enumerate(tickets):
        missing = required_ticket_fields - set(ticket.keys())
        if missing:
            _fail(f"Ticket at index {i} is missing fields: {sorted(missing)}")
            return

    try:
        drive_svc = get_drive_service()
        slides_svc = get_slides_service()
    except Exception as e:
        _fail(f"Failed to initialise Google Drive/Slides: {e}")
        return

    result = add_tickets_to_deck(
        drive_svc=drive_svc,
        slides_svc=slides_svc,
        sprint_number=sprint_number,
        user_name=user_name,
        tickets=tickets,
    )

    print(json.dumps(result))
    sys.exit(0 if result["status"] in ("ok", "already_filled") else 1)


if __name__ == "__main__":
    main()
