from pathlib import Path
import sys
from typing import Dict, Any

from state import AgentState


source_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(source_dir))
# 
from agents_demo import parse_and_coerce
from model_client import complete

def planner_node(state: AgentState) -> Dict[str, Any]:
    print(" --- NODE: Planner --- ")
    # ... ( your existing planner logic) ...
    task = state["task"]
    messages = [
        {"role": "system", "content": "Propose exactly 3 distinct, topical tags (prefer multi-word phrases) and a one-line summary for the vulnerability."},
        {"role": "user", "content": (f"Task:\n{task}\n"
             "Return ONLY one JSON object (no code fences, no markdown, no explanations). "
             "Keys: thought (string), message (non-empty, <=60 words, no code), "
             "data.tags (array of exactly 3 topical tags), "
             "data.summary (<=25 words, no ellipses), data.issues (array).\n"
             "Do not add extra text outside JSON.")}, ]
    # complete is a function that interacts with the LLM to get a response based on the messages provided
    result = complete(messages)
    proposal = parse_and_coerce(result["content"], state["title"], state["content"], state.get("strict", False))
    return {"planner_proposal": proposal}

def reviewer_node(state: AgentState) -> Dict[str, Any]:
    print(" --- NODE: Reviewer --- ")
    # ... ( your existing reviewer logic) ...
    task = state["task"]

    # proposal is the output from the planner node, which should be passed to the reviewer node and {} if not present
    proposal = state.get("planner_proposal", {})
    messages = [
        {"role": "system", "content": "Validate: tags topical and not generic; summary ≤ 25 words; no code or markdown."},
        {"role": "user", "content": (f"Task:\n{task}\n\n"
            f"Review the Planner's proposal:\n{proposal}\n\n"
             "Return ONLY one JSON object (no code fences, no markdown, no explanations). "
             "Keys: thought (string), message (non-empty, <=60 words, no code), "
             "data.tags (array of exactly 3 topical tags), "
             "data.summary (<=25 words, no ellipses), data.issues (array).\n"
             "Do not add extra text outside JSON.")}, ]
    # complete is a function that interacts with the LLM to get a response based on the messages provided
    result = complete(messages)
    feedback = parse_and_coerce(result["content"], state["title"], state["content"], state.get("strict", False))
    return {"reviewer_feedback": feedback}

# Supervisor Node modifies the state like incrementing the turn count
def supervisor_node(state: AgentState) -> Dict[str, Any]:
    print(" --- NODE: Supervisor --- ")
    return {"turn_count": state.get("turn_count", 0) + 1}