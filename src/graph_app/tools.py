import ast
import operator
from datetime import datetime
from zoneinfo import ZoneInfo


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
    if name == "calculator":
        expression = str(args.get("expression", "")).strip()
        return str(safe_calculate(expression))

    if name == "text_stats":
        text = str(args.get("text", ""))
        return text_stats(text)

    if name == "current_time":
        timezone = str(args.get("timezone", "Asia/Shanghai")).strip() or "Asia/Shanghai"
        return current_time(timezone)

    return f"未知工具：{name}"


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
