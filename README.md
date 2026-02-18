# Integration Team Sprint Demo Automation

Automates creating the next Integration Team sprint demo in Google Drive: copies the template into the **present** folder with the new sprint number, replaces **"xxx"** with that number on the first slide of the new deck, then moves the previous demo to **old**.

## Pushing to GitHub

To avoid uploading secrets (API keys, `.env`, OAuth and service account files), see **[docs/GITHUB_AND_SECRETS.md](docs/GITHUB_AND_SECRETS.md)** for a checklist and upload steps.

## Setup

1. **Python 3.10+** and a virtualenv:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Google Drive access** (choose one):
   - **Service account**: Create a project, enable the Drive API, create a **service account** key (JSON), and share the Team demos folder (and **present** / **old**) with the service account. (Service accounts have 0 MB Drive quota by default, so copies may fail with `storageQuotaExceeded`.)
   - **OAuth (your account)**: Use your own Google account for Drive so copies use your quota. See **[docs/DRIVE_OAUTH_SETUP.md](docs/DRIVE_OAUTH_SETUP.md)** for step-by-step setup.

3. **Config**: Copy `.env.example` to `.env` and set:

   - `TEAM_DEMOS_FOLDER_ID` — Team demos folder ID (from the folder URL).
   - `PRESENT_FOLDER_ID` — ID of the **present** subfolder.
   - `OLD_FOLDER_ID` — ID of the **old** subfolder.
   - `GOOGLE_APPLICATION_CREDENTIALS` — Path to the service account JSON key file.
   - **LLM for the agent** (choose one):
     - **OpenAI**: set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.
     - **DeepSeek**: set `LLM_PROVIDER=deepseek` and `DEEPSEEK_API_KEY`.
     - **Gemini (Google AI)**: set `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY` (or `GEMINI_API_KEY`).
     - **Note:** Most providers require a **billing method on file** for the API to work, even when using free tier or free credits (OpenAI, Gemini, DeepSeek typically all do).

   Optionally set `TEMPLATE_NAME_PATTERN` and `DEFAULT_SPRINT_NUMBER` (see `.env.example`).

## Run once

From the project root (with venv active):

```bash
python run_agent.py
```

Or with `PYTHONPATH` so imports resolve:

```bash
PYTHONPATH=. python run_agent.py
```

## Run every two weeks (cron)

Add a cron job that runs the script on your desired day/time. Example: every other Sunday at 9:00 (adjust path and user):

```bash
0 9 * * 0  cd /path/to/integration-bots && .venv/bin/python run_agent.py
```

Cron runs with a minimal environment; ensure `PYTHONPATH` is set if needed:

```bash
0 9 * * 0  cd /path/to/integration-bots && PYTHONPATH=. .venv/bin/python run_agent.py
```

To run every 14 days regardless of weekday (e.g. from a systemd timer or a helper script that sleeps 14 days), use a wrapper or a cron expression that matches your sprint end (e.g. `0 9 */14 * *` for every 14th day of the month at 9:00).

## First-slide sprint number

The template deck should have **"xxx"** as a placeholder on the first slide (e.g. "Integration Team Sprint xxx Demo"). After copying, the agent replaces **"xxx"** with the new sprint number (e.g. 306) on that slide only. This uses the **Google Slides API**: enable it in [APIs & Services → Library](https://console.cloud.google.com/apis/library) (search "Google Slides API") and, if you use OAuth, re-run `scripts/auth_drive_oauth.py` once so the token includes the Slides scope.

## Folder layout

- **Team demos** (root): contains the template file (name starting with `TEMPLATE_NAME_PATTERN`) and subfolders **present** and **old**.
- **present**: exactly one current demo file, e.g. `Integration Team Sprint 306 Demo`.
- **old**: previous demos moved here after each run.

## Flowchart (LangGraph)

A flowchart of the implementation from a LangGraph perspective (ReAct loop, tool sequence, state) is in **[docs/FLOWCHART_LANGGRAPH.md](docs/FLOWCHART_LANGGRAPH.md)**. The diagrams are in Mermaid (render in GitHub, VS Code, or any Mermaid viewer).

## Idempotency

If the agent runs twice without a new sprint, it will create the next numbered demo again. To avoid duplicates, run the job only at sprint end (e.g. every two weeks). Optional: add a “last run” or “last created sprint” check in the runner and skip if already up to date.
