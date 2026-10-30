import asyncio
import json
import os

from aiokafka import AIOKafkaProducer
from topics import TASKS_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TEST_KEY = b"poison-order-test"


async def main():
    poison = {
        "correlation_id": "poison-demo-001",
        "question": "",
        "plan": [],
    }
    valid = {
        "correlation_id": "after-poison-001",
        "question": "What should happen after a poison message?",
        "plan": [
            "Retry the bad message",
            "Move it to dead letter",
            "Process later messages",
        ],
    }

    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        print(f"[POISON TEST] Sending poison message to {TASKS_TOPIC}")
        await producer.send_and_wait(
            TASKS_TOPIC, json.dumps(poison).encode(), key=TEST_KEY
        )
        print("[POISON TEST] Sending valid message after poison message")
        await producer.send_and_wait(
            TASKS_TOPIC, json.dumps(valid).encode(), key=TEST_KEY
        )
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
