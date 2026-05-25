# Integration Sprint Demo — Fill Slides

Auto-fill the current sprint demo deck with Jira ticket slides for the requesting user.

## Usage

```
/integration-sprint-demo fill KONFLUX-123 KONFLUX-456
/integration-sprint-demo
```

- **With ticket numbers**: fills slides for the specified tickets.
- **Without arguments**: auto-discovers your tickets in the current sprint (status: In Review, Closed, or Resolved).

---

## What you do

Follow these steps exactly. Do not skip any step.

### Step 0 — Check if Jira MCP is available

Try calling:

```
jira_get /rest/api/3/myself
```

**If it succeeds:** extract `displayName` and `accountId`. Set `jira_available = true`. Continue to Step 1.

**If it fails** (tool not found, not configured, auth error, any error):
- Set `jira_available = false`.
- If the user ran **auto-discover mode** (no ticket numbers provided):
  - Stop immediately and tell the user:
    > "Auto-discover mode requires Jira MCP to be configured. Either set up the Jira MCP, or run `/integration-sprint-demo fill KONFLUX-123 KONFLUX-456` with your ticket numbers instead."
  - Do not proceed.
- If the user ran **manual mode** (ticket numbers were provided):
  - Tell the user:
    > "Jira MCP is not configured, so I can't look up your name or sprint automatically. I'll ask you for those instead."
  - Ask the user: **"What is your full display name?"** (e.g. "Kasem Alem") — this will appear on the slides.
  - Ask the user: **"What is the current sprint number?"** (e.g. 313)
  - Store these answers. Skip Steps 1 and 2 entirely. Go to Step 3.

### Step 1 — Get the current active sprint number

*(Skip this step if `jira_available = false` — you already have the sprint number from Step 0.)*

Use the Jira MCP to get active sprints for board 11443:

```
jira_get /rest/agile/1.0/board/11443/sprint?state=active
```

Find the sprint whose `state` is `"active"`. Extract the sprint number from its `name` field — for example from `"KONFLUX Integration Sprint 313"` extract `313`. If no active sprint is found, stop and tell the user.

### Step 2 — Determine which tickets to process

**If the user provided ticket numbers** (e.g. `fill KONFLUX-123 KONFLUX-456`):
- Use exactly those ticket keys. Skip to Step 3.

**If no tickets were provided** (auto-discover mode — only reachable here if `jira_available = true`):
- Query Jira for tickets assigned to the current user in the active sprint with a status of In Review, Closed, or Resolved:

```
jira_get /rest/api/3/search/jql
  jql: sprint in openSprints() AND assignee = "<accountId>" AND status in ("In Review", "Review", "Closed", "Resolved", "Done")
  fields: summary,status,description
```

- If no tickets match, tell the user: "No tickets found in the active sprint with status In Review, Closed, or Resolved assigned to you." and stop.
- List the discovered tickets to the user before proceeding so they can confirm.

### Step 2.5 — Filter out tickets already in the deck

Before fetching any ticket details or generating content, check which of the resolved ticket keys are already filled in for this user.

Call the check script from the project root:

```bash
cd /home/kalem/my-projects/integration-bots && \
PYTHONPATH=. .venv/bin/python run_check_demo.py << 'ENDJSON'
{
  "user_name": "<displayName>",
  "sprint_number": <N>,
  "ticket_keys": ["TICKET-1", "TICKET-2", ...]
}
ENDJSON
```

Parse the JSON result:

- If `status` is `"error"`: stop and report the error to the user (deck not found, auth issue, etc.).
- If `missing` is empty (all tickets already in deck): tell the user "All your tickets are already in the Sprint N deck." and show the deck link. Stop — do not proceed.
- If `already_in_deck` is non-empty but `missing` is also non-empty: tell the user which tickets were skipped (already present) and which will be added. Continue with only the `missing` tickets.
- If `already_in_deck` is empty: all tickets are new. Continue with all of them.

From this point on, **only process tickets in the `missing` list**.

### Step 3 — Fetch ticket details

**If `jira_available = true`:** for each ticket key, call:

```
jira_get /rest/api/3/issue/<TICKET-KEY>
  fields: summary,description
```

Extract `summary` and `description`. The description may be free-form text; that is fine.

**If `jira_available = false`:** for each ticket key provided by the user, ask:
> "Briefly describe **<TICKET-KEY>** — what was the problem and what did you do? (A sentence or two is enough)"

Use their answer as the description for content generation in the next step.

### Step 5 — Generate slide content

For **each ticket**, generate short, focused content for the four slide sections. Keep every section to **1–2 sentences maximum**. Plain language, no jargon — understandable by anyone on the team.

Use this reasoning for each ticket:

```
Given the Jira ticket:
  Title: <summary>
  Description: <description text>

Generate:
- Problem:          What was broken, missing, or painful? (1-2 sentences)
- Solution/Results: What was built or fixed? (1-2 sentences)
- Benefits:         What value does this deliver? (1-2 sentences)
- Downsides:        Any trade-offs or limitations? (1 sentence, or write "None")
```

Keep the content grounded in the ticket. Do not invent facts not present in the ticket.

After generating, show the user a preview of what will be written to each slide and ask them to confirm before proceeding:

```
I'll add the following slides to the Sprint <N> demo deck:

**KONFLUX-123** — <summary>
- Problem: <generated>
- Solution: <generated>
- Benefits: <generated>
- Downsides: <generated>

**KONFLUX-456** — <summary>
...

Shall I fill the slides? (yes/no)
```

### Step 6 — Fill the slides

Once the user confirms, build the JSON payload and call the Python script from the project root using a heredoc (this safely handles any special characters in ticket text):

```bash
cd /home/kalem/my-projects/integration-bots && \
PYTHONPATH=. .venv/bin/python run_fill_demo.py << 'ENDJSON'
<full JSON payload here>
ENDJSON
```

The JSON payload format:

```json
{
  "user_name": "<displayName from Step 1>",
  "sprint_number": <N from Step 2>,
  "tickets": [
    {
      "key": "KONFLUX-123",
      "summary": "<ticket summary>",
      "problem": "<generated problem>",
      "solution": "<generated solution>",
      "benefits": "<generated benefits>",
      "downsides": "<generated downsides>"
    }
  ]
}
```

### Step 7 — Report the result

Parse the JSON output from the script and report to the user:

| Script status | What to say |
|---|---|
| `ok` | "Done! Added <N> slide(s) to the Sprint <sprint> deck. [Open deck](<deck_url>)" |
| `already_filled` | "Your slides are already in the Sprint <sprint> deck. [Open deck](<deck_url>)" |
| `error` | "Something went wrong: <message>. Check your Drive auth and try again." |

---

## Important rules

- Never skip the user confirmation in Step 5 before writing to the deck.
- Never modify slide 2 of the deck — it is the template. New slides are always duplicates placed after it.
- If the deck in the present folder is for an older sprint than the active one, tell the user and stop.
- If the script fails with an auth error, remind the user to check that Drive OAuth is set up (`DRIVE_USE_OAUTH=true` and `token_drive.json` is valid).
