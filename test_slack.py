import urllib.request
import json
import config

token = config.SLACK_BOT_TOKEN
channel_id = config.SLACK_CHANNEL_ID

print(f"Token: {token[:10]}...")
print(f"Channel: {channel_id}")

url = "https://slack.com/api/chat.postMessage"
payload = {"channel": channel_id, "text": "Testing Slack Integration Direct"}
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
        print("Response Code:", resp.getcode())
        out = json.loads(resp.read().decode())
        print("Response Body:", json.dumps(out, indent=2))
except Exception as e:
    print("Exception:", e)
