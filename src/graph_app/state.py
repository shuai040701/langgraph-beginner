from typing import Any, Literal, TypedDict


class AppState(TypedDict):
    user_input: str
    route: Literal["tool", "final", ""]
    memory: list[str]
    messages: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    tool_name: str
    tool_args: dict[str, Any]
    tool_call_id: str
    tool_result: str
    answer: str
    answer_streamed: bool
