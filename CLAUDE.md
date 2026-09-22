## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Repository skills

The repository includes `.claude/skills/investigate-e2e-artifacts/` for investigating failed
Konflux e2e runs. Use it when a user asks to investigate e2e failures, download oras artifacts,
or produce an RCA for a failed Konflux pipeline. It requires `gh`, `jq`, and `oras`; the user
should run Claude Code from the repository root and provide the GitHub PR URL when available.
