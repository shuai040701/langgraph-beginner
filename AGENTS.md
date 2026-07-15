# AGENTS.md

This file is for Codex or any future coding agent working on this repository.

## Project Shape

This is a beginner-level LangGraph agent project. It is intentionally small, readable, and incremental. Prefer clear learning value over heavy abstractions.

Core runtime:

```text
main.py
src/graph_app/
tests/
docs/langgraph.mmd
```

The graph loop is:

```text
START -> agent_node -> tool_node -> agent_node -> save_memory -> END
```

`tool_node` is only entered when `agent_node` sets `route` to `tool`.

## Current Completion Level

The project already satisfies the beginner-agent goal:

- DeepSeek API integration
- local tools
- multi-step tool loop
- SQLite checkpoint memory
- thread switching
- graph event streaming
- final answer token streaming
- LangSmith tracing for DeepSeek/OpenAI-compatible calls
- CLI inspection commands
- Mermaid graph export
- pytest coverage
- GitHub Actions CI

Future work should be treated as productization or specialization, not required beginner fundamentals.

## Editing Rules

- Keep changes small and beginner-readable.
- Follow the existing module boundaries.
- Add new tools in `src/graph_app/tools.py` through `TOOL_REGISTRY`.
- Keep model/API behavior in `src/graph_app/llm.py`.
- Keep graph topology in `src/graph_app/graph.py`.
- Keep CLI command parsing in `main.py`.
- Do not commit `.env`, SQLite checkpoint files, caches, or virtual environments.
- Preserve DeepSeek `reasoning_content` handling unless the API behavior is deliberately changed and retested.
- Keep LangSmith tracing optional. It should only upload traces when `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` is configured.
- When changing tool-call behavior, run the full test suite.

## Commands

Run locally:

```powershell
python main.py
```

Run tests:

```powershell
python -m pytest
```

Compile check:

```powershell
python -m compileall main.py src tests
```

Export graph from the CLI:

```text
/graph
```

## Configuration

Environment variables are read by `src/graph_app/config.py`.

Important variables:

```env
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEFAULT_THREAD_ID=demo-thread
RECURSION_LIMIT=12
CHECKPOINT_DB=data/checkpoints.sqlite
GRAPH_MERMAID_FILE=docs/langgraph.mmd
TRACE_DEFAULT=true
TOKEN_STREAM_DEFAULT=true
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=langgraph-beginner
LANGSMITH_ENDPOINT=
```

## Testing Guidance

Tests should not call the real DeepSeek API. Use local fallback paths, parsing helpers, and isolated SQLite temp files.

Before handing off code changes, run:

```powershell
python -m compileall main.py src tests
python -m pytest
```

## Good Next Versions

Reasonable next directions:

- FastAPI wrapper
- web chat UI
- LangSmith tracing
- RAG over local documents
- Docker packaging
- domain-specific tools

Avoid adding these all at once. Pick one direction per version.
