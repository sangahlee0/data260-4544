import asyncio
import json
import os

from aiokafka import AIOKafkaProducer
from topics import TASKS_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


async def main():
    message = {
        "correlation_id": "consumer-death-demo-001",
        "question": "What should happen when a writer stops during processing?",
        "plan": [
            "Detect the failed consumer",
            "Redeliver the uncommitted message",
            "Commit after successful processing",
        ],
    }

    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        print(f"[DEATH TEST] Sending to {TASKS_TOPIC}")
        print(json.dumps(message, indent=2))
        await producer.send_and_wait(
            TASKS_TOPIC,
            json.dumps(message).encode(),
            key=message["correlation_id"].encode(),
        )
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
