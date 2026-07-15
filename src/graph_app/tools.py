import ast
import operator
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], str]

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def run_tool(name: str, args: dict) -> str:
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return f"未知工具：{name}"

    return tool.handler(args)


def get_tool_schemas() -> list[dict[str, Any]]:
    return [tool.schema() for tool in TOOL_REGISTRY.values()]


def _run_calculator(args: dict[str, Any]) -> str:
    expression = str(args.get("expression", "")).strip()
    return str(safe_calculate(expression))


def _run_text_stats(args: dict[str, Any]) -> str:
    text = str(args.get("text", ""))
    return text_stats(text)


def _run_current_time(args: dict[str, Any]) -> str:
    timezone = str(args.get("timezone", "Asia/Shanghai")).strip() or "Asia/Shanghai"
    return current_time(timezone)


def safe_calculate(expression: str) -> float | int:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


def text_stats(text: str) -> str:
    chars = len(text)
    non_space_chars = len("".join(text.split()))
    words = len(text.split())
    lines = text.count("\n") + 1 if text else 0

    return (
        f"字符数：{chars}；"
        f"非空白字符数：{non_space_chars}；"
        f"按空白分隔的词数：{words}；"
        f"行数：{lines}"
    )


def current_time(timezone: str) -> str:
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("Asia/Shanghai")
        timezone = "Asia/Shanghai"

    now = datetime.now(tz)
    return f"{timezone} 当前时间：{now:%Y-%m-%d %H:%M:%S}"


def _eval_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        operand = _eval_node(node.operand)
        return _OPERATORS[type(node.op)](operand)

    raise ValueError("Only simple arithmetic expressions are supported.")


TOOL_REGISTRY = {
    "calculator": ToolSpec(
        name="calculator",
        description="计算只包含数字、括号和 + - * / // % ** 运算符的数学表达式。",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "需要计算的数学表达式，例如：1 + 2 * (3 + 4)",
                }
            },
            "required": ["expression"],
        },
        handler=_run_calculator,
    ),
    "text_stats": ToolSpec(
        name="text_stats",
        description="统计文本的字符数、非空白字符数、按空白分隔的词数和行数。",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "需要统计的文本。",
                }
            },
            "required": ["text"],
        },
        handler=_run_text_stats,
    ),
    "current_time": ToolSpec(
        name="current_time",
        description="获取指定 IANA 时区的当前时间。",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA 时区名，例如 Asia/Shanghai 或 America/New_York。",
                }
            },
            "required": ["timezone"],
        },
        handler=_run_current_time,
    ),
}
