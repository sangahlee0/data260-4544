"""
verify-hw01.py

Basic self-check for HW1. Confirms the pipeline runs and writes results to reports/hw01/verification.json.

Usage:
    python3 verify-hw01.py
"""

import json
import os
import sys

# Make sure the modules can be found inside the code/ directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.abspath(os.path.join(ROOT_DIR, "src")))

from datetime import datetime, timezone
import agents_demo
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

WEB_APP_DIR = os.path.join(ROOT_DIR, "code/web_application")
NONDETERMINISM_INPUT = os.path.join(ROOT_DIR, "reports/hw01/cases/nondeterminism_input.json")
OUTPUT_PATH = os.path.join(ROOT_DIR, "reports/hw01/verification.json")

results = {}

# ------------------------
# Fixed input file exists
# ------------------------

results["nondeterminism_input_exists"] = os.path.isfile(NONDETERMINISM_INPUT)

# ----------------------------------------------
# Pipeline runs and returns valid tags/summary
# ----------------------------------------------

try:
    with open(NONDETERMINISM_INPUT) as f:
        data = json.load(f)

    # Initialize the model and agents directly using agents_demo classes
    llm = ChatOllama(
        model=os.environ.get("SMOL_MODEL", "qwen2.5:3b"),
        temperature=0.0,
        base_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        num_ctx=2048
    )

    planner = agents_demo.SimpleAgent(
        name="Planner",
        system="Propose exactly 3 distinct, topical tags (prefer multi-word phrases) and a one-line summary for the vulnerability.",
        model=llm
    )
    reviewer = agents_demo.SimpleAgent(
        name="Reviewer",
        system="Validate: tags topical and not generic; summary ≤ 25 words; no code or markdown. ",
        model=llm
    )
    finalizer = agents_demo.SimpleAgent(
        name="Finalizer",
        system="Use reviewer feedback to finalize. Output exactly 3 tags in data.tags and the final summary in data.summary.",
        model=llm
    )

    task = f'With vulnerability name "{data["title"]}" and description "{data["content"]}", produce exactly 3 topical tags and a one-sentence summary.'
    
    # Run the pipeline function from agents_demo
    final, _ = agents_demo.run_pipeline(
        planner, reviewer, finalizer, task, data["title"], data["content"], strict=False
    )
    

    sys.path.insert(0, WEB_APP_DIR)

    r_data = final.get("data", {})
    tags = r_data.get("tags", [])
    summary = r_data.get("summary", "")

    results["pipeline_returns_valid_output"] = (
        len(tags) == 3 and len(summary.split()) <= 25
    )
except Exception as e:
    print(f"Pipeline check failed: {e}", file=sys.stderr)
    results["pipeline_returns_valid_output"] = False


### RESULTS ###

for name, passed in results.items():
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")

### Write to verification.json

output = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": results,
    "all_passed": all(results.values()),
}

os.makedirs("reports/hw01", exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nWrote results to {OUTPUT_PATH}")
print(f"All checks passed: {output['all_passed']}")

sys.exit(0 if output["all_passed"] else 1)