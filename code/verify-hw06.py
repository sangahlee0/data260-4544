"""
verify-hw06.py

Basic self-check for HW6. Smoke tests
Writes results to reports/hw06/verification.json.

Usage:
    python3 code/verify-hw06.py
"""

import json
import subprocess
import sys
from pathlib import Path

import requests


SID4 = 4544
PORT_BASE = 8044
SEED = 4544
VERIFY_SEED = 264544
MODEL = "qwen2.5:3b"

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT_DIR / "reports" / "hw06" / "verification.json"

BASE_URL = f"http://localhost:{PORT_BASE}"


def get_commit_hash():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT_DIR,
        text=True,
    ).strip()


# Check the HW6 app on PORT_BASE
def check_backend():
    try:
        response = requests.get(
            f"{BASE_URL}/",
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


# POST /api/chat should return a reply
def check_chat():
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "user_id": "sangah",
                "session_id": "verify",
                "message": "/help",
            },
            timeout=15,
        )
        if response.status_code != 200:
            return False
        reply = response.json().get("reply")
        return isinstance(reply, str) and len(reply) > 0
    except (requests.RequestException, ValueError):
        return False


def main():
    checks = [
        {
            "check": "FastAPI backend responds on PORT_BASE 8044.",
            "passed": check_backend(),
        },
        {
            "check": "POST /api/chat returns a reply.",
            "passed": check_chat(),
        },
    ]

    verification = {
        "homework": 6,
        "sid4": SID4,
        "commit_hash": get_commit_hash(),
        "model": MODEL,
        "seed": SEED,
        "verify_seed": VERIFY_SEED,
        "checks": checks,
        "all_passed": all(check["passed"] for check in checks),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(verification, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(verification, indent=2))
    sys.exit(0 if verification["all_passed"] else 1)


if __name__ == "__main__":
    main()
