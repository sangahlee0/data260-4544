import json
from pathlib import Path
import os

from mcp_server.domain_server import execute_tool
from langchain_ollama import ChatOllama

MODEL_NAME = os.environ.get("SMOL_MODEL", "your-ollama-model-tag")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

MAX_STEPS_LIMIT = 4

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_LOG_PATH = REPO_ROOT / "reports" / "hw05" / "raw" / "agent_runs.jsonl"

def get_model():
    return ChatOllama(
        model=MODEL_NAME,
        temperature=0.0,
        base_url=OLLAMA_URL,
        num_ctx=2048,
    )


def run_agent(user_input):
    model = get_model()

    messages = [
        {
            "role": "system",
            "content": """
            You help users find vulnerability information.

            You have three tools:
            - search_vulnerabilities_by_name(query, limit=5), which we use to find vulnerabilities by vulnerability name.
            - search_vulnerabilities_by_id(vulnerability_id), which we use when the user provides a vulnerability ID.
            - count_by_package(package_name), which we use when the user asks how many vulnerabilities belong to a package.

            To call a tool, return only:
            {"action":"tool","tool":"tool_name","inputs":{}}

            When all the information is available, return only:
            {"action":"final","answer":"your answer"}
            - The "action" must be exactly "tool"
            - tool should be one of the three tool names stated above
            - "inputs" must contain the tool's inputs.

            REMEMBER that EVERY response must be valid JSON.
            Never respond with plain English outside of the JSON object, and use double quotes for all JSON keys and string values
            "action" must also be exactly "tool" or "final".
            With a successful result, normally return a final answer instead of calling another tool, and do not invent a tool call or question if the tool result already answers the question successfully.
            """,
        },
        {"role": "user", "content": user_input},
    ]

    step = 0
    tool_call_count = 0
    while step < MAX_STEPS_LIMIT:
        step += 1
        response = model.invoke(messages)
        content = getattr(response, "content", "")
        print("MODEL RESPONSE:", content)

        try:
            action = json.loads(content)
        except (TypeError, json.JSONDecodeError):
            log_agent_step({
                "step": step,
                "stop_reason": "invalid_json",
                "tool_call_count" : tool_call_count
            })
            return {
                "answer": "Invalid response.",
                "step_count": step,
                "stop_reason": "invalid_json",
                "tool_call_count": tool_call_count
            }

        if not isinstance(action, dict):
            log_agent_step({
                "step": step,
                "stop_reason": "invalid_json",
                "tool_call_count": tool_call_count
            })
            return {
                "answer": "Invalid response.",
                "step_count": step,
                "stop_reason": "invalid_json",
                "tool_call_count" : tool_call_count
            }
        # Normalize cases where the model puts the tool name in "action" because model is finding it difficult
        tool_names = [
            "search_vulnerabilities_by_name",
            "search_vulnerabilities_by_id",
            "count_by_package"
        ]

        if action.get("action") in tool_names:
            action["tool"] = action.get("action")
            action["action"] = "tool"

        if action.get("action") == "tool":
            tool_name = action.get("tool")
            tool_inputs = action.get("inputs", {}) or {}

            if not tool_name:
                log_agent_step({
                    "step": step,
                    "stop_reason": "invalid_tool",
                    "tool_call_count": tool_call_count
                })
                return {
                    "answer": "Invalid tool request.",
                    "step_count": step,
                    "stop_reason": "invalid_tool",
                    "tool_call_count" : tool_call_count
                }

            tool_result = execute_tool(tool_name, tool_inputs)
            tool_call_count += 1
            print("TOOL RESULT TEST:", tool_result) #### TEST
            log_agent_step({
                "step": step,
                "tool": tool_name,
                "inputs": tool_inputs,
                "result": tool_result
            })

            messages.append({
                "role": "assistant",
                "content": content
            })

            messages.append({
                "role": "user",
                "content": f"Tool result: {tool_result}"
            })

            continue

        if action.get("action") == "final":
            answer = action.get("answer", "")

            log_agent_step({
                "step": step,
                "stop_reason": "completed",
                "answer": answer,
                "tool_call_count": tool_call_count
            })
            return {
                "answer": action.get("answer", ""),
                "step_count": step,
                "stop_reason": "completed",
                "tool_call_count" : tool_call_count
            }
        log_agent_step({
            "step": step,
            "stop_reason": "invalid_action",
            "tool_call_count": tool_call_count
        })

        return {
            "answer": "Invalid response.",
            "step_count": step,
            "stop_reason": "invalid_action",
            "tool_call_count" : tool_call_count
        }

    log_agent_step({
        "step": step,
        "stop_reason": "max_steps",
        "tool_call_count" : tool_call_count
    })

    return {
        "answer": "Maximum number of steps reached.",
        "step_count": step,
        "stop_reason": "max_steps",
        "tool_call_count" : tool_call_count
    }

# Helper for the agent_runs.jsonl
def log_agent_step(log_data):
    AGENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(AGENT_LOG_PATH, "a") as file:
        file.write(json.dumps(log_data) + "\n")


if __name__ == "__main__":
    user_input = input("Enter a vulnerability question: ")
    result = run_agent(user_input)
    print(json.dumps(result, indent=2))