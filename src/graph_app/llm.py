import json
import os
from typing import Any


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "计算一个只包含数字、括号和 + - * / // % ** 运算符的数学表达式。",
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
}


def ask_with_tools(user_input: str, memory: list[str]) -> dict[str, Any]:
    if not os.getenv("DEEPSEEK_API_KEY"):
        answer = fallback_answer(user_input, memory)
        return {"route": "final", "answer": answer, "messages": []}

    client = create_client()
    messages = build_messages(user_input, memory)

    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=messages,
            tools=[CALCULATOR_TOOL],
            tool_choice="auto",
            stream=False,
        )
    except Exception as exc:
        return {"route": "final", "answer": f"DeepSeek API 调用失败：{exc}", "messages": messages}

    message = response.choices[0].message
    tool_calls = message.tool_calls or []

    if not tool_calls:
        return {
            "route": "final",
            "answer": message.content or "",
            "messages": [*messages, message_to_dict(message)],
        }

    tool_call = tool_calls[0]
    return {
        "route": "tool",
        "messages": [*messages, message_to_dict(message)],
        "tool_name": tool_call.function.name,
        "tool_args": parse_tool_args(tool_call.function.arguments),
        "tool_call_id": tool_call.id,
        "answer": "",
    }


def ask_final_answer(messages: list[dict[str, Any]]) -> str:
    if not os.getenv("DEEPSEEK_API_KEY"):
        return "本地模式下不会进入工具总结节点。"

    client = create_client()

    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=messages,
            stream=False,
        )
    except Exception as exc:
        return f"DeepSeek API 调用失败：{exc}"

    return response.choices[0].message.content or ""


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
                "如果用户的问题需要准确计算，必须调用 calculator 工具，不要心算。"
                "回答要简洁、具体，并在合适时指出下一步练习。"
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
        "配置 DEEPSEEK_API_KEY 后，这里会切换为 DeepSeek ReAct 工具调用模式。"
    )
