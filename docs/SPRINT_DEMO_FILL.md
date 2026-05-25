# Sprint Demo Slide Filler

Automatically fills your Jira ticket slides into the shared team sprint demo deck in Google Drive.

---

## What it does

At the end of each sprint, the team has a shared Google Slides deck in the Drive "present" folder (created by the main sprint demo bot). This tool lets any team member auto-populate their own slides into that deck — one slide per Jira ticket — without manually copy-pasting content.

For each ticket it:
1. Duplicates the template slide (slide 2) in the deck
2. Fills in your name, the ticket key (with a Jira hyperlink), the ticket title, and LLM-generated short summaries for Problem / Solution / Benefits / Downsides
3. Asks you to confirm the content before writing anything

---

## Prerequisites

Before using this feature:

1. **Jira MCP configured** *(optional for manual mode, required for auto-discover)* — if configured, the tool identifies you automatically and can fetch ticket details. If not configured, manual mode still works — the skill will ask you for your name, sprint number, and a short description of each ticket.

2. **Google Drive auth set up** — the project must be configured with valid Drive credentials. Check that your `.env` has either:
   - `DRIVE_USE_OAUTH=true` + `GOOGLE_DRIVE_OAUTH_CREDENTIALS` + `GOOGLE_DRIVE_TOKEN_PATH` (recommended), or
   - `GOOGLE_APPLICATION_CREDENTIALS` (service account)

   If you haven't done this yet, see [DRIVE_OAUTH_SETUP.md](DRIVE_OAUTH_SETUP.md).

3. **Sprint demo deck exists** — the main bot must have already created the current sprint deck in the "present" Drive folder. If it hasn't run yet, the fill tool will tell you.

4. **Python venv activated** — the tool calls `run_fill_demo.py` using `.venv/bin/python` in the project root.

---

## How to use it

Open Claude Code from the `integration-bots` project directory and run:

### Option A — Specify your tickets

```
/integration-sprint-demo fill KONFLUX-123 KONFLUX-456
```

Use this when you know exactly which tickets you want to demo.

### Option B — Auto-discover your tickets

```
/integration-sprint-demo
```

The tool will find all Jira tickets in the current sprint that are assigned to you with status **In Review**, **Closed**, or **Resolved**. It will show you what it found before doing anything.

---

## What happens step by step

1. Your Jira identity is fetched (display name, account ID)
2. The current active sprint number is fetched from the KONFLUX Jira board
3. Tickets are resolved (from your args or auto-discovered)
4. Ticket details (summary + description) are fetched from Jira
5. **Claude generates short slide content** for each ticket — 1–2 sentences per section
6. **You are shown a preview** and asked to confirm before anything is written
7. The Python script duplicates slide 2 for each ticket and fills in all placeholders
8. A link to the deck is returned

---

## Slide structure

Each slide follows this layout (from the team template):

```
Presenter: <Your Name>                        CONFIDENTIAL

KONFLUX-123  Fix snapshot race condition
┌──────────────────────┐  ┌──────────────────────┐
│ ► Problem            │  │ ► Benefits            │
│   •                  │  │   •                   │
│ ► Solution/Results   │  │ ► Downsides           │
│   •                  │  │   •                   │
└──────────────────────┘  └──────────────────────┘
                                          [Red Hat logo]
```

The ticket key (`KONFLUX-123`) is a clickable hyperlink to the Jira ticket.

---

## Guardrails

| Situation | What happens |
|---|---|
| Jira MCP not configured + auto-discover mode | Stops immediately with a message to configure Jira MCP or use manual mode |
| Jira MCP not configured + manual mode | Asks you for your name, sprint number, and a short description of each ticket — then continues |
| Deck in "present" is for an older sprint | Tool stops and tells you — run the main bot first |
| No deck in "present" folder | Tool stops and tells you — run the main bot first |
| Your slides are already in the deck | Tool tells you and shows you the deck link |
| No matching tickets found (auto mode) | Tool stops and tells you |
| Drive auth is expired | Python script exits with an auth error — re-run `scripts/auth_drive_oauth.py` |

---

## Template requirements

Slide 2 of the deck must contain these exact placeholder strings (already set up in the team template):

| Placeholder | Replaced with |
|---|---|
| `<Name>` | Your display name from Jira |
| `STONEINTG-XXXX` | Ticket key (e.g. `KONFLUX-123`) |
| `Title` | Ticket summary |
| `<PROBLEM>` | Generated problem description |
| `<SOLUTION>` | Generated solution description |
| `<BENEFITS>` | Generated benefits |
| `<DOWNSIDES>` | Generated downsides |

Slide 2 is **never modified** — it is always kept as the blank template. Every new slide is a duplicate.

---

## Troubleshooting

**"Could not identify your Jira user"**
→ Your Jira MCP is not configured or not authenticated. Check your MCP settings.

**"No deck found in present folder"**
→ The main sprint demo bot hasn't run yet this sprint. Ask whoever manages the bot to run it, or run `python run_agent.py` yourself.

**"The deck in present is for an older sprint"**
→ The present folder has a deck from a previous sprint. The main bot needs to create a new one.

**"Failed to initialise Google Drive/Slides"**
→ Drive credentials are missing or expired. Check `.env` and re-run `scripts/auth_drive_oauth.py` if using OAuth.

**"Failed to duplicate slide"**
→ The service account or OAuth user may not have Editor access to the deck. Check sharing settings in Google Drive.
