# LangGraph Beginner

An incremental LangGraph learning project using DeepSeek, local tools, SQLite checkpoints, streaming graph events, token streaming, graph export, pytest coverage, and GitHub Actions CI.

## Run

```powershell
python main.py
```

Useful commands:

```text
/about
/config
/tools
/tool calculator
/state
/memory
/history 8
/graph
```

## Configuration

Copy `.env.example` to `.env`, then set your DeepSeek key:

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

## LangSmith

This project can send DeepSeek/OpenAI-compatible model traces to LangSmith.

1. Create a LangSmith API key at [smith.langchain.com](https://smith.langchain.com).
2. Put these values in `.env`:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=langgraph-beginner
```

3. Run the agent:

```powershell
python main.py
```

4. Ask a question that calls the DeepSeek model. The trace will appear in the LangSmith project named `langgraph-beginner`.

If your LangSmith account is outside the default US region, also set `LANGSMITH_ENDPOINT`.

## Test

```powershell
python -m pytest
```

The tests do not call the DeepSeek API. They cover local tools, helper logic, streaming parsing, checkpoint behavior, and CLI helper functions.

## CI

GitHub Actions runs `python -m pytest` on every push and pull request.

## Project Files

```text
README.md           Human-facing project overview
AGENTS.md           Agent-facing development guide
PROJECT_CONTEXT.md  Current technical status and handoff summary
CHANGELOG.md        Learning-version history
```

## Completion Standard

This is now a complete beginner-level LangGraph agent when it can:

- call a real model through the DeepSeek API
- trace model calls to LangSmith
- select and execute multiple local tools
- loop through model -> tool -> model until a final answer is ready
- persist memory through SQLite checkpoints
- stream graph events and final answer tokens
- inspect state, memory, history, tools, and graph structure from the CLI
- run automated tests locally and in GitHub Actions

Further versions should be treated as productization work, not required beginner-agent fundamentals.
