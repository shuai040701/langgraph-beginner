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

        print("LangGraph Beginner v10 - Token Streaming")
        print(f"记忆数据库：{CHECKPOINT_DB}")
        print_status()
        print("输入 /reset 开启新会话；输入 /thread 名称 切换或恢复指定会话。")
        print("输入 /trace on|off 切换事件流；输入 /tokens on|off 切换回答流式输出；输入 exit 结束。")

        while True:
            user_input = input(f"\n你[{thread_id}]：").strip()

            if user_input.lower() in {"exit", "quit", "q"}:
                print("再见。")
                break

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

            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 12,
            }
            state_input = build_state_input(app, config, user_input)
            result = run_graph(app, state_input, config, trace_enabled, token_stream_enabled)

            if result.get("tool_result"):
                print(f"工具结果：\n{result['tool_result']}")
            if not result.get("answer_streamed"):
                print(f"助手：{result['answer']}")


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
