from __future__ import annotations

from langgraph.graph import StateGraph, END

from state import AgentState
from nodes import planner_node, reviewer_node, supervisor_node
from router import router_logic

def build_workflow():
    workflow = StateGraph(AgentState)

    # Add nodes to the workflow
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("reviewer", reviewer_node)

    workflow.set_entry_point("supervisor")

    # Add conditional edges based on the router logic
    workflow.add_conditional_edges("supervisor", router_logic, {
        "planner": "planner",
        "reviewer": "reviewer",
        "END": END
    })

    # Go back to the supervisor after each node to update state (like incrementing turn count)
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("reviewer", "supervisor")

    return workflow.compile()