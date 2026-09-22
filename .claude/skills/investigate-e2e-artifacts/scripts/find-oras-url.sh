#!/bin/bash
# find-oras-url.sh — Find the oras OCI artifact URL for the most recent failed e2e run on a PR
#
# Usage:  find-oras-url.sh <pr-url>
# Stdout: single line — the oras image reference (e.g., quay.io/konflux-test-storage/...)
# Stderr: diagnostic messages
# Exit 0: URL found
# Exit 1: URL not found (actionable error printed to stderr)

set -euo pipefail

PR_URL="${1:-}"

if [ -z "$PR_URL" ]; then
  # Try to auto-detect from current git branch
  PR_URL=$(gh pr view --json url -q .url 2>/dev/null || echo "")
  if [ -z "$PR_URL" ]; then
    echo "[find-oras-url] ERROR: No PR URL provided and cannot detect from current branch." >&2
    echo "[find-oras-url] Usage: find-oras-url.sh https://github.com/<owner>/<repo>/pull/<number>" >&2
    exit 1
  fi
  echo "[find-oras-url] Detected PR from current branch: $PR_URL" >&2
fi

# Extract owner and repo from the PR URL
owner=$(echo "$PR_URL" | sed 's|https://github\.com/\([^/]*\)/.*|\1|')
repo=$(echo "$PR_URL"  | sed 's|https://github\.com/[^/]*/\([^/]*\)/.*|\1|')

if [ "$owner" = "$PR_URL" ] || [ "$repo" = "$PR_URL" ]; then
  echo "[find-oras-url] ERROR: Could not parse owner/repo from URL: $PR_URL" >&2
  echo "[find-oras-url] Expected format: https://github.com/<owner>/<repo>/pull/<number>" >&2
  exit 1
fi

echo "[find-oras-url] Repo: $owner/$repo  PR: $PR_URL" >&2

# ── Strategy 1: Parse bot comments containing "oras pull" ────────────────────
echo "[find-oras-url] Strategy 1: scanning PR comments for oras pull command..." >&2

comment_body=$(gh pr view "$PR_URL" --json comments \
  --jq '[.comments[] | select(.body | contains("oras pull"))] |
        sort_by(.createdAt) | last | .body' 2>/dev/null || echo "")

if [ -n "$comment_body" ] && [ "$comment_body" != "null" ]; then
  oras_url=$(printf '%s' "$comment_body" \
    | grep -o 'quay\.io/konflux-test-storage/[^[:space:]"\\]*' | head -1 || echo "")
  if [ -n "$oras_url" ]; then
    echo "[find-oras-url] Found via bot comment: $oras_url" >&2
    echo "$oras_url"
    exit 0
  fi
fi

echo "[find-oras-url] Strategy 1: no oras URL found in comments, trying Checks API..." >&2

# ── Strategy 2: GitHub Checks API ───────────────────────────────────────────
sha=$(gh pr view "$PR_URL" --json headRefOid -q .headRefOid 2>/dev/null || echo "")

if [ -n "$sha" ]; then
  echo "[find-oras-url] HEAD SHA: $sha" >&2

  # Try to find oras URL embedded in check run output text
  check_output=$(gh api "repos/$owner/$repo/commits/$sha/check-runs" \
    --jq '[.check_runs[] |
           select(.name | ascii_downcase | contains("konflux-e2e")) |
           select(.conclusion == "failure") |
           .output.text // ""] | last' 2>/dev/null || echo "")

  if [ -n "$check_output" ] && [ "$check_output" != "null" ]; then
    oras_url=$(printf '%s' "$check_output" \
      | grep -o 'quay\.io/konflux-test-storage/[^[:space:]"<>\\]*' | head -1 || echo "")
    if [ -n "$oras_url" ]; then
      echo "[find-oras-url] Found via Checks API output text: $oras_url" >&2
      echo "$oras_url"
      exit 0
    fi
  fi

  # Last resort: construct URL from check name (best-effort, may be wrong)
  check_name=$(gh api "repos/$owner/$repo/commits/$sha/check-runs" \
    --jq '[.check_runs[] |
           select(.name | ascii_downcase | contains("konflux-e2e")) |
           select(.conclusion == "failure") |
           .name] | last' 2>/dev/null || echo "")

  if [ -n "$check_name" ] && [ "$check_name" != "null" ]; then
    # Map known GitHub orgs to their Quay equivalents
    quay_org="$owner"
    [ "$owner" = "konflux-ci" ] && quay_org="konflux-team"

    # Extract just the pipelinerun-style name from the check name
    # Check names look like "Red Hat Konflux / konflux-e2e / integration-service"
    pipeline_run_name=$(echo "$check_name" | grep -o 'konflux-e2e-[a-z0-9]*' || echo "")

    if [ -n "$pipeline_run_name" ]; then
      constructed="quay.io/konflux-test-storage/$quay_org/$repo:$pipeline_run_name"
    else
      constructed="quay.io/konflux-test-storage/$quay_org/$repo:$(echo "$check_name" | tr ' /' '-' | tr -s '-' | tr '[:upper:]' '[:lower:]' | sed 's/^-//')"
    fi

    echo "[find-oras-url] WARNING: constructed best-effort URL — verify before use: $constructed" >&2
    echo "$constructed"
    exit 0
  fi
fi

# ── Failure ──────────────────────────────────────────────────────────────────
echo "" >&2
echo "[find-oras-url] ERROR: Could not find a failed e2e run for this PR." >&2
echo "" >&2
echo "Possible causes:" >&2
echo "  1. The e2e run is still in progress (no bot comment yet)" >&2
echo "  2. The PR has no failed e2e run (all checks passed)" >&2
echo "  3. The bot comment uses a different format than expected" >&2
echo "" >&2
echo "Manual recovery:" >&2
echo "  Look for a comment from 'konflux-ci-qe-bot' on the PR." >&2
echo "  It will contain a line like:" >&2
echo "    oras pull quay.io/konflux-test-storage/<org>/<repo>:<pipelinerun-name>" >&2
echo "  Copy that URL and pass it directly to oras pull." >&2
exit 1
