"""Drive API operations exposed as LangChain tools. Use create_drive_tools(service) to get tools bound to a Drive service."""
import re
from typing import Optional

from langchain_core.tools import tool

import config


def create_drive_tools(service, slides_service=None):
    """Create LangChain tools that use the given Drive API service. Optionally pass slides_service from get_slides_service() to enable updating the first slide sprint number."""
    drive = service

    @tool
    def list_folder(folder_id: str, name_contains: str = "") -> str:
        """List files in a Google Drive folder. Optional name_contains filters by partial name match."""
        if not folder_id:
            return "Error: folder_id is required."
        q = f"'{folder_id}' in parents and trashed = false"
        if name_contains:
            q += f" and name contains '{name_contains}'"
        try:
            results = (
                drive.files()
                .list(
                    q=q,
                    pageSize=100,
                    fields="files(id, name, mimeType)",
                )
                .execute()
            )
            files = results.get("files", [])
            if not files:
                return "No files found."
            lines = [f"- {f['name']} (id: {f['id']})" for f in files]
            return "\n".join(lines)
        except Exception as e:
            return f"Error listing folder: {e}"

    _demo_pattern = re.compile(
        re.escape(config.DEMO_NAME_PREFIX) + r"(\d+)" + re.escape(config.DEMO_NAME_SUFFIX)
    )

    def _parse_sprint_from_name(name: str) -> Optional[int]:
        m = _demo_pattern.search(name)
        return int(m.group(1)) if m else None

    @tool
    def get_latest_sprint_number() -> str:
        """List present and old folders, find all 'Integration Team Sprint N Demo' files, and return the latest sprint number N and the file id of the current demo in present (if any). Returns a short summary like 'Latest sprint: 305, current present file id: abc123' or 'Latest sprint: 305, no file in present'."""
        present_id = config.PRESENT_FOLDER_ID
        old_id = config.OLD_FOLDER_ID
        if not present_id or not old_id:
            return (
                "Error: PRESENT_FOLDER_ID and OLD_FOLDER_ID must be set in .env."
            )
        max_sprint = None
        present_file_id = None
        try:
            for folder_id, folder_label in [(present_id, "present"), (old_id, "old")]:
                results = (
                    drive.files()
                    .list(
                        q=f"'{folder_id}' in parents and trashed = false",
                        pageSize=50,
                        fields="files(id, name)",
                    )
                    .execute()
                )
                for f in results.get("files", []):
                    n = _parse_sprint_from_name(f["name"])
                    if n is not None:
                        if max_sprint is None or n > max_sprint:
                            max_sprint = n
                        if folder_label == "present":
                            present_file_id = f["id"]
            if max_sprint is None:
                max_sprint = config.DEFAULT_SPRINT_NUMBER
                return (
                    f"No existing demo files found. Using default sprint number: {max_sprint}. "
                    "No file in present."
                )
            if present_file_id:
                return f"Latest sprint: {max_sprint}, current present file id: {present_file_id}"
            return f"Latest sprint: {max_sprint}, no file in present"
        except Exception as e:
            return f"Error getting latest sprint: {e}"

    @tool
    def find_template() -> str:
        """Find the template file in the Team demos folder (name starts with TEMPLATE_NAME_PATTERN). Returns the file id or an error message."""
        folder_id = config.TEAM_DEMOS_FOLDER_ID
        pattern = config.TEMPLATE_NAME_PATTERN
        if not folder_id:
            return "Error: TEAM_DEMOS_FOLDER_ID must be set in .env."
        try:
            results = (
                drive.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false and name contains '{pattern}'",
                    pageSize=10,
                    fields="files(id, name)",
                )
                .execute()
            )
            files = results.get("files", [])
            if not files:
                return f"Error: No template found in Team demos (looking for name containing '{pattern}')."
            # Prefer exact "TEMPLATE for Integration Team Sprint ..." match
            for f in files:
                if pattern in f["name"]:
                    return f"Template id: {f['id']} (name: {f['name']})"
            return f"Error: No template found (pattern: {pattern})."
        except Exception as e:
            return f"Error finding template: {e}"

    @tool
    def copy_file(file_id: str, new_parent_id: str, new_name: str) -> str:
        """Copy a Drive file to a new folder with a new name. Use for copying the template into present/."""
        if not file_id or not new_parent_id or not new_name:
            return "Error: file_id, new_parent_id, and new_name are required."
        try:
            body = {"name": new_name, "parents": [new_parent_id]}
            new_file = drive.files().copy(fileId=file_id, body=body).execute()
            return f"Created copy with id: {new_file['id']}, name: {new_file.get('name', new_name)}"
        except Exception as e:
            return f"Error copying file: {e}"

    @tool
    def move_file(file_id: str, new_parent_id: str) -> str:
        """Move a Drive file to another folder (e.g. move previous demo from present to old)."""
        if not file_id or not new_parent_id:
            return "Error: file_id and new_parent_id are required."
        try:
            file_meta = drive.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(file_meta.get("parents", []))
            drive.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=previous_parents,
            ).execute()
            return f"Moved file {file_id} to folder {new_parent_id}."
        except Exception as e:
            return f"Error moving file: {e}"

    tools_list = [
        list_folder,
        get_latest_sprint_number,
        find_template,
        copy_file,
        move_file,
    ]

    if slides_service:

        @tool
        def update_first_slide_sprint_number(file_id: str, sprint_number: int) -> str:
            """Replace 'xxx' with the sprint number in the first slide of a Google Slides file. Call this after copy_file with the new file id and the sprint number (N+1). The template has 'xxx' as placeholder; this updates it to e.g. 306."""
            if not file_id or sprint_number is None:
                return "Error: file_id and sprint_number are required."
            try:
                slides = slides_service
                pres = slides.presentations().get(presentationId=file_id).execute()
                slide_ids = [s["objectId"] for s in pres.get("slides", [])]
                if not slide_ids:
                    return "Error: presentation has no slides."
                first_slide_id = slide_ids[0]
                body = {
                    "requests": [
                        {
                            "replaceAllText": {
                                "containsText": {"text": "xxx", "matchCase": False},
                                "replaceText": str(sprint_number),
                                "pageObjectIds": [first_slide_id],
                            }
                        }
                    ]
                }
                slides.presentations().batchUpdate(
                    presentationId=file_id, body=body
                ).execute()
                return f"Replaced 'xxx' with '{sprint_number}' on the first slide (presentation {file_id})."
            except Exception as e:
                return f"Error updating slide: {e}"

        tools_list.append(update_first_slide_sprint_number)

    return tools_list
