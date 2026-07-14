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

        print("LangGraph Beginner v6 - SQLite Checkpoint Memory")
        print(f"记忆数据库：{CHECKPOINT_DB}")
        print_status()
        print("输入 /reset 开启新会话；输入 /thread 名称 切换或恢复指定会话；输入 exit 结束。")

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

            config = {"configurable": {"thread_id": thread_id}}
            state_input = build_state_input(app, config, user_input)
            result = app.invoke(state_input, config=config)

            if result.get("tool_result"):
                print(f"工具 calculator：{result['tool_result']}")
            print(f"助手：{result['answer']}")


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
