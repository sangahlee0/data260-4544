# Replay duplicate with same id
import asyncio
import json
import os
import uuid

from aiokafka import AIOKafkaProducer
from topics import TASKS_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


async def main():
    correlation_id = f"duplicate-demo-{uuid.uuid4()}"
    message = {
        "correlation_id": correlation_id,
        "question": "How should a team prioritize a high-severity vulnerability?",
        "plan": [
            "Identify the main question",
            "Use the available vulnerability information",
            "Write a concise answer",
        ],
    }

    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        for attempt in (1, 2):
            print(
                f"[REPLAY] Sending attempt {attempt} with "
                f"correlation_id={correlation_id}"
            )
            await producer.send_and_wait(
                TASKS_TOPIC,
                json.dumps(message).encode(),
                key=correlation_id.encode(),
            )
            await asyncio.sleep(1)
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
