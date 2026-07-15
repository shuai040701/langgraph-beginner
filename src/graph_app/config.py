import os
from dataclasses import dataclass
from pathlib import Path


APP_VERSION = "v18"
APP_TITLE = "LangGraph Beginner"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_THREAD_ID = "demo-thread"
DEFAULT_RECURSION_LIMIT = 12
DEFAULT_CHECKPOINT_DB = Path("data/checkpoints.sqlite")
DEFAULT_GRAPH_MERMAID_FILE = Path("docs/langgraph.mmd")
DEFAULT_LANGSMITH_PROJECT = "langgraph-beginner"


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    checkpoint_db: Path
    graph_mermaid_file: Path
    default_thread_id: str
    recursion_limit: int
    deepseek_base_url: str
    deepseek_model: str
    trace_default: bool
    token_stream_default: bool
    langsmith_tracing: bool
    langsmith_project: str
    langsmith_endpoint: str

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "AppConfig":
        root = project_root or Path.cwd()
        return cls(
            project_root=root,
            checkpoint_db=resolve_path(root, os.getenv("CHECKPOINT_DB"), DEFAULT_CHECKPOINT_DB),
            graph_mermaid_file=resolve_path(
                root,
                os.getenv("GRAPH_MERMAID_FILE"),
                DEFAULT_GRAPH_MERMAID_FILE,
            ),
            default_thread_id=os.getenv("DEFAULT_THREAD_ID", DEFAULT_THREAD_ID),
            recursion_limit=parse_int_env("RECURSION_LIMIT", DEFAULT_RECURSION_LIMIT),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
            trace_default=parse_bool_env("TRACE_DEFAULT", True),
            token_stream_default=parse_bool_env("TOKEN_STREAM_DEFAULT", True),
            langsmith_tracing=parse_bool_env("LANGSMITH_TRACING", False),
            langsmith_project=os.getenv("LANGSMITH_PROJECT", DEFAULT_LANGSMITH_PROJECT),
            langsmith_endpoint=os.getenv("LANGSMITH_ENDPOINT", ""),
        )


def resolve_path(root: Path, raw_path: str | None, default: Path) -> Path:
    path = Path(raw_path) if raw_path else default
    if path.is_absolute():
        return path
    return root / path


def parse_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def parse_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return max(1, value)
