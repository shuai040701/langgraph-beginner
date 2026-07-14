import os
import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from graph_app.graph import build_graph
from langgraph.checkpoint.memory import InMemorySaver


def main():
    if load_dotenv:
        load_dotenv()

    checkpointer = InMemorySaver()
    app = build_graph(checkpointer=checkpointer)
    thread_id = "demo-thread"
    config = {"configurable": {"thread_id": thread_id}}

    print("LangGraph Beginner v5 - Checkpoint Memory")
    if os.getenv("DEEPSEEK_API_KEY"):
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        print(f"输入 exit 结束。已检测到 DEEPSEEK_API_KEY，将使用 DeepSeek 模型：{model}")
    else:
        print("输入 exit 结束。未检测到 DEEPSEEK_API_KEY，将使用本地回退回复。")
    print("输入 /reset 可以开启一个新的 thread_id，清空当前会话记忆。")

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() in {"exit", "quit", "q"}:
            print("再见。")
            break

        if user_input == "/reset":
            thread_id = f"demo-thread-{uuid.uuid4().hex[:8]}"
            config = {"configurable": {"thread_id": thread_id}}
            print(f"已切换到新会话：{thread_id}")
            continue

        state_input = build_state_input(app, config, user_input)
        result = app.invoke(state_input, config=config)

        if result.get("tool_result"):
            print(f"工具 calculator：{result['tool_result']}")
        print(f"助手：{result['answer']}")


def build_state_input(app, config: dict, user_input: str) -> dict:
    snapshot = app.get_state(config)
    has_memory = bool(snapshot.values and snapshot.values.get("memory"))

    state_input = {
        "user_input": user_input,
        "route": "",
        "messages": [],
        "tool_name": "",
        "tool_args": {},
        "tool_call_id": "",
        "tool_result": "",
        "answer": "",
    }

    if not has_memory:
        state_input["memory"] = []

    return state_input


if __name__ == "__main__":
    main()
