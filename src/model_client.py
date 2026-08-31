"""
defining a stable
interface such as complete(messages, tools=None). All model calls must go through this
adapter
"""
from ollama import chat
 
MODEL_NAME = "qwen3:8b"


def complete(messages, tools=None):
    return chat(model=MODEL_NAME, messages=messages, think=False)
