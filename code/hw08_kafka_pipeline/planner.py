# To run each agent in own terminal
import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from topics import INBOX_TOPIC, TASKS_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def make_plan(question):
    return [
        "Identify the main question",
        "Use the available vulnerability information",
        "Write a concise answer",
    ]


async def main():
    consumer = AIOKafkaConsumer(
        INBOX_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="s4544-planner-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()
    print(f"[PLANNER] Listening on {INBOX_TOPIC}")

    try:
        async for message in consumer:
            incoming = json.loads(message.value.decode())
            plan = make_plan(incoming["question"])
            outgoing = {
                "correlation_id": incoming["correlation_id"],
                "question": incoming["question"],
                "plan": plan,
            }
            print(f"[PLANNER] Received: {json.dumps(incoming)}")
            print(f"[PLANNER] Sending to {TASKS_TOPIC}: {json.dumps(outgoing)}")
            await producer.send_and_wait(TASKS_TOPIC, json.dumps(outgoing).encode())
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
