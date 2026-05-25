"""Google Slides operations for filling sprint demo slides with Jira ticket content."""
import re
from typing import Optional

import config

# Matches "Integration Team Sprint 313 Demo" → sprint number 313
_DEMO_PATTERN = re.compile(
    re.escape(config.DEMO_NAME_PREFIX) + r"(\d+)" + re.escape(config.DEMO_NAME_SUFFIX)
)

JIRA_BASE_URL = "https://issues.redhat.com/browse"
SLIDES_URL_TEMPLATE = "https://docs.google.com/presentation/d/{file_id}/edit"

# Slide index of the template slide (0-based); slide 2 in the UI = index 1
TEMPLATE_SLIDE_INDEX = 1


def find_deck_in_present(drive_svc, sprint_number: int) -> tuple[str, str]:
    """Find the sprint demo deck in the present folder matching sprint_number.

    Returns (file_id, deck_url).
    Raises ValueError with a user-friendly message on any problem.
    """
    folder_id = config.PRESENT_FOLDER_ID
    if not folder_id:
        raise ValueError("PRESENT_FOLDER_ID is not set in .env.")

    try:
        results = (
            drive_svc.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                pageSize=50,
                fields="files(id, name)",
            )
            .execute()
        )
    except Exception as e:
        raise ValueError(f"Failed to list present folder: {e}") from e

    files = results.get("files", [])
    if not files:
        raise ValueError(
            "No deck found in the present folder. "
            "Run the main sprint demo bot first to create the deck."
        )

    for f in files:
        m = _DEMO_PATTERN.search(f["name"])
        if m is None:
            continue
        deck_sprint = int(m.group(1))
        if deck_sprint == sprint_number:
            file_id = f["id"]
            return file_id, SLIDES_URL_TEMPLATE.format(file_id=file_id)
        if deck_sprint < sprint_number:
            raise ValueError(
                f"The deck in present is for sprint {deck_sprint}, "
                f"but the current active sprint is {sprint_number}. "
                "The deck is outdated — run the main sprint demo bot to create a new one."
            )

    raise ValueError(
        f"No deck for sprint {sprint_number} found in the present folder. "
        "Run the main sprint demo bot first to create the deck."
    )


_TICKET_KEY_RE = re.compile(r'\b[A-Z]+-\d+\b')


def get_user_existing_ticket_keys(slides_svc, presentation_id: str, user_name: str) -> set[str]:
    """Return the set of ticket keys that already have a slide for user_name in the deck."""
    try:
        pres = slides_svc.presentations().get(presentationId=presentation_id).execute()
    except Exception as e:
        raise ValueError(f"Failed to read presentation: {e}") from e

    existing = set()
    for slide in pres.get("slides", []):
        texts = []
        for element in slide.get("pageElements", []):
            shape = element.get("shape", {})
            for te in shape.get("text", {}).get("textElements", []):
                if "textRun" in te:
                    texts.append(te["textRun"].get("content", ""))
        full_text = " ".join(texts)
        if user_name.lower() not in full_text.lower():
            continue
        existing.update(_TICKET_KEY_RE.findall(full_text))
    return existing


def _get_slide_object_id(slides_svc, presentation_id: str, index: int) -> str:
    """Return the objectId of the slide at the given 0-based index."""
    try:
        pres = slides_svc.presentations().get(presentationId=presentation_id).execute()
    except Exception as e:
        raise ValueError(f"Failed to read presentation: {e}") from e

    slides = pres.get("slides", [])
    if len(slides) <= index:
        raise ValueError(
            f"Presentation has only {len(slides)} slide(s); "
            f"cannot access slide at index {index}."
        )
    return slides[index]["objectId"]


def duplicate_slide(slides_svc, presentation_id: str, slide_object_id: str) -> str:
    """Duplicate the given slide and return the new slide's objectId."""
    try:
        response = (
            slides_svc.presentations()
            .batchUpdate(
                presentationId=presentation_id,
                body={"requests": [{"duplicateObject": {"objectId": slide_object_id}}]},
            )
            .execute()
        )
    except Exception as e:
        raise ValueError(f"Failed to duplicate slide: {e}") from e

    new_slide_id = response["replies"][0]["duplicateObject"]["objectId"]
    return new_slide_id


def _replace_all_text(slides_svc, presentation_id: str, slide_id: str, replacements: dict) -> None:
    """Replace placeholder text strings in a single slide."""
    requests = [
        {
            "replaceAllText": {
                "containsText": {"text": placeholder, "matchCase": True},
                "replaceText": value,
                "pageObjectIds": [slide_id],
            }
        }
        for placeholder, value in replacements.items()
    ]
    try:
        slides_svc.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()
    except Exception as e:
        raise ValueError(f"Failed to replace text in slide: {e}") from e


def _restyle_content_fields(
    slides_svc, presentation_id: str, slide_id: str, content_values: list[str]
) -> None:
    """Set bold=False and fontSize=13pt on text runs that match any of the filled content values."""
    try:
        pres = slides_svc.presentations().get(presentationId=presentation_id).execute()
    except Exception:
        return

    target_slide = next(
        (s for s in pres.get("slides", []) if s["objectId"] == slide_id), None
    )
    if target_slide is None:
        return

    normalized = {v.strip() for v in content_values if v}
    requests = []

    for element in target_slide.get("pageElements", []):
        if "shape" not in element:
            continue
        for te in element["shape"].get("text", {}).get("textElements", []):
            if "textRun" not in te:
                continue
            run_text = te["textRun"].get("content", "")
            if run_text.strip("\n") not in normalized:
                continue
            start = te.get("startIndex", 0)
            end = te.get("endIndex", start + len(run_text))
            requests.append({
                "updateTextStyle": {
                    "objectId": element["objectId"],
                    "style": {
                        "bold": False,
                        "fontSize": {"magnitude": 13, "unit": "PT"},
                    },
                    "textRange": {
                        "type": "FIXED_RANGE",
                        "startIndex": start,
                        "endIndex": end,
                    },
                    "fields": "bold,fontSize",
                }
            })

    if requests:
        try:
            slides_svc.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests},
            ).execute()
        except Exception as e:
            raise ValueError(f"Failed to restyle content fields: {e}") from e


def _update_ticket_hyperlink(
    slides_svc, presentation_id: str, slide_id: str, ticket_key: str, ticket_url: str
) -> None:
    """Find the ticket key text in the slide and update its hyperlink URL."""
    try:
        pres = slides_svc.presentations().get(presentationId=presentation_id).execute()
    except Exception as e:
        raise ValueError(f"Failed to read presentation for hyperlink update: {e}") from e

    target_slide = next(
        (s for s in pres.get("slides", []) if s["objectId"] == slide_id), None
    )
    if target_slide is None:
        raise ValueError(f"Slide {slide_id} not found after duplication.")

    for element in target_slide.get("pageElements", []):
        if "shape" not in element:
            continue
        text_obj = element["shape"].get("text", {})
        for te in text_obj.get("textElements", []):
            if "textRun" not in te:
                continue
            content = te["textRun"].get("content", "")
            if ticket_key not in content:
                continue

            rel_pos = content.index(ticket_key)
            abs_start = te.get("startIndex", 0) + rel_pos
            abs_end = abs_start + len(ticket_key)

            try:
                slides_svc.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={
                        "requests": [
                            {
                                "updateTextStyle": {
                                    "objectId": element["objectId"],
                                    "style": {"link": {"url": ticket_url}},
                                    "textRange": {
                                        "type": "FIXED_RANGE",
                                        "startIndex": abs_start,
                                        "endIndex": abs_end,
                                    },
                                    "fields": "link",
                                }
                            }
                        ]
                    },
                ).execute()
            except Exception as e:
                raise ValueError(f"Failed to update hyperlink: {e}") from e
            return


def fill_ticket_slide(
    slides_svc,
    presentation_id: str,
    new_slide_id: str,
    user_name: str,
    ticket_key: str,
    ticket_summary: str,
    problem: str,
    solution: str,
    benefits: str,
    downsides: str,
) -> None:
    """Fill all placeholders in a duplicated slide for one Jira ticket.

    Replaces text placeholders then updates the ticket key hyperlink.
    """
    ticket_url = f"{JIRA_BASE_URL}/{ticket_key}"

    replacements = {
        "<Name>": user_name,
        "STONEINTG-XXXX": ticket_key,
        "Title": ticket_summary,
        "<PROBLEM>": problem,
        "<SOLUTION>": solution,
        "<BENEFITS>": benefits,
        "<DOWNSIDES>": downsides,
    }
    _replace_all_text(slides_svc, presentation_id, new_slide_id, replacements)
    _update_ticket_hyperlink(slides_svc, presentation_id, new_slide_id, ticket_key, ticket_url)
    _restyle_content_fields(
        slides_svc, presentation_id, new_slide_id,
        [problem, solution, benefits, downsides],
    )


def add_tickets_to_deck(
    drive_svc,
    slides_svc,
    sprint_number: int,
    user_name: str,
    tickets: list[dict],
) -> dict:
    """Top-level function: find deck, validate, and add one slide per ticket.

    Each ticket dict must have: key, summary, problem, solution, benefits, downsides.
    Returns a result dict with status, message, slides_added, and deck_url.
    """
    # Find the deck
    try:
        presentation_id, deck_url = find_deck_in_present(drive_svc, sprint_number)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    # Determine which tickets are already in the deck for this user
    try:
        existing_keys = get_user_existing_ticket_keys(slides_svc, presentation_id, user_name)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    tickets_to_add = [t for t in tickets if t["key"] not in existing_keys]
    skipped_keys = [t["key"] for t in tickets if t["key"] in existing_keys]

    if not tickets_to_add:
        return {
            "status": "already_filled",
            "message": (
                f"All tickets for {user_name} are already in the Sprint {sprint_number} deck. "
                "If you want to re-fill, remove your existing slides first."
            ),
            "deck_url": deck_url,
        }

    # Get the template slide (slide 2, index 1) objectId
    try:
        template_slide_id = _get_slide_object_id(slides_svc, presentation_id, TEMPLATE_SLIDE_INDEX)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    added = 0
    for ticket in tickets_to_add:
        try:
            new_slide_id = duplicate_slide(slides_svc, presentation_id, template_slide_id)
            fill_ticket_slide(
                slides_svc=slides_svc,
                presentation_id=presentation_id,
                new_slide_id=new_slide_id,
                user_name=user_name,
                ticket_key=ticket["key"],
                ticket_summary=ticket["summary"],
                problem=ticket["problem"],
                solution=ticket["solution"],
                benefits=ticket["benefits"],
                downsides=ticket["downsides"],
            )
            added += 1
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Failed on ticket {ticket.get('key', '?')}: {e}",
                "slides_added": added,
                "deck_url": deck_url,
            }

    skipped_note = f" Skipped {len(skipped_keys)} already present: {', '.join(skipped_keys)}." if skipped_keys else ""
    return {
        "status": "ok",
        "slides_added": added,
        "deck_url": deck_url,
        "message": (
            f"Added {added} slide(s) for {user_name} "
            f"to the Sprint {sprint_number} demo deck.{skipped_note}"
        ),
    }
