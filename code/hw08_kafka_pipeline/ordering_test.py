import asyncio
import json
import os
import uuid

from aiokafka import AIOKafkaProducer
from topics import TASKS_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KEYED = os.getenv("ORDERING_KEYED") == "1"
ENTITY_ID = "related-entity-4544"


async def main():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()
    mode = "keyed" if KEYED else "unkeyed"
    print(f"[ORDERING] Starting {mode} run with 20 messages")

    try:
        for sequence in range(1, 21):
            message = {
                "correlation_id": f"ordering-{mode}-{uuid.uuid4()}",
                "entity_id": ENTITY_ID,
                "sequence": sequence,
                "question": f"Ordering message {sequence}",
                "plan": ["Preserve related message order"],
            }
            key = ENTITY_ID.encode() if KEYED else None
            await producer.send_and_wait(
                TASKS_TOPIC,
                json.dumps(message).encode(),
                key=key,
            )
            print(f"[ORDERING] Sent sequence={sequence} keyed={KEYED}")
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
