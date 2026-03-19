"""Post messages to Slack via webhook or Bot token (chat.postMessage)."""
import json
import urllib.error
import urllib.request
from typing import Any

import config

# Google Slides edit URL for a Drive file id
DEMO_URL_TEMPLATE = "https://docs.google.com/presentation/d/{file_id}/edit"


def _post_via_webhook(text: str, attachments: list | None = None, blocks: list | None = None) -> str | None:
    """POST to SLACK_WEBHOOK_URL. Returns None on success, error string on failure."""
    url = config.SLACK_WEBHOOK_URL
    if not url:
        return "SLACK_WEBHOOK_URL is not set."
    
    payload: dict[str, Any] = {"text": text}
    if attachments:
        payload["attachments"] = attachments
    if blocks:
        payload["blocks"] = blocks
        
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            if body != "ok":
                return f"Slack webhook returned: {body}"
            return None
    except urllib.error.HTTPError as e:
        return f"Slack webhook HTTP error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return f"Slack webhook error: {e.reason}"
    except Exception as e:
        return f"Slack webhook error: {e}"


def _post_via_api(channel_id: str, text: str, attachments: list | None = None, blocks: list | None = None) -> str | None:
    """Post via Slack Web API chat.postMessage. Returns None on success, error string on failure."""
    token = config.SLACK_BOT_TOKEN
    if not token or not channel_id:
        return "SLACK_BOT_TOKEN and SLACK_CHANNEL_ID must be set."
    url = "https://slack.com/api/chat.postMessage"
    
    payload: dict[str, Any] = {"channel": channel_id, "text": text}
    if attachments:
        payload["attachments"] = attachments
    if blocks:
        payload["blocks"] = blocks
        
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            out = json.loads(resp.read().decode())
            if not out.get("ok"):
                return f"Slack API error: {out.get('error', 'unknown')}"
            return None
    except urllib.error.HTTPError as e:
        return f"Slack API HTTP error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return f"Slack API error: {e.reason}"
    except Exception as e:
        return f"Slack API error: {e}"


def post_demo_message(demo_file_id: str, sprint_number: int) -> str | None:
    """Post the standard demo announcement to the team channel. The phrase 'Integration Team Sprint N Demo' is a link to the demo. Returns None on success, error string on failure."""
    url = DEMO_URL_TEMPLATE.format(file_id=demo_file_id)
    # Slack mrkdwn: <url|text> shows as clickable "text" linking to url
    link_text = f"Integration Team Sprint {sprint_number} Demo"
    text = f"Hi team, here are the demo slides for our <{url}|{link_text}>."
    
    attachments = [
        {
            "color": "#e01563",
            "title": f"Sprint {sprint_number} Demo 🚀",
            "title_link": url,
            "text": "Feel free to add any items you worked on during the sprint to these slides so we can review them.",
            "footer": "Integration Team Bot",
        }
    ]
    
    if config.SLACK_WEBHOOK_URL:
        return _post_via_webhook(text, attachments=attachments)
    if config.SLACK_BOT_TOKEN and config.SLACK_CHANNEL_ID:
        return _post_via_api(config.SLACK_CHANNEL_ID, text, attachments=attachments)
    return "Slack is not configured: set SLACK_WEBHOOK_URL or (SLACK_BOT_TOKEN and SLACK_CHANNEL_ID) in .env."
