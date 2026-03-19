"""Build the sprint-demo LangGraph agent with Drive tools and system prompt."""
import config
from langgraph.prebuilt import create_react_agent

from src.drive import create_drive_tools, get_drive_service, get_slides_service
from src.slack import create_slack_tools


def _get_model():
    """Return the chat model for the configured LLM provider (openai, gemini, or deepseek)."""
    provider = (config.LLM_PROVIDER or "openai").strip().lower()
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = config.GOOGLE_API_KEY or config.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "When LLM_PROVIDER=gemini, set GOOGLE_API_KEY or GEMINI_API_KEY in .env."
            )
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=api_key,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not config.OPENAI_API_KEY:
            raise ValueError("When LLM_PROVIDER=openai, set OPENAI_API_KEY in .env.")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    if provider == "deepseek":
        from langchain_openai import ChatOpenAI

        if not config.DEEPSEEK_API_KEY:
            raise ValueError(
                "When LLM_PROVIDER=deepseek, set DEEPSEEK_API_KEY in .env."
            )
        return ChatOpenAI(
            model="deepseek-chat",
            temperature=0,
            openai_api_key=config.DEEPSEEK_API_KEY,
            openai_api_base="https://api.deepseek.com",
        )
    raise ValueError(
        f"Unknown LLM_PROVIDER={config.LLM_PROVIDER!r}. Use 'openai', 'gemini', or 'deepseek'."
    )

SYSTEM_PROMPT_TEMPLATE = """You automate creating the next Integration Team sprint demo in Google Drive. Follow this procedure exactly:

1. Call get_latest_sprint_number to learn the latest sprint number N and whether there is a current demo file in the present folder.
2. Call find_template to get the template file id.
3. The next demo is for sprint N+1. Copy the template into the present folder with the name "Integration Team Sprint {{N+1}} Demo" using copy_file: use the template id from step 2, new_parent_id = PRESENT_FOLDER_ID below, and new_name = "Integration Team Sprint {{N+1}} Demo".
4. Call update_first_slide_sprint_number with the new file id returned from copy_file in step 3 and sprint_number = N+1. This replaces "xxx" with the sprint number in the first slide (and any "xxx" in the deck).
5. If the post_slack_demo_link tool is available, call it with demo_file_id = the new file id from step 3 and sprint_number = N+1. This posts a message to the team Slack channel with a link to the new demo.
6. If there was a current demo file in present (from step 1), move it to the old folder using move_file: use that file id and new_parent_id = OLD_FOLDER_ID below. If there was no file in present, skip this step.
7. Reply with a short summary: e.g. "Created Integration Team Sprint {{N+1}} Demo in present, updated slide to {{N+1}}, posted link to Slack, and moved the previous demo to old."

Folder IDs (use these in copy_file and move_file):
- PRESENT_FOLDER_ID: {present_folder_id}
- OLD_FOLDER_ID: {old_folder_id}

Use the tool results to extract file ids and the latest sprint number. For copy_file you need: file_id (template id), new_parent_id (PRESENT_FOLDER_ID above), new_name ("Integration Team Sprint X Demo" where X is N+1). After copy_file, use the returned new file id in update_first_slide_sprint_number with sprint_number = N+1. For post_slack_demo_link use that same new file id and sprint_number = N+1. For move_file you need: file_id (previous demo from get_latest_sprint_number), new_parent_id (OLD_FOLDER_ID above).
Do not skip steps. If a tool returns an error, say so and stop."""


def create_graph():
    """Build and return the compiled LangGraph agent. Uses Drive service from config."""
    if not config.PRESENT_FOLDER_ID or not config.OLD_FOLDER_ID:
        raise ValueError("PRESENT_FOLDER_ID and OLD_FOLDER_ID must be set in .env.")

    service = get_drive_service()
    try:
        slides_service = get_slides_service()
    except Exception:
        slides_service = None  # Slides API not configured; first-slide update tool will be omitted
    tools = list(create_drive_tools(service, slides_service=slides_service))
    tools.extend(create_slack_tools())
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        present_folder_id=config.PRESENT_FOLDER_ID,
        old_folder_id=config.OLD_FOLDER_ID,
    )
    model = _get_model()
    agent = create_react_agent(model, tools, prompt=system_prompt)
    return agent
