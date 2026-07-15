from pathlib import Path

from graph_app.config import AppConfig, parse_bool_env, parse_int_env


def test_app_config_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("DEFAULT_THREAD_ID", "custom-thread")
    monkeypatch.setenv("RECURSION_LIMIT", "7")
    monkeypatch.setenv("CHECKPOINT_DB", "tmp/checkpoints.sqlite")
    monkeypatch.setenv("GRAPH_MERMAID_FILE", "tmp/graph.mmd")
    monkeypatch.setenv("TRACE_DEFAULT", "false")
    monkeypatch.setenv("TOKEN_STREAM_DEFAULT", "yes")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_PROJECT", "custom-langsmith-project")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://example.langsmith.test")

    config = AppConfig.from_env(tmp_path)

    assert config.default_thread_id == "custom-thread"
    assert config.recursion_limit == 7
    assert config.checkpoint_db == tmp_path / "tmp/checkpoints.sqlite"
    assert config.graph_mermaid_file == tmp_path / "tmp/graph.mmd"
    assert config.trace_default is False
    assert config.token_stream_default is True
    assert config.langsmith_tracing is True
    assert config.langsmith_project == "custom-langsmith-project"
    assert config.langsmith_endpoint == "https://example.langsmith.test"


def test_app_config_accepts_absolute_paths(monkeypatch, tmp_path):
    db_path = tmp_path / "absolute.sqlite"
    monkeypatch.setenv("CHECKPOINT_DB", str(db_path))

    config = AppConfig.from_env(Path("unused"))

    assert config.checkpoint_db == db_path


def test_parse_env_helpers(monkeypatch):
    monkeypatch.setenv("BOOL_VALUE", "on")
    monkeypatch.setenv("INT_VALUE", "not-an-int")

    assert parse_bool_env("BOOL_VALUE", False) is True
    assert parse_bool_env("MISSING_BOOL", True) is True
    assert parse_int_env("INT_VALUE", 12) == 12
    assert parse_int_env("MISSING_INT", 8) == 8
