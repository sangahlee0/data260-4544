from typing import TypedDict, Dict, Any

# TypedDict for the state of the agent, allowing for optional keys
# total=False means that all keys are optional, so the state can be partially filled
class AgentState(TypedDict, total=False):
    title: str
    content: str
    email: str
    strict: bool
    task: str
    planner_proposal: Dict[str, Any]
    reviewer_feedback: Dict[str, Any]
    turn_count: int