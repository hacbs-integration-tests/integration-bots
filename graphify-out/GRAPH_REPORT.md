# Graph Report - .  (2026-05-26)

## Corpus Check
- Corpus is ~9,665 words - fits in a single context window. You may not need a graph.

## Summary
- 108 nodes · 187 edges · 9 communities (7 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Google Auth Layer|Google Auth Layer]]
- [[_COMMUNITY_Slide Fill Pipeline|Slide Fill Pipeline]]
- [[_COMMUNITY_Config and Slack Posting|Config and Slack Posting]]
- [[_COMMUNITY_LangGraph Agent Assembly|LangGraph Agent Assembly]]
- [[_COMMUNITY_Fill Tools Core|Fill Tools Core]]
- [[_COMMUNITY_Drive LangChain Tools|Drive LangChain Tools]]
- [[_COMMUNITY_Environment Config|Environment Config]]
- [[_COMMUNITY_Agent Flowchart Docs|Agent Flowchart Docs]]

## God Nodes (most connected - your core abstractions)
1. `Config Module` - 22 edges
2. `get_drive_service()` - 16 edges
3. `create_graph()` - 15 edges
4. `get_slides_service()` - 13 edges
5. `create_drive_tools()` - 12 edges
6. `add_tickets_to_deck()` - 11 edges
7. `post_demo_message()` - 11 edges
8. `str` - 8 edges
9. `create_slack_tools()` - 8 edges
10. `main()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Sprint Demo Automation Plan` --references--> `create_drive_tools()`  [EXTRACTED]
  .cursor/plans/sprint_demo_automation_agent_2d8cd456.plan.md → src/drive/tools.py
- `OAuth vs Service Account Auth Decision` --rationale_for--> `get_drive_service()`  [EXTRACTED]
  docs/DRIVE_OAUTH_SETUP.md → src/drive/client.py
- `ReAct Agent Pattern (LangGraph)` --rationale_for--> `create_graph()`  [EXTRACTED]
  docs/FLOWCHART_LANGGRAPH.md → src/agent/graph.py
- `Sprint Demo Automation Plan` --references--> `create_graph()`  [EXTRACTED]
  .cursor/plans/sprint_demo_automation_agent_2d8cd456.plan.md → src/agent/graph.py
- `Sprint Demo Fill Feature Docs` --references--> `Fill Demo CLI Entry Point`  [EXTRACTED]
  docs/SPRINT_DEMO_FILL.md → run_fill_demo.py

## Hyperedges (group relationships)
- **Slide Fill Pipeline: check then fill** — run_check_demo, run_fill_demo, fill_tools_add_tickets_to_deck [EXTRACTED 1.00]
- **LangGraph Agent Assembly: model + tools + prompt** — agent_graph_create_graph, drive_tools_create_drive_tools, slack_tools_create_slack_tools [EXTRACTED 1.00]
- **Google Auth Dual Path: OAuth or Service Account** — drive_client_get_drive_service, drive_client_get_slides_service, drive_client_oauth_creds [EXTRACTED 1.00]

## Communities (9 total, 2 thin omitted)

### Community 0 - "Google Auth Layer"
Cohesion: 0.15
Nodes (17): get_drive_service(), get_slides_service(), _oauth_creds(), Google Drive API client: OAuth (user) or service account credentials., Load or refresh OAuth credentials from token file and client secret., Build and return a Drive API v3 service. Uses OAuth if DRIVE_USE_OAUTH=true, els, Build and return a Slides API v1 service (same credentials as Drive). Enable Goo, _fail() (+9 more)

### Community 1 - "Slide Fill Pipeline"
Cohesion: 0.18
Nodes (19): add_tickets_to_deck(), duplicate_slide(), fill_ticket_slide(), find_deck_in_present(), _get_slide_object_id(), get_user_existing_ticket_keys(), Google Slides operations for filling sprint demo slides with Jira ticket content, Duplicate the given slide and return the new slide's objectId. (+11 more)

### Community 2 - "Config and Slack Posting"
Cohesion: 0.17
Nodes (16): Config Module, post_demo_message(), _post_via_api(), _post_via_webhook(), Post messages to Slack via webhook or Bot token (chat.postMessage)., POST to SLACK_WEBHOOK_URL. Returns None on success, error string on failure., Post via Slack Web API chat.postMessage. Returns None on success, error string o, Post the standard demo announcement to the team channel. The phrase 'Integration (+8 more)

### Community 3 - "LangGraph Agent Assembly"
Cohesion: 0.14
Nodes (14): create_graph(), _get_model(), Build the sprint-demo LangGraph agent with Drive tools and system prompt., Return the chat model for the configured LLM provider (openai, gemini, or deepse, Build and return the compiled LangGraph agent. Uses Drive service from config., SYSTEM_PROMPT_TEMPLATE, LangGraph agent for sprint demo automation., Drive OAuth Setup Documentation (+6 more)

### Community 4 - "Fill Tools Core"
Cohesion: 0.20
Nodes (14): add_tickets_to_deck, duplicate_slide, fill_ticket_slide, find_deck_in_present, _get_slide_object_id, get_user_existing_ticket_keys, _replace_all_text, _update_ticket_hyperlink (+6 more)

### Community 5 - "Drive LangChain Tools"
Cohesion: 0.18
Nodes (10): Google Drive client and tools for sprint demo automation., copy_file tool, create_drive_tools(), find_template tool, get_latest_sprint_number tool, list_folder tool, move_file tool, Drive API operations exposed as LangChain tools. Use create_drive_tools(service) (+2 more)

## Knowledge Gaps
- **15 isolated node(s):** `str`, `int`, `Slack Integration Test Script`, `list_folder tool`, `copy_file tool` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config Module` connect `Config and Slack Posting` to `Google Auth Layer`, `Slide Fill Pipeline`, `LangGraph Agent Assembly`, `Fill Tools Core`, `Drive LangChain Tools`?**
  _High betweenness centrality (0.452) - this node is a cross-community bridge._
- **Why does `get_drive_service()` connect `Google Auth Layer` to `Config and Slack Posting`, `LangGraph Agent Assembly`, `Fill Tools Core`, `Drive LangChain Tools`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `create_graph()` connect `LangGraph Agent Assembly` to `Google Auth Layer`, `Config and Slack Posting`, `Drive LangChain Tools`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **What connects `Configuration for sprint demo automation. Keys and IDs are loaded from .env only`, `str`, `CLI entry point for filling sprint demo slides with Jira ticket content.  Reads` to the rest of the system?**
  _48 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Google Auth Layer` be split into smaller, more focused modules?**
  _Cohesion score 0.14761904761904762 - nodes in this community are weakly interconnected._
- **Should `LangGraph Agent Assembly` be split into smaller, more focused modules?**
  _Cohesion score 0.13970588235294118 - nodes in this community are weakly interconnected._