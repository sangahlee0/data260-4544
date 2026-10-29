import asyncio
import json
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
REQUEST_TOPIC = "s4544_vulnerability_requests"


vulnerabilities = {}


def validate_vulnerability(data):
    # Return a readable validation error, or None when data is valid
    if not isinstance(data, dict):
        return "data must be an object"

    if not isinstance(data.get("package_id"), int) or data["package_id"] <= 0:
        return "package_id must be a positive integer"

    for field in ("vulnerability_name", "vulnerability_code"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            return f"{field} is required"

    urgency_score = data.get("urgency_score")
    if not isinstance(urgency_score, int) or urgency_score < 1:
        return "urgency_score must be a positive integer"

    return None


def process_vulnerability_request(operation, data):
    # Process CREATE_VULNERABILITY or GET_VULNERABILITY
    if operation == "CREATE_VULNERABILITY":
        error = validate_vulnerability(data)
        if error:
            return {"success": False, "error": error}

        entity_id = str(uuid.uuid4())
        entity = {
            "entity_id": entity_id,
            "package_id": data["package_id"],
            "vulnerability_name": data["vulnerability_name"].strip(),
            "vulnerability_code": data["vulnerability_code"].strip(),
            "urgency_score": data["urgency_score"],
        }
        vulnerabilities[entity_id] = entity

        return {
            "success": True,
            "entity_id": entity_id,
            "message": "Entity created",
        }

    if operation == "GET_VULNERABILITY":
        if not isinstance(data, dict) or not data.get("entity_id"):
            return {"success": False, "error": "entity_id is required"}

        entity = vulnerabilities.get(data["entity_id"])
        if entity is None:
            return {"success": False, "error": "Entity not found"}

        return {"success": True, "entity": entity}

    return {"success": False, "error": "Unknown operation"}


def process_request_message(request):
    """Validate the Kafka envelope and return a response with its correlation ID."""
    correlation_id = request.get("correlation_id")

    if not correlation_id:
        return {
            "correlation_id": correlation_id,
            "success": False,
            "error": "correlation_id is required",
        }

    if not request.get("reply_to"):
        return {
            "correlation_id": correlation_id,
            "success": False,
            "error": "reply_to is required",
        }

    if not request.get("operation"):
        return {
            "correlation_id": correlation_id,
            "success": False,
            "error": "operation is required",
        }

    result = process_vulnerability_request(request["operation"], request.get("data"))
    return {"correlation_id": correlation_id, **result}


async def main():
    consumer = AIOKafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="s4544-vulnerability-worker-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()
    print("The consumer is ready and listening...")
    print(f"Listening for requests on topic: {REQUEST_TOPIC}")

    try:
        async for message in consumer:
            try:
                request = json.loads(message.value.decode())
            except json.JSONDecodeError:
                print("[WORKER] Invalid JSON message; skipping message")
                continue

            correlation_id = request.get("correlation_id")
            reply_to = request.get("reply_to")

            print("[WORKER] Received request from Kafka")
            print(f"[WORKER] correlation_id={correlation_id}")
            print(f"[WORKER] request={json.dumps(request, indent=2)}")

            response = process_request_message(request)

            print("[WORKER] Sending response to Kafka")
            print(f"[WORKER] response={json.dumps(response, indent=2)}")
            if reply_to:
                await producer.send_and_wait(reply_to, json.dumps(response).encode())
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
