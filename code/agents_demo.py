import asyncio
import logging
import os
import signal
import traceback

from agent import ComputerAgent
from computer import Computer
from dotenv import load_dotenv

from langchain_ollama import OllamaLLM
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain import hub
 
# Step 1: Load the local model via Ollama
llm = OllamaLLM(model="(qwen3:8b)")

# Planner
def create_planner():
    """Create a planner agent"""
    return ComputerAgent(
        name="Planner",
        role="You are a planner agent whose goal is to draft three tags and a short summary",
        goals=[
            "Create a plan for the computer to follow.",
            "The plan should be clear and concise.",
            "The plan should be achievable by the computer.",
        ],
    )
# Step 5: Create the agent
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
# Reviewer

# Finalization step