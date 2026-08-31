"""
defining a stable
interface such as complete(messages, tools=None). All model calls must go through this
adapter
"""
from ollama import chat
 
MODEL_NAME = "qwen2.5:3b"


def complete(messages, tools=None):
    response = chat(model=MODEL_NAME, messages=messages, think=False)

    # After every model response, print input tokens, output tokents, and total tokens for that turn

    # Ollama reports token counts on the response itself.
    input_tokens = response.get("prompt_eval_count", 0)
    output_tokens = response.get("eval_count", 0)
 
    return {"content": response.message.content, "input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": input_tokens + output_tokens}

