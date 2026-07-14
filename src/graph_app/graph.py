from typing import Literal

from langgraph.graph import END, START, StateGraph

from graph_app.nodes import agent_node, save_memory, tool_node
from graph_app.state import AppState


def route_after_agent(state: AppState) -> Literal["tool_node", "save_memory"]:
    if state["route"] == "tool":
        return "tool_node"

    return "save_memory"


def build_graph(checkpointer=None):
    builder = StateGraph(AppState)

    builder.add_node("agent_node", agent_node)
    builder.add_node("tool_node", tool_node)
    builder.add_node("save_memory", save_memory)

    builder.add_edge(START, "agent_node")

    builder.add_conditional_edges(
        "agent_node",
        route_after_agent,
        {
            "tool_node": "tool_node",
            "save_memory": "save_memory",
        },
    )

    builder.add_edge("tool_node", "agent_node")
    builder.add_edge("save_memory", END)

    return builder.compile(checkpointer=checkpointer)
