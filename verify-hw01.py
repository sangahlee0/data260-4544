"""
verify_hw01.py

Basic self-check for HW1. Confirms the pipeline runs and writes results to reports/hw01/verification.json.

Usage:
    python3 verify_hw01.py
"""

import json
import os
import sys
from datetime import datetime, timezone
import agent_demo

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

WEB_APP_DIR = "code/web_application"
NONDETERMINISM_INPUT = "reports/hw01/cases/nondeterminism_input.json"
OUTPUT_PATH = "reports/hw01/verification.json"

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

    sys.path.insert(0, WEB_APP_DIR)

    result = agent_demo.finalize(data["title"], data["content"], temperature=0.0)
    tags = result.get("tags", [])
    summary = result.get("summary", "")

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