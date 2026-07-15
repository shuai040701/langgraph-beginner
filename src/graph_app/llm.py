import json
import os
import re
from typing import Any

from graph_app.config import (
    APP_VERSION,
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DEFAULT_LANGSMITH_PROJECT,
)
from graph_app.tools import get_tool_schemas


STREAM_TOKENS_ENV = "LANGGRAPH_STREAM_TOKENS"


def ask_with_tools(
    user_input: str,
    memory: list[str],
    messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not os.getenv("DEEPSEEK_API_KEY"):
        answer = fallback_answer(user_input, memory)
        return {"route": "final", "answer": answer, "messages": messages or []}

    current_messages = messages if messages else build_messages(user_input, memory)

    forced_tool = choose_forced_tool(user_input, current_messages)
    if forced_tool:
        return forced_tool

    client = create_client()

    try:
        if should_stream_tokens():
            message = stream_chat_completion(client, current_messages)
        else:
            response = client.chat.completions.create(
                model=get_model(),
                messages=current_messages,
                tools=get_tool_schemas(),
                tool_choice="auto",
                stream=False,
            )
            message = message_to_dict(response.choices[0].message)
    except Exception as exc:
        return {
            "route": "final",
            "answer": f"DeepSeek API 调用失败：{exc}",
            "messages": current_messages,
            "tool_calls": [],
            "answer_streamed": False,
        }

    next_messages = [*current_messages, message]
    tool_calls = parse_message_tool_calls(message.get("tool_calls") or [])

    if not tool_calls:
        return {
            "route": "final",
            "answer": message.get("content") or "",
            "messages": next_messages,
            "tool_calls": [],
            "tool_name": "",
            "tool_args": {},
            "tool_call_id": "",
            "answer_streamed": bool(message.get("_streamed_content")),
        }

    first_tool = tool_calls[0]
    return {
        "route": "tool",
        "messages": next_messages,
        "tool_calls": tool_calls,
        "tool_name": first_tool["name"],
        "tool_args": first_tool["args"],
        "tool_call_id": first_tool["id"],
        "answer": "",
        "answer_streamed": False,
    }


def stream_chat_completion(client: Any, messages: list[dict[str, Any]]) -> dict[str, Any]:
    stream = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        tools=get_tool_schemas(),
        tool_choice="auto",
        stream=True,
    )

    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    tool_call_parts: dict[int, dict[str, Any]] = {}
    printed_content = False

    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        content_delta = getattr(delta, "content", None)
        reasoning_delta = getattr(delta, "reasoning_content", None)
        tool_call_deltas = getattr(delta, "tool_calls", None) or []

        if reasoning_delta:
            reasoning_parts.append(reasoning_delta)

        if content_delta:
            if not printed_content:
                print("助手流式：", end="", flush=True)
                printed_content = True
            print(content_delta, end="", flush=True)
            content_parts.append(content_delta)

        for tool_call_delta in tool_call_deltas:
            index = tool_call_delta.index
            current = tool_call_parts.setdefault(
                index,
                {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                },
            )

            if getattr(tool_call_delta, "id", None):
                current["id"] = tool_call_delta.id

            function_delta = getattr(tool_call_delta, "function", None)
            if function_delta:
                if getattr(function_delta, "name", None):
                    current["function"]["name"] += function_delta.name
                if getattr(function_delta, "arguments", None):
                    current["function"]["arguments"] += function_delta.arguments

    if printed_content:
        print()

    message: dict[str, Any] = {
        "role": "assistant",
        "content": "".join(content_parts) or None,
    }

    if reasoning_parts:
        message["reasoning_content"] = "".join(reasoning_parts)

    if tool_call_parts:
        message["tool_calls"] = [
            tool_call_parts[index]
            for index in sorted(tool_call_parts)
        ]

    if printed_content:
        message["_streamed_content"] = True

    return message


def should_stream_tokens() -> bool:
    return os.getenv(STREAM_TOKENS_ENV) == "1"


def choose_forced_tool(
    user_input: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if has_tool_result(messages, "text_stats"):
        return None

    if not needs_text_stats(user_input):
        return None

    text = extract_quoted_text(user_input)
    if not text:
        return None

    tool_call = {
        "id": "forced_text_stats_1",
        "name": "text_stats",
        "args": {"text": text},
    }
    assistant_message = {
        "role": "assistant",
        "content": None,
        "reasoning_content": "",
        "tool_calls": [
            {
                "id": tool_call["id"],
                "type": "function",
                "function": {
                    "name": "text_stats",
                    "arguments": json.dumps(tool_call["args"], ensure_ascii=False),
                },
            }
        ],
    }

    return {
        "route": "tool",
        "messages": [*messages, assistant_message],
        "tool_calls": [tool_call],
        "tool_name": tool_call["name"],
        "tool_args": tool_call["args"],
        "tool_call_id": tool_call["id"],
        "answer": "",
        "answer_streamed": False,
    }


def needs_text_stats(user_input: str) -> bool:
    keywords = ["统计", "字符", "字数", "非空白", "词数", "行数"]
    return any(keyword in user_input for keyword in keywords)


def extract_quoted_text(user_input: str) -> str:
    patterns = [
        r'"([^"]+)"',
        r"'([^']+)'",
        r"“([^”]+)”",
        r"「([^」]+)」",
    ]
    for pattern in patterns:
        match = re.search(pattern, user_input)
        if match:
            return match.group(1)

    return ""


def has_tool_result(messages: list[dict[str, Any]], tool_name: str) -> bool:
    for message in messages:
        if message.get("role") != "assistant":
            continue

        for tool_call in message.get("tool_calls") or []:
            function = tool_call.get("function") or {}
            if function.get("name") == tool_name:
                return True

    return False


def create_client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("请先运行：pip install -r requirements.txt") from exc

    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
    )

    return wrap_client_for_langsmith(client)


def wrap_client_for_langsmith(client: Any) -> Any:
    if not langsmith_tracing_enabled():
        return client

    if not os.getenv("LANGSMITH_API_KEY"):
        return client

    try:
        from langsmith import wrappers
    except ImportError as exc:
        raise RuntimeError("请先运行：pip install -r requirements.txt") from exc

    os.environ.setdefault("LANGSMITH_PROJECT", DEFAULT_LANGSMITH_PROJECT)

    return wrappers.wrap_openai(
        client,
        tracing_extra={
            "metadata": {
                "app": "langgraph-beginner",
                "app_version": APP_VERSION,
                "ls_provider": "deepseek",
                "ls_model_name": get_model(),
            }
        },
    )


def langsmith_tracing_enabled() -> bool:
    return os.getenv("LANGSMITH_TRACING", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_model() -> str:
    return os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL)


def build_messages(user_input: str, memory: list[str]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "你是一个帮助用户学习 LangGraph 的中文助教。"
                "如果用户的问题需要准确计算、文本统计或当前时间，必须调用对应工具。"
                "如果一个问题需要多个步骤，可以连续调用工具，直到信息足够再回答。"
                "尤其注意：涉及字符数、非空白字符数、词数或行数时，必须先使用 text_stats。"
                "涉及基于工具结果的算术时，必须再使用 calculator，不要心算。"
                "不要编造工具结果。回答要简洁、具体。"
            ),
        }
    ]

    for item in memory[-6:]:
        if item.startswith("用户："):
            messages.append({"role": "user", "content": item.removeprefix("用户：")})
        elif item.startswith("助手："):
            messages.append({"role": "assistant", "content": item.removeprefix("助手：")})

    messages.append({"role": "user", "content": user_input})
    return messages


def message_to_dict(message: Any) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        data = message.model_dump(exclude_none=True)
    else:
        data = dict(message)

    return {
        key: value
        for key, value in data.items()
        if key in {"role", "content", "reasoning_content", "tool_calls"}
    }


def parse_message_tool_calls(raw_tool_calls: list[Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    for raw_call in raw_tool_calls:
        if isinstance(raw_call, dict):
            function = raw_call.get("function") or {}
            calls.append(
                {
                    "id": raw_call.get("id", ""),
                    "name": function.get("name", ""),
                    "args": parse_tool_args(function.get("arguments", "{}")),
                }
            )
        else:
            calls.append(
                {
                    "id": raw_call.id,
                    "name": raw_call.function.name,
                    "args": parse_tool_args(raw_call.function.arguments),
                }
            )

    return calls


def parse_tool_args(raw_args: str) -> dict[str, Any]:
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        return {"expression": raw_args}

    if isinstance(args, dict):
        return args

    return {"expression": str(args)}


def fallback_answer(user_input: str, memory: list[str]) -> str:
    turns = len(memory) // 2
    return (
        f"本地回复：你说的是「{user_input}」。"
        f"我已经记住了前面 {turns} 轮对话。"
        "配置 DEEPSEEK_API_KEY 后，这里会切换为 DeepSeek 多步工具循环模式。"
    )
