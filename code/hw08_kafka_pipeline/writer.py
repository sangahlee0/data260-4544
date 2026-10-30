# To run each agent in own terminal
import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from topics import DEAD_LETTER_TOPIC, DRAFTS_TOPIC, TASKS_TOPIC

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
WRITER_GROUP_ID = os.getenv("WRITER_GROUP_ID", "s4544-writer-group")
WRITER_INSTANCE = os.getenv("WRITER_INSTANCE", "writer")
processed_correlation_ids = set()
CRASH_AFTER_RECEIVE = os.getenv("CRASH_AFTER_RECEIVE") == "1"
MAX_RETRIES = 3


def write_draft(question, plan):
    return (
        f"The question was: {question} "
        f"The response follows this plan: {', '.join(plan)}."
    )


def validate_task(incoming):
    if not incoming.get("correlation_id"):
        return "correlation_id is required"
    if not incoming.get("question"):
        return "question is required"
    if not isinstance(incoming.get("plan"), list) or not incoming["plan"]:
        return "plan is required"
    return None


async def main():
    consumer = AIOKafkaConsumer(
        TASKS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=WRITER_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()
    print(f"[WRITER-{WRITER_INSTANCE}] Listening on {TASKS_TOPIC}")

    try:
        async for message in consumer:
            incoming = json.loads(message.value.decode())
            validation_error = validate_task(incoming)
            if validation_error:
                retry_count = incoming.get("retry_count", 0)
                if retry_count < MAX_RETRIES:
                    retry_message = {
                        **incoming,
                        "retry_count": retry_count + 1,
                        "error": validation_error,
                    }
                    print(
                        f"[WRITER] Poison message retry "
                        f"{retry_count + 1}/{MAX_RETRIES}: "
                        f"{validation_error}"
                    )
                    await producer.send_and_wait(
                        TASKS_TOPIC,
                        json.dumps(retry_message).encode(),
                        key=str(incoming.get("correlation_id", "poison")).encode(),
                    )
                else:
                    dead_letter = {
                        **incoming,
                        "dead_letter": True,
                        "error": validation_error,
                    }
                    print(
                        f"[WRITER] Moving poison message to "
                        f"{DEAD_LETTER_TOPIC} after {MAX_RETRIES} retries"
                    )
                    await producer.send_and_wait(
                        DEAD_LETTER_TOPIC,
                        json.dumps(dead_letter).encode(),
                    )
                await consumer.commit()
                continue

            correlation_id = incoming["correlation_id"]
            if correlation_id in processed_correlation_ids:
                print(
                    f"[WRITER-{WRITER_INSTANCE}] Duplicate correlation_id "
                    f"ignored: {correlation_id}"
                )
                continue

            if CRASH_AFTER_RECEIVE:
                print(
                    f"[WRITER-{WRITER_INSTANCE}] Simulating consumer death before commit for "
                    f"{correlation_id}"
                )
                raise RuntimeError("Simulated writer failure")

            processed_correlation_ids.add(correlation_id)
            outgoing = {
                "correlation_id": correlation_id,
                "question": incoming["question"],
                "plan": incoming["plan"],
                "draft": write_draft(incoming["question"], incoming["plan"]),
            }
            print(
                f"[WRITER-{WRITER_INSTANCE}] Received partition="
                f"{message.partition} offset={message.offset} "
                f"sequence={incoming.get('sequence')} "
                f"correlation_id={correlation_id}"
            )
            print(
                f"[WRITER-{WRITER_INSTANCE}] Sending to {DRAFTS_TOPIC}: "
                f"{json.dumps(outgoing)}"
            )
            await producer.send_and_wait(DRAFTS_TOPIC, json.dumps(outgoing).encode())
            await consumer.commit()
            print(f"[WRITER-{WRITER_INSTANCE}] Offset committed for {correlation_id}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
