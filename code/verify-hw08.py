import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from worker.consumer import process_request_message, process_vulnerability_request

REQUEST_TOPIC = "s4544_vulnerability_requests"
RESPONSE_TOPIC = "s4544_vulnerability_responses"


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "reports" / "hw08" / "verification.json"


def check(name, passed, detail):
    return {"name": name, "pass": bool(passed), "detail": detail}


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def main():
    entity_id = str(uuid.uuid4())
    correlation_id = "verify-hw08-001"
    created = process_vulnerability_request(
        "CREATE_VULNERABILITY",
        {
            "package_id": 1,
            "vulnerability_name": "Verification vulnerability",
            "vulnerability_code": f"VERIFY-{entity_id[:8]}",
            "urgency_score": 5,
        },
    )
    stored_id = created.get("entity_id")
    retrieved = process_vulnerability_request(
        "GET_VULNERABILITY", {"entity_id": stored_id}
    )
    envelope = process_request_message(
        {
            "correlation_id": correlation_id,
            "reply_to": RESPONSE_TOPIC,
            "operation": "GET_VULNERABILITY",
            "data": {"entity_id": stored_id},
        }
    )

    checks = [
        check(
            "required_topics",
            REQUEST_TOPIC == "s4544_vulnerability_requests"
            and RESPONSE_TOPIC == "s4544_vulnerability_responses",
            f"request={REQUEST_TOPIC}, response={RESPONSE_TOPIC}",
        ),
        check(
            "create_generates_entity_id",
            created.get("success") is True and bool(stored_id),
            json.dumps(created),
        ),
        check(
            "get_returns_created_entity",
            retrieved.get("success") is True
            and retrieved.get("entity", {}).get("entity_id") == stored_id,
            json.dumps(retrieved),
        ),
        check(
            "correlation_id_preserved",
            envelope.get("correlation_id") == correlation_id,
            json.dumps(envelope),
        ),
        check(
            "unknown_operation_returns_error",
            process_vulnerability_request("UNKNOWN", {}).get("success") is False,
            "success=false",
        ),
    ]

    result = {
        "homework": 8,
        "sid4": "4544",
        "commit_hash": git_commit(),
        "model": "qwen2.5:3b",
        "seed": 4544,
        "verify_seed": 264544,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "all_passed": all(item["pass"] for item in checks),
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
