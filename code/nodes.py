from pathlib import Path
import sys
from typing import Dict, Any

from state import AgentState

# For feeding validation back to planner and retry within turn ceiling
from pydantic import ValidationError
from validateplanner import PlannerOutput


source_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(source_dir))
# 
from agents_demo import parse_and_coerce
from model_client import complete

def planner_node(state: AgentState) -> Dict[str, Any]:
    print(" --- NODE: Planner --- ")
    # ... ( your existing planner logic) ...

    # Read the validation error from the state if it exists, otherwise set it to an empty string
    validation_error = state.get("validation_error", "")
    task = state["task"]

    retry_message = ""
    if validation_error:
        retry_message = (f"\nPrevious validation error: {validation_error}. \n Fix the error and retry.")

    messages = [
        {"role": "system", "content": "Propose exactly 3 distinct, topical tags (prefer multi-word phrases) and a one-line summary for the vulnerability."},
        {"role": "user", "content": (f"Task:\n{task}\n"
            f"Retry message:\n{retry_message}\n"
            "Return ONLY one JSON object (no code fences, no markdown, no explanations). "
            "Keys: thought (string), message (non-empty, <=60 words, no code), "
            "data.tags (array of exactly 3 topical tags), "
            "data.summary (<=25 words, no ellipses), data.issues (array).\n"
            "Do not add extra text outside JSON.")}, ]
    # complete is a function that interacts with the LLM to get a response based on the messages provided
    result = complete(messages)
    # proposal is the output from the planner node, which should be passed to the reviewer node and {} if not present
    proposal = parse_and_coerce(result["content"], state["title"], state["content"], state.get("strict", False))

    try:
        # Validate the proposal using the PlannerOutput model
        PlannerOutput(**proposal["data"])  # This will raise a ValidationError if the proposal is invalid

    except ValidationError as e:
        # If validation fails, store the error message in the state for the next iteration
        return {"planner_proposal": {}, "reviewer_feedback": {}, "validation_error": str(e)} # empty planner_proposal to indicate failure, reviewer_feedback empty to clear out any previous feedback when the planner is called again
    # reviewer_feedback empty to clear out any previous feedback when the planner is called again
    return {"planner_proposal": proposal, "reviewer_feedback": {}, "validation_error": ""}  # Clear validation error if proposal is valid

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


    ##### Extra for Step 6: Running and Testing; temporary modification to always return an issue for testing purposes. Remove this line in production.
    #feedback["data"]["issues"] = ["Forced test for testing purposes."]
    return {"reviewer_feedback": feedback}

# Supervisor Node modifies the state like incrementing the turn count
def supervisor_node(state: AgentState) -> Dict[str, Any]:
    print(" --- NODE: Supervisor --- ")
    return {"turn_count": state.get("turn_count", 0) + 1}