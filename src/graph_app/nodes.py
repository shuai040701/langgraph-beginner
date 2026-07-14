from graph_app.llm import ask_final_answer, ask_with_tools
from graph_app.state import AppState
from graph_app.tools import run_tool


def agent_node(state: AppState) -> dict:
    return ask_with_tools(state["user_input"], state["memory"])


def tool_node(state: AppState) -> dict:
    try:
        tool_result = run_tool(state["tool_name"], state["tool_args"])
    except Exception as exc:
        tool_result = f"工具执行失败：{exc}"

    messages = [
        *state["messages"],
        {
            "role": "tool",
            "tool_call_id": state["tool_call_id"],
            "content": tool_result,
        },
    ]

    return {"messages": messages, "tool_result": tool_result}


def final_answer_node(state: AppState) -> dict:
    answer = ask_final_answer(state["messages"])
    return {"answer": answer}


def save_memory(state: AppState) -> dict:
    memory = [
        *state["memory"],
        f"用户：{state['user_input']}",
        f"助手：{state['answer']}",
    ]
    return {"memory": memory}
