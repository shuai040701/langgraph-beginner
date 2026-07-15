# Project Context

## Current Status

This repository is a complete beginner-level LangGraph agent project. It started as a minimal routing graph and has evolved into a CLI-based agent with DeepSeek model access, local tools, multi-step tool loops, persistent checkpoint memory, streaming output, graph inspection, tests, and CI.

Current application version in code: `v18`

Latest local commit at the time this context was written:

```text
4ec723c Add app configuration layer
```

The working tree was clean before this context file and the small `tools.py` text cleanup were added.

## What The Agent Can Do

- Call DeepSeek through an OpenAI-compatible API.
- Send model-call traces to LangSmith when tracing is enabled.
- Use local tools through LangGraph tool calls.
- Run multi-step model -> tool -> model loops.
- Persist conversation state with SQLite checkpoints.
- Stream LangGraph node events.
- Stream final answer tokens.
- Inspect state, memory, checkpoint history, tools, config, and graph structure from the CLI.
- Export the LangGraph structure as Mermaid.
- Run a pytest suite locally and through GitHub Actions.

## Core Runtime Flow

The graph is defined in `src/graph_app/graph.py`.

Current topology:

```text
START -> agent_node
agent_node -> tool_node       when route == "tool"
agent_node -> save_memory     when route != "tool"
tool_node -> agent_node
save_memory -> END
```

This is the important loop:

```text
agent_node -> tool_node -> agent_node
```

It lets the model request a tool, receive the result, then decide whether another tool is needed or whether it can produce a final answer.

## Important Files

```text
main.py
```

CLI entry point. Handles commands, SQLite checkpointer setup, streaming graph events, token streaming toggle, config display, graph export, and thread switching.

```text
src/graph_app/config.py
```

Central app configuration. Reads environment variables and resolves paths.

```text
src/graph_app/graph.py
```

Builds and compiles the LangGraph `StateGraph`.

```text
src/graph_app/state.py
```

Defines `AppState`, including user input, messages, tool calls, tool results, answer, and streaming metadata.

```text
src/graph_app/nodes.py
```

Implements graph nodes:

- `agent_node`
- `tool_node`
- `save_memory`

```text
src/graph_app/llm.py
```

DeepSeek API integration, tool-call parsing, streaming response collection, forced `text_stats` rule, and message construction.

```text
src/graph_app/tools.py
```

Central tool registry and local tool implementations.

```text
docs/langgraph.mmd
```

Generated Mermaid graph.

```text
tests/
```

Pytest suite.

```text
.github/workflows/tests.yml
```

GitHub Actions workflow running `python -m pytest`.

## Tools

Tools are centralized in `TOOL_REGISTRY` in `src/graph_app/tools.py`.

Current tools:

```text
calculator
```

Evaluates simple arithmetic expressions safely with Python AST.

```text
text_stats
```

Counts characters, non-whitespace characters, whitespace-separated words, and lines.

```text
current_time
```

Returns the current time for an IANA timezone.

The model-facing tool schemas are generated from the same registry via `get_tool_schemas()`, so runtime execution and LLM schema stay in sync.

## Configuration

Copy `.env.example` to `.env`.

Current supported environment variables:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEFAULT_THREAD_ID=demo-thread
RECURSION_LIMIT=12
CHECKPOINT_DB=data/checkpoints.sqlite
GRAPH_MERMAID_FILE=docs/langgraph.mmd
TRACE_DEFAULT=true
TOKEN_STREAM_DEFAULT=true
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=langgraph-beginner
# LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

Runtime config is surfaced in the CLI with:

```text
/config
```

## CLI Commands

```text
/help             Show commands
/about            Show project capabilities and completion standard
/config           Show active configuration
/tools            List registered tools
/tool name        Show one tool's description and parameters
/graph            Export Mermaid graph
/state            Show current thread state summary
/memory           Show current thread memory
/history [n]      Show recent checkpoint history, default 5
/thread name      Switch or restore a thread
/reset            Create a new random thread
/trace on|off     Toggle LangGraph node event streaming
/tokens on|off    Toggle final answer token streaming
exit              Quit
```

## Persistence

The app uses `SqliteSaver` from `langgraph-checkpoint-sqlite`.

Default checkpoint database:

```text
data/checkpoints.sqlite
```

The `data/` folder and SQLite files are ignored by Git.

Memory is scoped by `thread_id`. Use `/thread name` to switch threads and `/reset` to create a new random thread.

## Streaming

There are two streaming layers:

```text
Graph event streaming
```

Controlled by `/trace on|off`. Shows node-level updates such as agent decisions, tool execution, and memory save.

```text
Final answer token streaming
```

Controlled by `/tokens on|off`. Uses DeepSeek streaming responses and prints final answer tokens as they arrive.

The code preserves DeepSeek `reasoning_content` because DeepSeek thinking mode requires it to be passed back in follow-up API calls.

## Tests

Run:

```powershell
python -m pytest
```

Current known passing result:

```text
19 passed
```

Coverage areas:

- config parsing
- LangSmith config parsing
- tool execution
- tool schema registry
- forced `text_stats` rule
- streaming content parsing
- streaming tool-call parsing
- graph local fallback path
- SQLite checkpoint behavior
- CLI helper functions

Tests do not call the real DeepSeek API.

## GitHub / CI

The repo includes GitHub Actions:

```text
.github/workflows/tests.yml
```

It runs:

```text
python -m pytest
```

on push and pull requests.

## Development Timeline

Recent milestones:

```text
v18 Add LangSmith tracing
22b7760 Initial LangGraph DeepSeek agent
3f37c02 Add checkpoint memory
1dcb682 Persist checkpoints with SQLite
c2b4490 Add multi tool agent
53f4241 Add multi step tool loop
e63d5c5 Enforce text stats before derived calculations
82c7722 Preserve DeepSeek reasoning content
a814a8e Stream graph execution events
d25bc10 Stream final answer tokens
f76a419 Add checkpoint inspector commands
cd822c3 Add graph export command
f991c80 Add automated tests
b4046cc Add GitHub Actions tests
f938dff Centralize tool registry
16894e4 Add tool catalog commands
4ec723c Add app configuration layer
```

## Completion Assessment

This project is now a complete beginner-level LangGraph agent.

It satisfies the completion standard:

- real model integration
- local tools
- multi-step tool loop
- durable memory
- observability
- streaming
- config layer
- tests
- CI
- GitHub-ready structure
- optional LangSmith tracing

Further versions should be treated as productization work, not required beginner-agent fundamentals.

## Reasonable Next Steps

If continuing, choose one of these productization directions:

```text
FastAPI service
```

Expose the agent over HTTP.

```text
Web UI
```

Build a small chat interface with thread selection and trace display.

```text
LangSmith tracing
```

Add production-grade observability.

```text
RAG
```

Add document loading, embeddings, and retrieval.

```text
Docker
```

Package the app for repeatable deployment.

```text
More tools
```

Add file, web, or domain-specific tools, keeping them in `TOOL_REGISTRY`.
