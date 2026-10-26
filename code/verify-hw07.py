"""
HW7 smoke-test / verification script.

Runs the app in a subprocess, exercises key JWT auth and RBAC behaviors,
writes reports/hw07/verification.json, then shuts down.

Run from the data260-4544/ root:
    python code/verify-hw07.py
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8044"
REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "reports" / "hw07"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# Helpers
def get_token(username: str, password: str) -> str:
    r = httpx.post(
        f"{BASE_URL}/auth/login", data={"username": username, "password": password}
    )
    return r.json().get("access_token", "")


def run_check(name: str, fn) -> dict:
    try:
        passed, detail = fn()
        return {"name": name, "pass": passed, "detail": detail}
    except Exception as exc:
        return {"name": name, "pass": False, "detail": str(exc)}


# Individual checks
def check_login_valid():
    r = httpx.post(
        f"{BASE_URL}/auth/login", data={"username": "alice", "password": "alice123"}
    )
    ok = r.status_code == 200 and "access_token" in r.json()
    return ok, f"status={r.status_code}"


def check_login_invalid():
    r = httpx.post(
        f"{BASE_URL}/auth/login", data={"username": "alice", "password": "WRONG"}
    )
    return r.status_code == 401, f"status={r.status_code}"


def check_no_token_401():
    r = httpx.get(f"{BASE_URL}/api/vulnerabilities")
    return r.status_code == 401, f"status={r.status_code}"


def check_auth_me():
    token = get_token("alice", "alice123")
    r = httpx.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = r.json()
    ok = r.status_code == 200 and body.get("role") == "reader"
    return ok, f"status={r.status_code} role={body.get('role')}"


def check_reader_can_list():
    token = get_token("alice", "alice123")
    r = httpx.get(
        f"{BASE_URL}/api/vulnerabilities", headers={"Authorization": f"Bearer {token}"}
    )
    return r.status_code == 200, f"status={r.status_code}"


def check_reader_cannot_create():
    token = get_token("alice", "alice123")
    r = httpx.post(
        f"{BASE_URL}/api/vulnerabilities",
        json={
            "vulnerability_name": "test",
            "vulnerability_code": "T-VERIFY-999",
            "urgency_score": 1,
            "package_id": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return r.status_code == 403, f"status={r.status_code}"


def check_writer_can_create():
    token = get_token("bob", "bob123")
    r = httpx.post(
        f"{BASE_URL}/api/vulnerabilities",
        json={
            "vulnerability_name": "verify-test",
            "vulnerability_code": "T-VERIFY-998",
            "urgency_score": 2,
            "package_id": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return r.status_code == 201, f"status={r.status_code}"


def check_writer_cannot_delete():
    token = get_token("bob", "bob123")
    r = httpx.delete(
        f"{BASE_URL}/api/vulnerabilities/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    return r.status_code == 403, f"status={r.status_code}"


def check_agent_loop_verification():
    from hw7_agent import run_agent

    res = run_agent(
        "Search for 'Injection' vulnerabilities, then lookup the details of the first vulnerability found.",
        use_live_model=False,
        verbose=False,
    )
    ok = res.get("status") == "success" and res.get("tool_calls", 0) >= 2
    return ok, f"status={res.get('status')} tool_calls={res.get('tool_calls')}"


# Main

commit = (
    subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
    .decode()
    .strip()
)

checks = [
    run_check("login_valid_creds_200", check_login_valid),
    run_check("login_invalid_creds_401", check_login_invalid),
    run_check("no_token_returns_401", check_no_token_401),
    run_check("auth_me_returns_role", check_auth_me),
    run_check("reader_can_list_200", check_reader_can_list),
    run_check("reader_cannot_create_403", check_reader_cannot_create),
    run_check("writer_can_create_201", check_writer_can_create),
    run_check("writer_cannot_delete_403", check_writer_cannot_delete),
    run_check("agent_loop_verification_task", check_agent_loop_verification),
]

output = {
    "homework": 7,
    "sid4": "4544",
    "commit_hash": commit,
    "model": "qwen2.5:3b",
    "seed": 4544,
    "verify_seed": 264544,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
}

out_path = REPORT_DIR / "verification.json"
out_path.write_text(json.dumps(output, indent=2))
print(json.dumps(output, indent=2))

all_passed = all(c["pass"] for c in checks)
sys.exit(0 if all_passed else 1)
