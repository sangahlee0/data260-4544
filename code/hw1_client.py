"""
small command-line demo that imports the adapter
"""
import sys
import json

sys.path.insert(0, "src")

from model_client import complete

with open("AGENT.md") as f:
    system_prompt = f.read()
previous = [{"role": "system", "content": system_prompt}]

# On exit, print cumulative input tokens, output tokens, and turn count
turn_count = 0
cumulative_in = 0
cumulative_out = 0

while True:
    user_input = input("You: ").strip()

    if user_input == "/exit":
        break

    # Add /stats showing turn count, cumulative tokent counts, and serialized conversation-history length
    if user_input == "/stats":
        print(f"Turn count: {turn_count}")
        print(f"Cumulative input tokens: {cumulative_in}")
        print(f"Cumulative output tokens: {cumulative_out}")
        print(f"Serialized conversation-history length: {len(json.dumps(previous))}\n")
        continue

    previous.append({"role": "user", "content": user_input})

    result = complete(previous)

    previous.append({"role": "assistant", "content": result["content"]})
    turn_count += 1
    cumulative_in += result['input_tokens']
    cumulative_out += result['output_tokens']

    print(f"\nAssistant: {result['content']}\n")
    print(f"(turn {turn_count}; input tokens: {result['input_tokens']}, "
          f"output tokens: {result['output_tokens']}, "
          f"total: {result['total_tokens']})\n")

    print(f"Total turn count: {turn_count}\n")
    print(f"Cumulative input tokens: {cumulative_in}\n")
    print(f"Cumulative output tokens: {cumulative_out}\n")
    print(f"Cumulative total tokens: {cumulative_in + cumulative_out}\n")