# To run each agent in own terminal
import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from topics import DRAFTS_TOPIC, FINAL_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def review_draft(draft):
    if not draft.strip():
        return {"status": "rejected", "answer": "Draft was empty"}
    return {"status": "approved", "answer": draft}


async def main():
    consumer = AIOKafkaConsumer(
        DRAFTS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="s4544-reviewer-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()
    print(f"[REVIEWER] Listening on {DRAFTS_TOPIC}")

    try:
        async for message in consumer:
            incoming = json.loads(message.value.decode())
            review = review_draft(incoming["draft"])
            outgoing = {
                "correlation_id": incoming["correlation_id"],
                "status": review["status"],
                "answer": review["answer"],
            }
            print(f"[REVIEWER] Received: {json.dumps(incoming)}")
            print(f"[REVIEWER] Sending to {FINAL_TOPIC}: {json.dumps(outgoing)}")
            await producer.send_and_wait(FINAL_TOPIC, json.dumps(outgoing).encode())
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
