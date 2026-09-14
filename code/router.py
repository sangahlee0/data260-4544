from __future__ import annotations
from typing import Literal
from state import AgentState

#turn_ceiling = 10

def router_logic(state: AgentState) -> Literal["planner", "reviewer", "END"]:
    # Added for to compare turn ceilings of 2 and 10
    turn_ceiling = state.get("turn_ceiling", 10)  # Default to 10 if not specified in the state

    if state.get("turn_count", 0) >= turn_ceiling:
        return "END"
    
    if not state.get("planner_proposal"):
        return "planner"
    if not state.get("reviewer_feedback"):
        return "reviewer"

    # If the reviewer has provided feedback and there are issues, go back to the planner for another iteration for the loop. If there are no issues, we can end the process.
    if state["reviewer_feedback"].get("data", {}).get("issues", []):
        return "planner"
    return "END"
