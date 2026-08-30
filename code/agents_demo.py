from ollama import chat
from pydantic import BaseModel

prompt = f"""Run a planner agent
        name="Planner",
        role="You are a planner agent whose goal is to draft three tags and a short summary.",
        goals=[
            "The plan is to take in title and content as input.",
            "The plan is to draft three tags, an example being e.g. ['vector clocks', 'partial ordering', 'conflict resolution']",
            "The plan is to write a one-sentence summary with a strict less than 25 word limit.",
            "Return only valid JSON."
        ],
    )"""
 
# Step 1: Load the local model via Ollama

# Planner
def create_planner(title, content):
    response = chat(
        model="qwen3:8b",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": f"""Title: {title}, Content: {content}"""}],
        format="json"
    )
    return response.message.content


# Reviewer

# Finalization step