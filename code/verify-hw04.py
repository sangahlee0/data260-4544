"""
verify-hw04.py

Basic self-check for HW4. Checks everything is reachable, and responds, and uploaded in reports/hw04/verification.json.

Usage:
    python3 code/verify-hw04.py
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

TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "password"

session = requests.Session()

RAG_CONFIG = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "top_k": 3,
    "relevance_threshold": 0.30,
}

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT_DIR / "reports" / "hw04" / "verification.json"

BASE_URL = f"http://localhost:{PORT_BASE}"

def login():
    try:
        response = session.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_commit_hash():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT_DIR,
        text=True,
    ).strip()


def check_response():
    try:
        response = session.get(
            f"{BASE_URL}/health",
            timeout=5,
        )

        return response.status_code == 200
    except requests.RequestException:
        return False


def check_naive_endpoint():
    try:
        response = session.get(
            f"{BASE_URL}/api/vulnerabilities?page_size=10",
            timeout=5,
        )

        if response.status_code != 200:
            return False

        data = response.json()

        return isinstance(data, list) and len(data) > 0

    except (requests.RequestException, ValueError):
        return False


def check_fixed_endpoint():
    try:
        response = session.get(
            f"{BASE_URL}/api/vulnerabilities-fixed?page_size=10",
            timeout=5,
        )

        if response.status_code != 200:
            return False

        data = response.json()

        return isinstance(data, list) and len(data) > 0

    except (requests.RequestException, ValueError):
        return False


def check_questions_file():
    questions_path = (ROOT_DIR/"reports"/"hw04"/"questions.yaml")

    return questions_path.is_file()


def check_rag_file():
    rag_path = (ROOT_DIR/"code"/"rag.py")

    return rag_path.is_file()


def main():
    login_confirm = login()

    checks = [
        {
            "check": "FastAPI backend responds on PORT_BASE 8044.",
            "passed": check_response(),
        },
        {
            "check": "Test user login succeeds.",
            "passed": login_confirm,
        },
        {
            "check": "Naive vulnerability endpoint returns data successfully.",
            "passed": login_confirm and check_naive_endpoint(),        
        },
        {
            "check": "Fixed vulnerability endpoint returns data successfully.",
            "passed": login_confirm and check_fixed_endpoint(),
        },
        {
            "check": "questions.yaml exists for HW04.",
            "passed": check_questions_file(),
        },
        {
        "check": "rag.py exists.",
        "passed": check_rag_file(),
        },
    ]

    verification = {
        "homework": 4,
        "sid4": SID4,
        "commit_hash": get_commit_hash(),
        "model": MODEL,
        "configuration": RAG_CONFIG,
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