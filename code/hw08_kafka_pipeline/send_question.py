# To run each agent in own terminal
import asyncio
import json
import os
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from topics import FINAL_TOPIC, INBOX_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


async def main():
    correlation_id = str(uuid.uuid4())
    question = "How should a team prioritize a high-severity vulnerability?"
    message = {
        "correlation_id": correlation_id,
        "question": question,
    }

    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    consumer = AIOKafkaConsumer(
        FINAL_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=f"s4544-final-reader-{correlation_id}",
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )

    await producer.start()
    await consumer.start()
    print(f"[SENDER] Sending to {INBOX_TOPIC}: {json.dumps(message)}")
    await producer.send_and_wait(INBOX_TOPIC, json.dumps(message).encode())

    try:
        async for record in consumer:
            result = json.loads(record.value.decode())
            if result.get("correlation_id") == correlation_id:
                print(f"[SENDER] Final result from {FINAL_TOPIC}:")
                print(json.dumps(result, indent=2))
                break
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
