# LangGraph Beginner

An incremental LangGraph project using DeepSeek, local tools, SQLite checkpoints, streaming graph events, token streaming, graph export, pytest coverage, GitHub Actions CI, and a v22 sales-frontdesk agent direction.

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
/tool qualify_lead
/state
/memory
/history 8
/graph
```

## Sales Frontdesk MVP

Version `v20` turns the beginner agent into a marketable "AI sales frontdesk" for local service businesses.

The first sellable workflow is:

```text
customer inquiry -> qualify lead -> draft reply -> record lead -> create follow-up plan -> sales report
```

Current sales tools:

```text
qualify_lead          Score lead quality and classify A/B/C intent
record_lead           Save a lead to data/leads.jsonl
draft_sales_reply     Draft a customer-facing reply
create_followup_plan  Create a sales follow-up cadence
generate_sales_report Create a boss-readable lead report
list_hot_leads        List recent A-grade leads
import_leads          Batch import leads from CSV/JSONL/JSON
sync_lead_to_feishu   Sync one lead to Feishu Bitable
test_feishu_sync      Write one test lead to Feishu Bitable
```

Example prompt:

```text
客户来自网页表单：上海牙科客户，想做牙齿矫正，预算2万，本周想预约，微信 abc123。请判断意向等级，记录线索，生成回复和跟进计划。
```

After recording leads, ask:

```text
请生成今天的销售线索日报，并列出最需要优先跟进的高意向线索。
```

## Lead Import

Version `v23` adds batch lead intake. This is useful when leads come from ads, forms, manual spreadsheets, or exported CRM data.

Try the included sample file:

```text
/import examples/sample_leads.csv
```

Supported formats:

```text
.csv
.jsonl
.json
```

Recommended columns:

```text
客户名称,联系方式,行业,需求,预算,时间计划,城市,来源,线索等级,备注
```

Common aliases such as `姓名`, `手机`, `业务`, `咨询内容`, `渠道`, `name`, `phone`, and `message` are also recognized. If a lead has no `线索等级`, the agent scores it automatically before recording it.

## Feishu Bitable

Version `v21` can sync leads to Feishu Bitable. Local JSONL storage remains the default fallback.

Create a Feishu Bitable table with these columns:

```text
创建时间
客户名称
联系方式
行业
需求
预算
时间计划
城市
来源
线索等级
备注
```

Then configure `.env`:

```env
FEISHU_SYNC_ENABLED=true
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_BITABLE_APP_TOKEN=your_bitable_app_token
FEISHU_BITABLE_TABLE_ID=your_table_id
```

When `FEISHU_SYNC_ENABLED=true`, `record_lead` writes to `data/leads.jsonl` and also attempts to create one Feishu Bitable record.
`FEISHU_BITABLE_TABLE_ID` must be the table ID, usually starting with `tbl`. Do not use the view ID that starts with `vew`.

Your Feishu app must have at least one of these permissions approved and published:

```text
bitable:app
base:record:create
```

The app also needs access to the target Bitable file. If `/feishu test` returns `HTTP 403` with `code=91403`, add the self-built Feishu app as a collaborator/authorized app for that Bitable, and confirm `FEISHU_BITABLE_APP_TOKEN` and `FEISHU_BITABLE_TABLE_ID` come from the same table.

If `/feishu fields` returns `WrongTableId`, check `FEISHU_BITABLE_TABLE_ID` first. This usually means a view ID such as `vew...` was configured instead of the real table ID such as `tbl...`.
Run `/feishu tables` to list the available table IDs in the configured Bitable file, then copy the matching `tbl...` value into `.env`.

If `/feishu test` returns `WrongRequestBody`, check that the Bitable column names match the `FEISHU_FIELD_*` values and that field types match the values being written. The app now writes `创建时间` as a millisecond timestamp for Feishu date fields. If needed, temporarily set this to skip the date column:

```env
FEISHU_FIELD_CREATED_AT=__skip__
```

Recommended Bitable fields:

```text
创建时间: date/time, or set `FEISHU_FIELD_CREATED_AT=__skip__` to skip this field
客户名称: text
联系方式: text
行业: text
需求: text
预算: text
时间计划: text
城市: text
来源: text
线索等级: text
备注: text
```

You can configure it with the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_feishu_env.ps1
```

The script writes these values into the project root `.env` file:

```env
FEISHU_SYNC_ENABLED=true
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_BITABLE_APP_TOKEN=your_bitable_app_token
FEISHU_BITABLE_TABLE_ID=your_table_id
```

After configuration, verify it in the CLI:

```text
/feishu
/feishu tables
/feishu fields
/feishu test
```

`/feishu` prints a masked config summary. `/feishu tables` lists table IDs. `/feishu fields` lists fields for the configured table. `/feishu test` writes one test lead to the configured Bitable table.

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

This project can send DeepSeek/OpenAI-compatible model traces to LangSmith. Keep it off during normal practice, then turn it on when you want to inspect model calls, tool calls, latency, or prompt changes.

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

For daily local practice, leave tracing off:

```env
LANGSMITH_TRACING=false
```

During one running session, you can also use:

```text
/langsmith on
/langsmith off
```

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

Further versions should focus on productization: Feishu base integration, web form intake, CRM sync, daily sales report, and a small web dashboard.
