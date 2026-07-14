from graph_app.llm import ask_final_answer, ask_with_tools
from graph_app.state import AppState
from graph_app.tools import safe_calculate


def agent_node(state: AppState) -> dict:
    return ask_with_tools(state["user_input"], state["memory"])


def calculator_node(state: AppState) -> dict:
    expression = str(state["tool_args"].get("expression", "")).strip()

    try:
        result = safe_calculate(expression)
        tool_result = str(result)
    except Exception as exc:
        tool_result = f"计算失败：{exc}"

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
