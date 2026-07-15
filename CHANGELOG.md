# Changelog

All notable learning-version changes for this project are recorded here.

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
