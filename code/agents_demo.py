from ollama import chat
from pydantic import BaseModel

prompt = f"""Run a planner agent
        name="Planner",
        role="You are a planner agent whose goal is to draft three tags and a short summary.",
        goals=[
            "Create a plan for the computer to follow.",
            "The plan should be clear and concise.",
            "The plan should be achievable by the computer.",
            "The plan is to draft three tags, an example being e.g. ['vector clocks', 'partial ordering', 'conflict resolution']",
            "The plan is to write a one-sentence summary with a strict less than 25 word limit."
        ],
    )"""
 
# Step 1: Load the local model via Ollama

# Planner
def create_planner(title, content):
    response = chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": prompt}],
        format="json"
    )
    return response.message.content

# Step 5: Create the agent
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
# Reviewer

# Finalization step