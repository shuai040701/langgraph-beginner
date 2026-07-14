import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from graph_app.graph import build_graph


def main():
    if load_dotenv:
        load_dotenv()

    app = build_graph()
    memory: list[str] = []

    print("LangGraph Beginner v4 - DeepSeek ReAct")
    if os.getenv("DEEPSEEK_API_KEY"):
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        print(f"输入 exit 结束。已检测到 DEEPSEEK_API_KEY，将使用 DeepSeek 模型：{model}")
    else:
        print("输入 exit 结束。未检测到 DEEPSEEK_API_KEY，将使用本地回退回复。")

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() in {"exit", "quit", "q"}:
            print("再见。")
            break

        result = app.invoke(
            {
                "user_input": user_input,
                "route": "",
                "memory": memory,
                "messages": [],
                "tool_name": "",
                "tool_args": {},
                "tool_call_id": "",
                "tool_result": "",
                "answer": "",
            }
        )

        memory = result["memory"]
        if result.get("tool_result"):
            print(f"工具 calculator：{result['tool_result']}")
        print(f"助手：{result['answer']}")


if __name__ == "__main__":
    main()
