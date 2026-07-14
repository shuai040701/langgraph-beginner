from typing import Literal

from langgraph.graph import END, START, StateGraph

from graph_app.nodes import agent_node, calculator_node, final_answer_node, save_memory
from graph_app.state import AppState


def route_after_agent(state: AppState) -> Literal["calculator_node", "save_memory"]:
    if state["route"] == "tool":
        return "calculator_node"

    return "save_memory"


def build_graph(checkpointer=None):
    builder = StateGraph(AppState)

    builder.add_node("agent_node", agent_node)
    builder.add_node("calculator_node", calculator_node)
    builder.add_node("final_answer_node", final_answer_node)
    builder.add_node("save_memory", save_memory)

    builder.add_edge(START, "agent_node")

    builder.add_conditional_edges(
        "agent_node",
        route_after_agent,
        {
            "calculator_node": "calculator_node",
            "save_memory": "save_memory",
        },
    )

    builder.add_edge("calculator_node", "final_answer_node")
    builder.add_edge("final_answer_node", "save_memory")
    builder.add_edge("save_memory", END)

    return builder.compile(checkpointer=checkpointer)
