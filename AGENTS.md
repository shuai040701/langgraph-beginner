# AGENTS.md

This file is for Codex or any future coding agent working on this repository.

## Project Shape

This is a beginner-level LangGraph agent project that is now evolving toward a marketable AI sales-frontdesk agent. It is intentionally small, readable, and incremental. Prefer clear learning value and sellable workflows over heavy abstractions.

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

## Product Direction

The current commercial direction is an AI sales frontdesk for local service businesses.

Core workflow:

```text
customer inquiry/import -> qualify lead -> draft reply -> record lead -> sync Feishu -> create follow-up plan -> sales report
```

Start with high-ticket industries such as dental, medical beauty, renovation, study abroad, immigration, legal consulting, B2B services, and SaaS.

## Editing Rules

- Keep changes small and beginner-readable.
- Follow the existing module boundaries.
- Add new tools in `src/graph_app/tools.py` through `TOOL_REGISTRY`.
- Keep sales-frontdesk tools deterministic enough to test locally.
- `record_lead` writes to `data/leads.jsonl` by default; use `LEADS_DB` in tests or custom runs.
- `import_leads` supports CSV, JSONL, and JSON lead intake with common field aliases.
- Feishu sync is optional and controlled by `FEISHU_SYNC_ENABLED`.
- `sync_lead_to_feishu` uses tenant access token auth and Bitable record creation through Feishu Open API.
- Feishu Bitable writes require `bitable:app` or `base:record:create` app permission.
- Users can run `powershell -ExecutionPolicy Bypass -File .\scripts\setup_feishu_env.ps1` to configure Feishu values in `.env`.
- Users can run `/feishu` and `/feishu test` from the CLI to validate Feishu sync.
- `generate_sales_report` and `list_hot_leads` read from the same JSONL lead ledger.
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
- Feishu base / CRM lead sync
- lead import from ad/form exports
- sales daily report
- RAG over service catalogs and price sheets
- Docker packaging
- domain-specific tools

Avoid adding these all at once. Pick one direction per version.
