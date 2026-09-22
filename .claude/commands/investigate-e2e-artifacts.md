# Investigate Konflux E2E Artifacts

Use the repository skill at `.claude/skills/investigate-e2e-artifacts/SKILL.md` to investigate a
failed Konflux e2e run. Follow that skill's workflow exactly, passing `$ARGUMENTS` as the PR URL
when provided.

Usage:

```text
/investigate-e2e-artifacts https://github.com/konflux-ci/integration-service/pull/1649
/investigate-e2e-artifacts
```

The command requires `gh`, `jq`, and `oras`. If no PR URL is provided, allow the skill to detect
the current branch's open PR.
