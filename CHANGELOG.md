# Changelog

All notable learning-version changes for this project are recorded here.

## v23 - Lead Import Pipeline

- Added `/import 路径` CLI command for batch lead intake.
- Added `import_leads` tool for CSV, JSONL, and JSON lead imports.
- Added field alias mapping for common form/export column names.
- Imported leads are automatically scored, recorded locally, and synced to Feishu when enabled.
- Added `examples/sample_leads.csv` for quick local testing.
- Added tests for CSV and JSONL lead import.

## v22 - Feishu Sync Verification

- Added `/feishu` CLI command for masked Feishu config inspection.
- Added `/feishu tables`, `/feishu fields`, and `/feishu payload` diagnostics for Bitable schema/payload debugging.
- Added `/feishu test` CLI command to write one test lead into Feishu Bitable.
- Added `test_feishu_sync` tool for model-driven sync verification.
- Documented required Feishu Bitable write permissions: `bitable:app` or `base:record:create`.
- Added clearer diagnostics for `WrongTableId`, view IDs (`vew...`), and `WrongRequestBody`.
- Added tests for Feishu config masking and test-record sync.

## v21 - Feishu Bitable Sync

- Added optional Feishu Bitable lead sync.
- Added `sync_lead_to_feishu` tool.
- `record_lead` now keeps the local JSONL ledger and can also sync to Feishu when `FEISHU_SYNC_ENABLED=true`.
- Added Feishu environment variables and default Bitable field mapping.
- Added tests for Feishu field mapping, missing config, and mocked record creation.

## v20 - Sales Report Tools

- Added `generate_sales_report` for boss-readable lead summaries.
- Added `list_hot_leads` for recent A-grade lead follow-up.
- Updated the sales-frontdesk prompt to use report tools for daily summaries and lead dashboards.
- Added tests for lead reports and hot-lead listing.

## v19 - Sales Frontdesk Agent MVP

- Started the marketable AI sales-frontdesk direction for local service businesses.
- Added lead qualification, lead recording, sales reply drafting, and follow-up planning tools.
- Added local `data/leads.jsonl` lead storage with `LEADS_DB` override for tests/custom runs.
- Updated the system prompt to prioritize sales-frontdesk workflows.
- Added tests for sales tools.

## v18 - LangSmith Tracing

- Added optional LangSmith tracing for DeepSeek/OpenAI-compatible model calls.
- Wrapped the OpenAI-compatible DeepSeek client with `langsmith.wrappers.wrap_openai`.
- Added LangSmith environment variables to `.env.example`.
- Added `/config` visibility for LangSmith tracing state.
- Added tests for LangSmith configuration parsing.

## v17 - App Configuration Layer

- Added centralized app configuration in `src/graph_app/config.py`.
- Moved environment parsing and default paths out of scattered call sites.
- Added `/config` CLI inspection.

## v16 - Tool Catalog Commands

- Added CLI commands for listing tools and inspecting one tool.
- Made registered tools easier to discover while running the app.

## v15 - Central Tool Registry

- Centralized local tools in `TOOL_REGISTRY`.
- Generated DeepSeek tool schemas from the same registry used for execution.
- Reduced drift between model-facing schemas and runtime behavior.

## v14 - GitHub Actions

- Added GitHub Actions workflow for automated tests.
- CI runs `python -m pytest` on push and pull requests.

## v13 - Automated Tests

- Added pytest coverage for core helper logic.
- Covered tools, graph behavior, streaming parsers, checkpoint behavior, and CLI helpers.

## v12 - Graph Export

- Added Mermaid graph export.
- Added CLI support for writing graph structure to `docs/langgraph.mmd`.

## v11 - Checkpoint Inspection

- Added CLI commands to inspect current state, memory, and checkpoint history.
- Improved visibility into SQLite-backed conversations.

## v10 - Token Streaming

- Added final answer token streaming from DeepSeek responses.
- Added `/tokens on|off`.

## v9 - Graph Event Streaming

- Added LangGraph node-event streaming.
- Added `/trace on|off`.

## v8 - Multi-Step Tool Loop

- Added repeated model -> tool -> model execution.
- Allowed the agent to use more than one tool before answering.

## v7 - DeepSeek Reasoning Compatibility

- Preserved DeepSeek `reasoning_content` in follow-up API messages.
- Fixed the invalid request error caused by dropping reasoning content in thinking mode.

## v6 - Forced Text Stats Rule

- Added a deterministic guard for text-statistics requests.
- Ensured text counting uses `text_stats` before derived calculations.

## v5 - Multi-Tool Agent

- Added multiple local tools.
- Expanded beyond a single calculator-style action.

## v4 - SQLite Checkpoint Persistence

- Switched checkpoint memory to SQLite.
- Added durable thread state in `data/checkpoints.sqlite`.

## v3 - Checkpoint Memory

- Added LangGraph checkpoint-based memory.
- Introduced thread-scoped conversation state.

## v2 - DeepSeek Model Integration

- Added DeepSeek API support through an OpenAI-compatible client.
- Added local fallback behavior when no API key is configured.

## v1 - Initial LangGraph Agent

- Created the first runnable LangGraph beginner agent.
- Added a minimal graph, CLI loop, and local response path.
