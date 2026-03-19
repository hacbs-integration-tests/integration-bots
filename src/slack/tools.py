"""Slack tools for the sprint demo agent."""
from langchain_core.tools import tool

import config

from src.slack.client import post_demo_message


def create_slack_tools():
    """Return a list of Slack tools if Slack is configured; otherwise empty list."""
    if not config.SLACK_WEBHOOK_URL and not (config.SLACK_BOT_TOKEN and config.SLACK_CHANNEL_ID):
        return []

    @tool
    def post_slack_demo_link(demo_file_id: str, sprint_number: int) -> str:
        """Post a message to the team Slack channel with a link to the new demo slides. Call this after creating the new demo (after copy_file and update_first_slide_sprint_number). Pass the new file id from copy_file and the sprint number (N+1). The message says 'Hi team, here are the demo slides for our Integration Team Sprint X Demo, feel free to add any items you worked on during the sprint' with the demo title linking to the slides."""
        if not demo_file_id or sprint_number is None:
            return "Error: demo_file_id and sprint_number are required."
        err = post_demo_message(demo_file_id, sprint_number)
        if err:
            return f"Error posting to Slack: {err}"
        return f"Posted demo link (sprint {sprint_number}) to the team Slack channel."

    return [post_slack_demo_link]
