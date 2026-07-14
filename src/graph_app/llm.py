import json
import os
import re
from typing import Any


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算只包含数字、括号和 + - * / // % ** 运算符的数学表达式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "需要计算的数学表达式，例如：1 + 2 * (3 + 4)",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_stats",
            "description": "统计文本的字符数、非空白字符数、按空白分隔的词数和行数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要统计的文本。",
                    }
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "获取指定 IANA 时区的当前时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA 时区名，例如 Asia/Shanghai 或 America/New_York。",
                    }
                },
                "required": ["timezone"],
            },
        },
    },
]


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
        response = client.chat.completions.create(
            model=get_model(),
            messages=current_messages,
            tools=TOOLS,
            tool_choice="auto",
            stream=False,
        )
    except Exception as exc:
        return {
            "route": "final",
            "answer": f"DeepSeek API 调用失败：{exc}",
            "messages": current_messages,
            "tool_calls": [],
        }

    message = response.choices[0].message
    next_messages = [*current_messages, message_to_dict(message)]
    tool_calls = parse_tool_calls(message.tool_calls or [])

    if not tool_calls:
        return {
            "route": "final",
            "answer": message.content or "",
            "messages": next_messages,
            "tool_calls": [],
            "tool_name": "",
            "tool_args": {},
            "tool_call_id": "",
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
    }


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

    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
    )


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
        if key in {"role", "content", "tool_calls"}
    }


def parse_tool_calls(raw_tool_calls: list[Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    for raw_call in raw_tool_calls:
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
