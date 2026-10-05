"""
verify-hw05.py

Basic self-check for HW5. Smoke tests
Writes results to reports/hw05/verification.json.

Usage:
    python3 code/verify-hw05.py
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import requests

from mcp_server.domain_server import execute_tool


SID4 = 4544
PORT_BASE = 8044
SEED = 4544
VERIFY_SEED = 264544
MODEL = "qwen2.5:3b"

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT_DIR / "reports" / "hw05" / "verification.json"

BASE_URL = f"http://localhost:{PORT_BASE}"


def get_commit_hash():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT_DIR,
        text=True,
    ).strip()


# Check FastAPI backend on PORT_BASE
def check_backend():
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            timeout=5,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


# Check domain MCP tool and see if it responds
def check_domain_tool():
    try:
        result = execute_tool(
            "search_vulnerabilities_by_name",
            {
                "query": "Injection",
                "limit": 5,
            },
        )

        data = json.loads(result)

        return (
            isinstance(data, dict)
            and "ok" in data
            and "data" in data
            and "error" in data
        )

    except Exception:
        return False

# Check offline test suite
def check_offline_tests():
    try:
        result = subprocess.run(
            [sys.executable, "test_execute_tool.py"],
            cwd=ROOT_DIR / "code",
            capture_output=True,
            text=True,
            timeout=30,
        )

        return (
            result.returncode == 0
            and "8/8 tests passed" in result.stdout
        )

    except (subprocess.SubprocessError, OSError):
        return False


# Check that Q20 produced all 150 calls
def check_retry_results():
    path = ROOT_DIR / "reports" / "hw05" / "raw" / "retry_results.csv"

    if not path.is_file():
        return False

    try:
        with open(path, newline="") as file:
            rows = list(csv.DictReader(file))

        return len(rows) == 150

    except (OSError, csv.Error):
        return False


# Check that agent_runs.jsonl contains valid JSON
def check_agent_log():
    path = ROOT_DIR / "reports" / "hw05" / "raw" / "agent_runs.jsonl"

    if not path.is_file():
        return False

    try:
        lines = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        if not lines:
            return False

        for line in lines:
            json.loads(line)

        return True

    except (OSError, json.JSONDecodeError):
        return False


def main():
    checks = [
        {
            "check": "FastAPI backend responds on PORT_BASE 8044.",
            "passed": check_backend(),
        },
        {
            "check": "Domain MCP tool responds successfully.",
            "passed": check_domain_tool(),
        },
        {
            "check": "Offline test suite passes 8/8.",
            "passed": check_offline_tests(),
        },
        {
            "check": "Fault-injection CSV contains 150 calls.",
            "passed": check_retry_results(),
        },
        {
            "check": "Agent log contains valid JSONL records.",
            "passed": check_agent_log(),
        },
    ]

    verification = {
        "homework": 5,
        "sid4": SID4,
        "commit_hash": get_commit_hash(),
        "model": MODEL,
        "seed": SEED,
        "verify_seed": VERIFY_SEED,
        "port_base": PORT_BASE,
        "checks": checks,
        "all_passed": all(
            check["passed"] for check in checks
        ),
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(verification, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(verification, indent=2))

    sys.exit(0 if verification["all_passed"] else 1)


if __name__ == "__main__":
    main()