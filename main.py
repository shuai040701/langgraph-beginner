import os
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from graph_app.graph import build_graph
from graph_app.llm import STREAM_TOKENS_ENV
from langgraph.checkpoint.sqlite import SqliteSaver


PROJECT_ROOT = Path(__file__).parent
CHECKPOINT_DB = PROJECT_ROOT / "data" / "checkpoints.sqlite"
GRAPH_MERMAID_FILE = PROJECT_ROOT / "docs" / "langgraph.mmd"
DEFAULT_THREAD_ID = "demo-thread"


def main():
    if load_dotenv:
        load_dotenv()

    CHECKPOINT_DB.parent.mkdir(exist_ok=True)

    with SqliteSaver.from_conn_string(str(CHECKPOINT_DB)) as checkpointer:
        app = build_graph(checkpointer=checkpointer)
        thread_id = DEFAULT_THREAD_ID
        trace_enabled = True
        token_stream_enabled = True

        print("LangGraph Beginner v12 - Graph Export")
        print(f"记忆数据库：{CHECKPOINT_DB}")
        print_status()
        print_help()

        while True:
            user_input = input(f"\n你[{thread_id}]：").strip()

            if user_input.lower() in {"exit", "quit", "q"}:
                print("再见。")
                break

            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 12,
            }

            if user_input == "/help":
                print_help()
                continue

            if user_input == "/graph":
                export_graph(app)
                continue

            if user_input == "/state":
                print_state(app, config)
                continue

            if user_input == "/memory":
                print_memory(app, config)
                continue

            if user_input.startswith("/history"):
                print_history(app, config, user_input)
                continue

            if user_input == "/reset":
                thread_id = f"demo-thread-{uuid.uuid4().hex[:8]}"
                print(f"已切换到新会话：{thread_id}")
                continue

            if user_input.startswith("/thread "):
                next_thread_id = user_input.removeprefix("/thread ").strip()
                if next_thread_id:
                    thread_id = next_thread_id
                    print(f"已切换到会话：{thread_id}")
                else:
                    print("用法：/thread 你的会话名")
                continue

            if user_input.startswith("/trace "):
                trace_enabled = user_input.removeprefix("/trace ").strip().lower() != "off"
                print(f"事件流：{'开启' if trace_enabled else '关闭'}")
                continue

            if user_input.startswith("/tokens "):
                token_stream_enabled = user_input.removeprefix("/tokens ").strip().lower() != "off"
                print(f"回答流式输出：{'开启' if token_stream_enabled else '关闭'}")
                continue

            state_input = build_state_input(app, config, user_input)
            result = run_graph(app, state_input, config, trace_enabled, token_stream_enabled)

            if result.get("tool_result"):
                print(f"工具结果：\n{result['tool_result']}")
            if not result.get("answer_streamed"):
                print(f"助手：{result['answer']}")


def print_help():
    print("命令：")
    print("  /help             显示命令")
    print("  /graph            导出 Mermaid 图到 docs/langgraph.mmd")
    print("  /state            查看当前 thread 的状态摘要")
    print("  /memory           查看当前 thread 的对话记忆")
    print("  /history [n]      查看最近 n 条 checkpoint，默认 5")
    print("  /thread 名称      切换或恢复指定会话")
    print("  /reset            创建一个新的随机会话")
    print("  /trace on|off     切换 LangGraph 节点事件流")
    print("  /tokens on|off    切换最终回答 token 流式输出")
    print("  exit              结束程序")


def export_graph(app):
    mermaid = app.get_graph().draw_mermaid()
    GRAPH_MERMAID_FILE.parent.mkdir(exist_ok=True)
    GRAPH_MERMAID_FILE.write_text(mermaid, encoding="utf-8")

    print(f"已导出 Mermaid 图：{GRAPH_MERMAID_FILE}")
    print("Mermaid：")
    print(mermaid)


def run_graph(
    app,
    state_input: dict,
    config: dict,
    trace_enabled: bool,
    token_stream_enabled: bool,
) -> dict:
    previous_stream_setting = os.environ.get(STREAM_TOKENS_ENV)
    os.environ[STREAM_TOKENS_ENV] = "1" if token_stream_enabled else "0"

    try:
        if trace_enabled:
            print("事件流：")

        for update in app.stream(state_input, config=config, stream_mode="updates"):
            if trace_enabled:
                print_graph_update(update)

        snapshot = app.get_state(config)
        return snapshot.values
    finally:
        if previous_stream_setting is None:
            os.environ.pop(STREAM_TOKENS_ENV, None)
        else:
            os.environ[STREAM_TOKENS_ENV] = previous_stream_setting


def print_graph_update(update: dict[str, Any]):
    for node_name, payload in update.items():
        if node_name == "agent_node":
            print_agent_update(payload)
        elif node_name == "tool_node":
            print_tool_update(payload)
        elif node_name == "save_memory":
            print("  save_memory -> 已保存本轮对话")
        else:
            print(f"  {node_name} -> {payload}")


def print_agent_update(payload: dict[str, Any]):
    if payload.get("route") == "tool":
        tool_names = [tool_call["name"] for tool_call in payload.get("tool_calls", [])]
        print(f"  agent_node -> 请求工具：{', '.join(tool_names)}")
        return

    answer = payload.get("answer", "")
    if payload.get("answer_streamed"):
        print("  agent_node -> 最终回答已流式输出")
        return

    preview = answer.replace("\n", " ")[:80]
    print(f"  agent_node -> 生成最终回答：{preview}")


def print_tool_update(payload: dict[str, Any]):
    tool_name = payload.get("tool_name", "unknown")
    print(f"  tool_node -> 已执行工具：{tool_name}")


def print_status():
    if os.getenv("DEEPSEEK_API_KEY"):
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        print(f"已检测到 DEEPSEEK_API_KEY，将使用 DeepSeek 模型：{model}")
    else:
        print("未检测到 DEEPSEEK_API_KEY，将使用本地回退回复。")


def print_state(app, config: dict):
    snapshot = app.get_state(config)
    values = snapshot.values or {}

    if not values:
        print("当前 thread 还没有 checkpoint。")
        return

    print("状态摘要：")
    print(f"  user_input: {values.get('user_input', '')}")
    print(f"  route: {values.get('route', '')}")
    print(f"  tool_name: {values.get('tool_name', '')}")
    print(f"  memory_turns: {len(values.get('memory', [])) // 2}")
    print(f"  messages: {len(values.get('messages', []))}")
    print(f"  answer_streamed: {values.get('answer_streamed', False)}")

    answer = values.get("answer", "")
    if answer:
        print(f"  answer_preview: {answer.replace(chr(10), ' ')[:100]}")


def print_memory(app, config: dict):
    snapshot = app.get_state(config)
    memory = (snapshot.values or {}).get("memory", [])

    if not memory:
        print("当前 thread 还没有对话记忆。")
        return

    print("对话记忆：")
    for index, item in enumerate(memory, start=1):
        print(f"  {index}. {item}")


def print_history(app, config: dict, command: str):
    limit = parse_history_limit(command)
    history = list(app.get_state_history(config, limit=limit))

    if not history:
        print("当前 thread 还没有 checkpoint 历史。")
        return

    print(f"最近 {len(history)} 条 checkpoint：")
    for index, snapshot in enumerate(history, start=1):
        values = snapshot.values or {}
        metadata = snapshot.metadata or {}
        step = metadata.get("step", "?")
        source = metadata.get("source", "?")
        next_nodes = ", ".join(snapshot.next) if snapshot.next else "END"
        answer = values.get("answer", "")
        preview = answer.replace("\n", " ")[:60] if answer else ""
        print(f"  {index}. step={step} source={source} next={next_nodes} answer={preview}")


def parse_history_limit(command: str) -> int:
    parts = command.split(maxsplit=1)
    if len(parts) == 1:
        return 5

    try:
        return max(1, min(20, int(parts[1])))
    except ValueError:
        return 5


def build_state_input(app, config: dict, user_input: str) -> dict:
    snapshot = app.get_state(config)
    has_memory = bool(snapshot.values and snapshot.values.get("memory"))

    state_input = {
        "user_input": user_input,
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

    if not has_memory:
        state_input["memory"] = []

    return state_input


if __name__ == "__main__":
    main()
