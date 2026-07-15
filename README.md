# LangGraph Beginner

An incremental LangGraph learning project using DeepSeek, local tools, SQLite checkpoints, streaming graph events, token streaming, graph export, and pytest coverage.

## Run

```powershell
python main.py
```

## Test

```powershell
python -m pytest
```

The tests do not call the DeepSeek API. They cover local tools, helper logic, streaming parsing, checkpoint behavior, and CLI helper functions.
