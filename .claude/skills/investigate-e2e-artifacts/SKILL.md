---
name: investigate-e2e-artifacts
description: Use when asked to investigate e2e test failures on a Konflux GitHub PR, download
  OCI test artifacts with oras pull, analyze Ginkgo logs and pod logs, or produce a root-cause
  analysis of a failed Konflux e2e pipeline run. Trigger phrases: "investigate e2e", "analyze e2e
  artifacts", "e2e failed on PR", "oras artifacts", "download test artifacts", "konflux-e2e failed".
version: 1.0.0
argument-hint: <pr-url>
allowed-tools: Bash(gh:*), Bash(oras:*), Bash(ls:*), Bash(mkdir:*), Bash(find:*), Bash(grep:*),
  Bash(gunzip:*), Bash(jq:*), Bash(python3:*), Bash(sort:*), Bash(tail:*), Bash(printf:*),
  Bash(which:*), Bash(cat:*), Bash(chmod:*), Bash(./.claude/skills/investigate-e2e-artifacts/scripts/*:*),
  Read, Write
---

# Investigate E2E Artifacts

Fully automated investigation of a failed Konflux e2e test run: discovers the OCI artifact from
the GitHub PR, downloads it, and runs parallel analysis across all artifact types to produce an
evidence-backed root-cause analysis report.

## Phase 0 — Prerequisite Check

Run all three checks simultaneously (single response turn):

```bash
which oras 2>/dev/null || echo "MISSING_oras"
which jq   2>/dev/null || echo "MISSING_jq"
which gh   2>/dev/null || echo "MISSING_gh"
```

If ANY output is `MISSING_*`, STOP immediately. Print:

```
Missing prerequisites. Install the following, then retry:

  oras  → brew install oras
          OR: https://github.com/oras-project/oras/releases
  jq    → sudo dnf install jq  /  brew install jq  /  sudo apt install jq
  gh    → https://cli.github.com/
```

Do NOT proceed without all three tools present.

## Phase 1 — Find the OCI Artifact URL

The PR URL comes from `$ARGUMENTS`. If `$ARGUMENTS` is empty, detect the current PR:

```bash
gh pr view --json url -q .url 2>/dev/null || echo ""
```

Run the discovery script:

```bash
./.claude/skills/investigate-e2e-artifacts/scripts/find-oras-url.sh "$ARGUMENTS"
```

Capture its stdout as `ORAS_URL`. The script prints exactly one line — the oras image reference.

If the script exits non-zero, show its stderr to the user and STOP. Do NOT guess or construct an
oras URL yourself.

The oras tag portion (e.g., `konflux-e2e-clqrf`) is the PipelineRun name — save it for the report.

## Phase 2 — Create Folder and Download

Run Steps 2.1 through 2.3 sequentially (each depends on the previous):

```bash
# Step 2.1 — Compute next folder name (zero-padded, increments each invocation)
FOLDER=$(./.claude/skills/investigate-e2e-artifacts/scripts/next-folder.sh)
echo "Creating folder: $FOLDER"

# Step 2.2 — Create and enter the folder
mkdir -p "$FOLDER"
cd "$FOLDER"

# Step 2.3 — Pull OCI artifact
oras pull "$ORAS_URL"
```

If `oras pull` fails with "unauthorized" in stderr, attempt login and retry:

```bash
oras login quay.io
oras pull "$ORAS_URL"
```

If it still fails, tell the user: "Run this manually to authenticate, then retry the skill:
`oras login quay.io`" — and STOP.

**Step 2.4** — Discover the artifact structure. Run all three simultaneously:

```bash
ls -lh .
ls -lh konflux-artifacts/ 2>/dev/null || echo "NOTE: no konflux-artifacts/ directory"
find pods/ -type f 2>/dev/null | sort | head -40 || echo "NOTE: no pods/ directory"
```

Report what was found. The pods/ structure is only known at this point.

**Step 2.5** — Decompress all compressed files:

```bash
find . -name "*.gz" -exec gunzip {} \;
```

## Phase 3 — Parallel Analysis

**CRITICAL: Issue ALL five sets of tool calls in a single response turn. Do NOT wait for one
to complete before issuing the next. All commands must be started simultaneously.**

---

### Agent A — JUnit XML (e2e-report.xml)

```bash
./.claude/skills/investigate-e2e-artifacts/scripts/parse-junit.sh e2e-report.xml
```

Fallback if python3 is unavailable:

```bash
grep -c '<failure' e2e-report.xml
grep -B5 '<failure' e2e-report.xml | grep -E 'classname=|name=' | head -60
```

Record from output:
- Total failures count and total tests count
- For each failure: suite name (classname), test name, failure message (first 200 chars)

**The list of failed test names feeds into Agent B below.**

---

### Agent B — Ginkgo Log Correlation (e2e-tests.log)

Issue simultaneously with Agent A:

```bash
grep -n '\[FAILED\]\|Failure Details:\|Failure:\|panic:\|Expected.*but got' e2e-tests.log | head -120
tail -300 e2e-tests.log
```

Then for up to 5 most interesting failed test names from Agent A (replace spaces with `.*` for
the regex since test names may span classname + testname):

```bash
grep -n -A50 "<test-name-pattern>" e2e-tests.log | head -70
```

Record: Ginkgo `Failure:` blocks, `Expected`/`Got` lines, and the **exact line numbers** for
report citations (e.g., `e2e-tests.log:1847`).

---

### Agent C — Kubernetes Events (konflux-artifacts/events.json)

Issue simultaneously with Agents A and B:

```bash
# Count Warning events
jq '[.items[] | select(.type == "Warning")] | length' konflux-artifacts/events.json

# Last 40 Warning events (messages truncated to avoid token explosion)
jq '[.items[] | select(.type == "Warning")] | sort_by(.lastTimestamp) | .[-40:] | .[] |
    {reason:.reason, msg:.message[0:180], obj:.involvedObject.name,
     kind:.involvedObject.kind, t:.lastTimestamp}' konflux-artifacts/events.json

# Critical event patterns regardless of time window
jq '[.items[] | select(.reason |
    test("OOMKill|ImagePull|FailedSchedul|BackOff|Evict|CrashLoop";"i"))] | .[] |
    {reason:.reason, msg:.message[0:180], obj:.involvedObject.name,
     t:.lastTimestamp}' konflux-artifacts/events.json
```

Record: OOMKilled pods, ImagePullBackOff, FailedScheduling events, CrashLoop restarts. Note
timestamps for correlation with the test failure window.

If `konflux-artifacts/events.json` does not exist, report "events.json not found" and skip.

---

### Agent D — Pod Log Scanning (pods/)

Issue simultaneously with Agents A, B, and C:

```bash
# Discover pod log files (structure may be flat or nested)
find pods/ -type f 2>/dev/null | sort | head -60

# Find files with error patterns
grep -rl 'level=error\|"level":"error"\|ERROR\|FATAL\|panic:' pods/ 2>/dev/null | head -20
```

Then for each pod log file that had hits (up to 5 files):

```bash
grep -n 'level=error\|"level":"error"\|ERROR\|FATAL\|panic:' pods/<file> | head -50
```

Record: which pod log files contain errors, the line numbers, and the error text.

If `pods/` does not exist, report "pods/ directory not found" and skip.

---

### Agent E — TaskRun / PipelineRun Status

Issue simultaneously with Agents A, B, C, and D:

```bash
# pipeline-status.json is small — read fully
cat pipeline-status.json 2>/dev/null || echo "pipeline-status.json not found"

# Failed PipelineRuns
jq '[.items[] | select(.status.conditions[]? |
    select(.type == "Succeeded" and .status == "False"))] | .[] |
    {name:.metadata.name,
     msg:(.status.conditions[] | select(.type=="Succeeded") | .message[0:250])}' \
    konflux-artifacts/pipelineruns.json 2>/dev/null || echo "pipelineruns.json not found"

# Failed TaskRuns (sample top 15 — file is large)
jq '[.items[] | select(.status.conditions[]? |
    select(.type == "Succeeded" and .status == "False"))] | .[0:15] | .[] |
    {name:.metadata.name,
     task:(.spec.taskRef.name // .metadata.labels["tekton.dev/task"] // "inline"),
     msg:(.status.conditions[] | select(.type=="Succeeded") | .message[0:200])}' \
    konflux-artifacts/taskruns.json 2>/dev/null || echo "taskruns.json not found"
```

Record: failed pipeline and task names with their error messages.

## Phase 4 — Root Cause Synthesis

With all five agents' output collected, build 1–3 ranked hypotheses.

For each hypothesis:
1. **One-sentence claim** — what broke and why
2. **Evidence** — each evidence item MUST be file-anchored:
   - `e2e-tests.log:LINE` — verbatim excerpt (≤120 chars)
   - `events.json` — reason + object name + timestamp
   - `pods/<filename>:LINE` — verbatim excerpt
3. **Confidence**: HIGH (≥2 independent signals) / MEDIUM (1 signal, plausible) / LOW (speculative)

**Correlation heuristics:**

| If Agent C shows... | AND Agent B shows... | → Root cause |
|---|---|---|
| OOMKilled on a pod | "context deadline exceeded" near the same time | Memory pressure |
| ImagePullBackOff | test suite timeout or setup failure | Image not available |
| FailedScheduling | pending pods at test start | Cluster capacity |

| If Agent A shows... | AND Agent E shows... | → Root cause |
|---|---|---|
| Many failures in same test suite | Matching TaskRun failed | Tekton task failure skipped the suite |

| If Agent B shows... | AND Agent C shows... | → Root cause |
|---|---|---|
| "connection refused" or timeout | No Warning events | Environment config issue, not cluster health |

| If Agent D shows errors in component pod X | AND Agent A shows failures in tests for component X | → Component-level bug in X |

**Rules:**
- Do NOT cite "flakiness" unless there is no other evidence and Agent B shows intermittent timing
- Every hypothesis MUST have at least one file:line citation
- If signals conflict across agents, list both hypotheses with different confidence levels

## Phase 5 — Write Report

Write the investigation report to: `$FOLDER/INVESTIGATION.md`

Use this exact structure:

```markdown
# E2E Investigation Report

**PR**: <pr-url or "unknown">
**Artifact folder**: <folder-name>
**PipelineRun**: <oras-tag extracted from ORAS_URL>
**Generated**: <current date and time>

## Summary

<1–2 sentences: what broke, what the most likely cause is>

## Failed Tests (<N> failures out of <total>)

| # | Test Suite | Test Name | Failure Summary |
|---|---|---|---|
| 1 | ... | ... | ... ≤100 chars |

## Root Cause Analysis

### Hypothesis 1 — <short title> [CONFIDENCE: HIGH]

<One sentence claim.>

**Evidence:**
- `e2e-tests.log:LINE` — `<verbatim excerpt ≤120 chars>`
- `events.json` — `<reason>` on `<object-name>` at `<timestamp>`
- `pods/<filename>:LINE` — `<verbatim excerpt>`

### Hypothesis 2 — <short title> [CONFIDENCE: MEDIUM]

...

## Detailed Evidence

### Kubernetes Warning Events (events.json)

<paste the filtered jq output from Agent C, truncated to ≤30 events>

### Pod Errors (pods/)

<list each affected pod file with its error line citations>

### Failed TaskRuns

<list names and error messages from Agent E>

## Recommendations

1. <Actionable step — fix or rerun with more resources, or file a bug>
2. ...
```

After writing `INVESTIGATION.md`, read it back and print its full content to stdout so the user
sees the complete report in their chat window.

## Common Mistakes — DO NOT DO THESE

❌ WRONG: Guess the oras URL based on PR metadata instead of running `find-oras-url.sh`
✅ CORRECT: Always run the script; its two-strategy cascade handles edge cases

❌ WRONG: Run Agents A–E one at a time, waiting for each before starting the next
✅ CORRECT: Issue all five agents' tool calls in a single response turn

❌ WRONG: Read `events.json` directly — it is 11 MB and will overflow context
✅ CORRECT: Always pipe through `jq` with field truncation and row limits

❌ WRONG: Skip the structure discovery step (2.4) and hard-code `pods/*.log` paths
✅ CORRECT: `find pods/ -type f` first — the structure is only known after `oras pull`

❌ WRONG: Cite "test flakiness" with no file:line evidence
✅ CORRECT: Every hypothesis needs at least one file:line anchor

❌ WRONG: Write the report to the current directory instead of `$FOLDER/INVESTIGATION.md`
✅ CORRECT: The report lives inside the numbered artifact folder
