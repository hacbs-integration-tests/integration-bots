# investigate-e2e-artifacts

Automatically downloads and investigates Konflux e2e test artifacts from a failing GitHub PR,
then produces a root-cause analysis report with file-anchored evidence.

## Prerequisites

Install these three tools before using the skill:

| Tool | Linux | macOS |
|------|-------|-------|
| `oras` | [GitHub releases](https://github.com/oras-project/oras/releases) | `brew install oras` |
| `gh` | [cli.github.com](https://cli.github.com/) | `brew install gh` |
| `jq` | `sudo dnf install jq` / `sudo apt install jq` | `brew install jq` |

Log in to the GitHub CLI before first use:

```bash
gh auth login
```

## How to Invoke

**Option 1 — Slash command (recommended for reliable invocation):**

```
/investigate-e2e-artifacts https://github.com/konflux-ci/integration-service/pull/1649
```

**Option 2 — Natural language (Claude auto-detects and applies the skill):**

```
"investigate the e2e failures on PR 1649"
"analyze e2e artifacts for this PR"
"e2e failed on integration-service, can you look at the artifacts?"
"download and investigate the oras artifacts from this PR"
```

The PR URL argument is optional if you are already inside a git repository on a branch with
an open PR — the skill detects the PR automatically.

## What the Skill Does

1. **Finds the artifact** — Reads the `konflux-ci-qe-bot` comment on the PR to get the exact
   `oras pull` command for the most recent failed run. Falls back to the GitHub Checks API.

2. **Creates a numbered folder** in your current directory:
   - First invocation → `oras-artifacts_01/`
   - Second invocation → `oras-artifacts_02/`
   - Each call always creates a new folder, regardless of whether the oras artifact changed.

3. **Downloads the artifact** — Runs `oras pull quay.io/konflux-test-storage/...` into the folder.

4. **Runs 5 parallel analyses** simultaneously:
   - **JUnit XML** (`e2e-report.xml`) — which tests failed and their failure messages
   - **Ginkgo log** (`e2e-tests.log`) — full failure blocks, stack traces, `Expected`/`Got` lines
   - **Kubernetes events** (`konflux-artifacts/events.json`) — OOMKill, ImagePull, scheduling errors
   - **Pod logs** (`pods/`) — component-level errors from individual service pods
   - **TaskRun status** (`pipelineruns.json`, `taskruns.json`) — Tekton pipeline failures

5. **Synthesizes findings** — Cross-correlates signals across all 5 sources into ranked hypotheses.

6. **Writes `INVESTIGATION.md`** inside the artifact folder and prints it to your chat.

## Example Session

```
/investigate-e2e-artifacts https://github.com/konflux-ci/integration-service/pull/1649

✓ Found oras artifact: quay.io/konflux-test-storage/konflux-team/integration-service:konflux-e2e-clqrf
✓ Created folder: oras-artifacts_01/
✓ Pulled 47 files (312 MB)
✓ Decompressed .gz files
✓ Running parallel analysis across 5 artifact types...

---

# E2E Investigation Report

**PR**: https://github.com/konflux-ci/integration-service/pull/1649
**PipelineRun**: konflux-e2e-clqrf
**Generated**: 2026-07-22 13:45:00

## Summary

3 of 142 tests failed. The integration-service pod OOMKilled during the test window, causing
"context deadline exceeded" errors in the `CreateSnapshotForIntegrationTestRun` suite.

## Failed Tests (3 failures)

| # | Test Suite | Test Name | Failure Summary |
|---|---|---|---|
| 1 | CreateSnapshotForIntegrationTestRun | when creating a snapshot | context deadline exceeded |
| 2 | CreateSnapshotForIntegrationTestRun | with valid component | context deadline exceeded |
| 3 | IntegrationServiceController | reconcile loop | connection refused |

## Root Cause Analysis

### Hypothesis 1 — OOM on integration-service pod [CONFIDENCE: HIGH]

The integration-service container exceeded its memory limit mid-test, causing the process
to be killed and all in-flight requests to fail with timeout errors.

**Evidence:**
- `events.json` — OOMKilling on `integration-service-7d9f4b` at 2026-07-22T12:41:03Z
- `e2e-tests.log:1847` — `context deadline exceeded (Client.Timeout exceeded while awaiting headers)`
- `pods/integration-service-7d9f4b.log:2901` — `signal: killed`

## Recommendations

1. Increase the memory limit for integration-service in the test cluster config
2. Check recent commits for memory leaks in the reconcile loop
```

## Output Files

After each invocation you will find in `oras-artifacts_NN/`:

| File | Description |
|------|-------------|
| `e2e-report.xml` | Raw JUnit XML from the test run |
| `e2e-tests.log` | Full Ginkgo runner stdout |
| `deploy-konflux-ci.log` | Deploy task logs |
| `pipeline-status.json` | PipelineRun summary |
| `konflux-artifacts/` | Kubernetes resource dumps (events, PipelineRuns, TaskRuns, etc.) |
| `pods/` | Individual pod logs |
| **`INVESTIGATION.md`** | **The generated RCA report — start here** |

## Troubleshooting

**`oras pull` fails with "unauthorized"**

The skill retries automatically with `oras login quay.io`. If it still fails, obtain credentials
from your team for `quay.io/konflux-test-storage` and run:

```bash
oras login quay.io
oras pull quay.io/konflux-test-storage/<org>/<repo>:<pipelinerun-name>
```

**"No failed e2e run found"**

- The e2e run may still be in progress — wait for the `konflux-ci-qe-bot` comment on the PR
- Check the PR's Checks tab for a check named `Red Hat Konflux / konflux-e2e / ...`
- If you already have the oras URL, pass it directly:

  ```bash
  cd oras-artifacts_01
  oras pull quay.io/konflux-test-storage/konflux-team/integration-service:konflux-e2e-XXXXX
  ```

**Skill not triggered by natural language**

Use the explicit slash command: `/investigate-e2e-artifacts <pr-url>`

**`jq` errors on events.json or taskruns.json**

If the JSON schema differs from expected, run a discovery query first:

```bash
jq 'keys' konflux-artifacts/events.json
jq '.items[0] | keys' konflux-artifacts/events.json
```

## Architecture Notes

- The skill discovers the artifact via the `scripts/find-oras-url.sh` script, which uses two
  strategies: parsing bot comments (primary) and the GitHub Checks API (fallback).
- Folder numbering (`oras-artifacts_01`, `_02`, ...) is handled by `scripts/next-folder.sh`
  which scans the current directory for existing `oras-artifacts_*` folders.
- JUnit XML parsing uses `scripts/parse-junit.sh` (Python 3, stdlib only).
- Large files (`events.json` ~11 MB, `taskruns.json` ~5 MB) are always accessed via `jq`
  with message truncation to avoid context window overflow.
