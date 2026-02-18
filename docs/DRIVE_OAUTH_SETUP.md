# Option A: Use your Google account for Drive (OAuth)

When the service account has 0 MB Drive quota, copies fail with `storageQuotaExceeded`. Using **OAuth** lets the agent use **your** Google account for Drive, so copies use your quota.

Follow these steps once. After that, the agent runs as before.

---

## Step 1: Open Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Select the **same project** as your service account (e.g. **aiagent-449310**).
3. In the top bar, click the project name to confirm.

---

## Step 2: Enable the Drive API (if needed)

1. In the left menu go to **APIs & Services** → **Library**.
2. Search for **Google Drive API**.
3. Open it and click **Enable** if it is not already enabled.

---

## Step 3: Create OAuth 2.0 credentials

1. Go to **APIs & Services** → **Credentials**.
2. Click **+ Create Credentials** → **OAuth client ID**.
3. If asked to configure the consent screen:
   - Choose **External** (or **Internal** if you use Workspace and only your org will use this).
   - Fill in App name (e.g. **Sprint Demo Bot**) and your email as support.
   - Save and continue until back to Create OAuth client ID.
4. Under **Application type** choose **Desktop app**.
5. Set a name (e.g. **Sprint Demo Bot Desktop**).
6. Click **Create**.
7. In the popup, click **Download JSON** (or copy the Client ID and Client Secret if you prefer to paste into a file yourself).
8. Save the file in your **project root** as:
   ```text
   credentials_drive_oauth.json
   ```
   (Rename the downloaded file if needed.) Keep this file private and do not commit it.

---

## Step 4: Add OAuth settings to `.env`

In your project root, open `.env` and add (or uncomment and set):

```env
# Use your account for Drive (avoids service account 0 MB quota)
DRIVE_USE_OAUTH=true
GOOGLE_DRIVE_OAUTH_CREDENTIALS=./credentials_drive_oauth.json
GOOGLE_DRIVE_TOKEN_PATH=./token_drive.json
```

Use full paths if you prefer, e.g.:

```env
GOOGLE_DRIVE_OAUTH_CREDENTIALS=/home/you/integration-bots/credentials_drive_oauth.json
GOOGLE_DRIVE_TOKEN_PATH=/home/you/integration-bots/token_drive.json
```

Leave your existing folder IDs and other vars as they are. You can leave `GOOGLE_APPLICATION_CREDENTIALS` set; it is ignored when `DRIVE_USE_OAUTH=true`.

---

## Step 5: Run the one-time auth script

From the **project root**, with the venv:

```bash
source .env
.venv/bin/python scripts/auth_drive_oauth.py
```

1. A browser window opens and asks you to sign in to Google.
2. Sign in with the **account that owns the Drive folders** (e.g. your work account that has “Team demos”, “present”, “old”).
3. If you see “Google hasn’t verified this app”: click **Advanced** → **Go to Sprint Demo Bot (unsafe)** (or the name you gave). You are only authorizing your own app.
4. Approve the requested Drive access.
5. The script prints **Token saved** and creates `token_drive.json` in the project root.

Do not commit `token_drive.json` or `credentials_drive_oauth.json` (they are already covered by `.gitignore` if you ignore `*.json` or list them).

---

## Step 6: Run the agent

From the project root:

```bash
source .env
.venv/bin/python run_agent.py
```

Drive operations (copy template, move previous demo) will use **your** account and **your** Drive quota.

---

## Summary checklist

| Step | Action |
|------|--------|
| 1 | Open Cloud Console, select project (e.g. aiagent-449310). |
| 2 | Enable Google Drive API. |
| 3 | Create OAuth client (Desktop app), download JSON, save as `credentials_drive_oauth.json` in project root. |
| 4 | In `.env`: `DRIVE_USE_OAUTH=true`, set `GOOGLE_DRIVE_OAUTH_CREDENTIALS` and `GOOGLE_DRIVE_TOKEN_PATH`. |
| 5 | Run `.venv/bin/python scripts/auth_drive_oauth.py`, sign in in browser, approve Drive. |
| 6 | Run `.venv/bin/python run_agent.py`. |

---

## Switching back to the service account

To use the service account again (e.g. after moving to a Shared Drive):

- Set `DRIVE_USE_OAUTH=false` (or remove it) in `.env`.
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to your service account JSON.

---

## Troubleshooting

- **“credentials file not found”**  
  Check `GOOGLE_DRIVE_OAUTH_CREDENTIALS` path and that `credentials_drive_oauth.json` exists in the project root (or at the path you set).

- **“Token saved” but agent still fails**  
  Ensure `.env` has `DRIVE_USE_OAUTH=true` and you ran `source .env` before `run_agent.py`.

- **“Access blocked” or consent screen**  
  Use the same Google account that owns the Drive folders. For “unverified app”, use Advanced → Go to (your app name).

- **Token expired**  
  Delete `token_drive.json` and run `scripts/auth_drive_oauth.py` again to sign in and create a new token.
