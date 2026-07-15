import os
import tempfile

from graph_app.graph import build_graph
from langgraph.checkpoint.sqlite import SqliteSaver
from main import build_state_input, parse_history_limit, run_graph


BASE_STATE = {
    "route": "",
    "messages": [],
    "tool_calls": [],
    "tool_name": "",
    "tool_args": {},
    "tool_call_id": "",
    "tool_result": "",
    "answer": "",
    "answer_streamed": False,
}


def test_parse_history_limit():
    assert parse_history_limit("/history") == 5
    assert parse_history_limit("/history 3") == 3
    assert parse_history_limit("/history nope") == 5
    assert parse_history_limit("/history 99") == 20


def test_graph_local_fallback_persists_checkpoint(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False).name

    try:
        with SqliteSaver.from_conn_string(db) as checkpointer:
            app = build_graph(checkpointer=checkpointer)
            config = {
                "configurable": {"thread_id": "pytest-thread"},
                "recursion_limit": 12,
            }
            state_input = {
                **BASE_STATE,
                "user_input": "hello",
                "memory": [],
            }

            result = run_graph(app, state_input, config, False, False)

            assert "hello" in result["answer"]
            assert len(result["memory"]) == 2
            assert app.get_state(config).values["memory"] == result["memory"]
            assert len(list(app.get_state_history(config, limit=3))) == 3
    finally:
        os.unlink(db)


def test_build_state_input_only_initializes_memory_once(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    db = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False).name

    try:
        with SqliteSaver.from_conn_string(db) as checkpointer:
            app = build_graph(checkpointer=checkpointer)
            config = {
                "configurable": {"thread_id": "pytest-thread"},
                "recursion_limit": 12,
            }

            first_input = build_state_input(app, config, "first")
            assert first_input["memory"] == []

            run_graph(
                app,
                {**BASE_STATE, "user_input": "first", "memory": []},
                config,
                False,
                False,
            )

            second_input = build_state_input(app, config, "second")
            assert "memory" not in second_input
    finally:
        os.unlink(db)
