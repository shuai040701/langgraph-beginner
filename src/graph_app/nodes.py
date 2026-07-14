from graph_app.llm import ask_with_tools
from graph_app.state import AppState
from graph_app.tools import run_tool


def agent_node(state: AppState) -> dict:
    return ask_with_tools(
        state["user_input"],
        state["memory"],
        state.get("messages") or None,
    )


def tool_node(state: AppState) -> dict:
    tool_messages = []
    tool_results = []

    for tool_call in state.get("tool_calls", []):
        name = tool_call["name"]
        args = tool_call["args"]

        try:
            result = run_tool(name, args)
        except Exception as exc:
            result = f"工具执行失败：{exc}"

        tool_results.append(f"{name}: {result}")
        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result,
            }
        )

    messages = [*state["messages"], *tool_messages]
    tool_result = "\n".join(tool_results)
    tool_name = ", ".join(tool_call["name"] for tool_call in state.get("tool_calls", []))

    return {
        "messages": messages,
        "tool_result": tool_result,
        "tool_name": tool_name,
        "tool_calls": [],
    }


def save_memory(state: AppState) -> dict:
    memory = [
        *state["memory"],
        f"用户：{state['user_input']}",
        f"助手：{state['answer']}",
    ]
    return {"memory": memory}
