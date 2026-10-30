# Demo for Part 1 IV
import json
import uuid

import requests

BASE_URL = "http://127.0.0.1:8044/vulnerabilities"
CORRELATION_ID = str(uuid.uuid4())


def show_response(label, response):
    print(f"\n[DEMO] {label}")
    print(f"[DEMO] HTTP status={response.status_code}")
    print(json.dumps(response.json(), indent=2))


print(f"<DEMO> correlation_id={CORRELATION_ID}")

create_payload = {
    "correlation_id": CORRELATION_ID,
    "operation": "CREATE_VULNERABILITY",
    "data": {
        "package_id": 1,
        "vulnerability_name": "Unsafe parser",
        "vulnerability_code": "CVE-DEMO-001",
        "urgency_score": 5,
    },
}

print("<DEMO> Sending CREATE_VULNERABILITY request")
create_response = requests.post(BASE_URL, json=create_payload, timeout=15)
show_response("CREATE_VULNERABILITY response", create_response)
create_result = create_response.json()

if not create_result.get("success"):
    raise RuntimeError("CREATE_VULNERABILITY failed")

entity_id = create_result["entity_id"]
print(f"[DEMO] Generated entity_id={entity_id}")

get_payload = {
    "correlation_id": CORRELATION_ID,
    "operation": "GET_VULNERABILITY",
    "data": {"entity_id": entity_id},
}

print("<DEMO> Sending GET_VULNERABILITY request")
get_response = requests.post(BASE_URL, json=get_payload, timeout=15)
show_response("GET_VULNERABILITY response", get_response)
get_result = get_response.json()

if get_result.get("correlation_id") == CORRELATION_ID:
    print("<DEMO> correlation_id preserved successfully")
else:
    raise RuntimeError("correlation_id was not preserved")

print("<DEMO> CREATE_VULNERABILITY -> GET_VULNERABILITY complete")
