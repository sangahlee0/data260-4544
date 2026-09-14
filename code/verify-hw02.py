"""
verify-hw02.py

Basic self-check for HW2. Confirms the pipeline runs and writes results to reports/hw02/verification.json.

Usage:
    python3 verify-hw02.py
"""

import json
import os
import sys
import subprocess   # subprocess used to run external commands from python code
import urllib.request

from workflow import build_workflow


SID4 = 4544
PORT_BASE = 8044
SEED = 4544
VERIFY_SEED = 264544
MODEL = "qwen2.5:3b"


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SCHEMA_INPUT = os.path.join(
    ROOT_DIR,
    "reports/hw02/cases/schema_input.json"
)

OUTPUT_PATH = os.path.join(
    ROOT_DIR,
    "reports/hw02/verification.json"
)


# get the commit hash
def get_commit_hash():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True
    ).strip()

# ----------------------------------------------
# Langgraph runs and returns valid output
# ----------------------------------------------
def check_langgraph():
    try:
        with open(SCHEMA_INPUT, "r") as f:
            schema_load = json.load(f)
        graph = build_workflow()

        initial_state = {
            "title": schema_load["vulnerability_name"],
            "content": schema_load["issue_description"],
            "email": schema_load["reporter_email"],
            "strict": False,
            "task": (
                f"Generate exactly 3 topical tags and a summary for this vulnerability. "
                f"Package: {schema_load['package_name']}. "
                f"Vulnerability: {schema_load['vulnerability_name']}. "
                f"Severity: {schema_load['severity']}."
            ),
            "planner_proposal": {},
            "reviewer_feedback": {},
            "validation_error": "",
            "turn_count": 0,
            "turn_ceiling": 10,
        }

        final_state = graph.invoke(initial_state)

        proposal = final_state.get("planner_proposal", {})
        data = proposal.get("data", {})

        tags = data.get("tags", [])
        summary = data.get("summary", "")

        return {
            "graph_finished": True,
            "exactly_3_tags": len(tags) == 3,
            "summary_25_words_or_less": len(summary.split()) <= 25,
        }

    except Exception as e:
        print(f"LangGraph check failed: {e}", file=sys.stderr)
        return {"graph_finished": False,
            "exactly_3_tags": False,
            "summary_25_words_or_less": False,
        }
# ----------------------------------------------
# FastAPI backend responds on PORT_BASE
# ----------------------------------------------
def check_fastapi():
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{PORT_BASE}/",
            timeout=7
        ) as response:
            return response.status == 200

    except Exception as e:
        print(f"FastAPI check failed: {e}", file=sys.stderr)
        return False

def main():
    graph_checks = check_langgraph()

    checks = [
        {
            "check": "LangGraph finishes",
            "passed": graph_checks["graph_finished"],
        },
        {
            "check": "Planner returns exactly 3 tags",
            "passed": graph_checks["exactly_3_tags"],
        },
        {
            "check": "Summary contains at less than or equal to 25 words",
            "passed": graph_checks["summary_25_words_or_less"],
        },
        {
            "check": "The FastAPI backend responds on PORT_BASE",
            "passed": check_fastapi(),
        },
    ]

    verification = {
        "homework": 2,
        "sid4": SID4,
        "commit_hash": get_commit_hash(),
        "model": MODEL,
        "port_base": PORT_BASE,
        "seed": SEED,
        "verify_seed": VERIFY_SEED,
        "checks": checks,
        "all_passed": all(check["passed"] for check in checks),
    }
    
    with open(OUTPUT_PATH, "w") as f:
        json.dump(verification, f, indent=2)

    print(json.dumps(verification, indent=2))

    # Return success if all verification checks passed
    sys.exit(0 if verification["all_passed"] else 1)


if __name__ == "__main__":
    main()