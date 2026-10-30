import asyncio
import json
import os
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REQUEST_TOPIC = "s4544_vulnerability_requests"
RESPONSE_TOPIC = "s4544_vulnerability_responses"
TIMEOUT_SECONDS = 8


class KafkaRPC:
    def __init__(self):
        self.producer = None
        self.consumer = None
        self.pending = {}
        self.consumer_task = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        self.consumer = AIOKafkaConsumer(
            RESPONSE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="s4544-fastapi-response-group",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self.producer.start()
        await self.consumer.start()
        self.consumer_task = asyncio.create_task(self.consume_responses())
        print("FastAPI KafkaRPC started")
        print(f"Listening for Kafka responses on topic: {RESPONSE_TOPIC}")

    async def stop(self):
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass
        if self.consumer is not None:
            await self.consumer.stop()
        if self.producer is not None:
            await self.producer.stop()
        print("FastAPI KafkaRPC stopped")

    async def consume_responses(self):
        async for message in self.consumer:
            response = json.loads(message.value.decode())
            correlation_id = response.get("correlation_id")
            print(f"[FASTAPI] Received response from topic={message.topic}")
            print(f"[FASTAPI] correlation_id={correlation_id}")
            print(f"[FASTAPI] response={json.dumps(response, indent=2)}")

            future = self.pending.pop(correlation_id, None)
            if future is not None and not future.done():
                future.set_result(response)

    async def make_request(self, operation, data, correlation_id=None):
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        request = {
            "correlation_id": correlation_id,
            "reply_to": RESPONSE_TOPIC,
            "operation": operation,
            "data": data,
        }
        future = asyncio.get_event_loop().create_future()
        self.pending[correlation_id] = future

        print("[FASTAPI] Sending request to Kafka")
        print(f"[FASTAPI] topic={REQUEST_TOPIC}")
        print(f"[FASTAPI] request={json.dumps(request, indent=2)}")
        await self.producer.send_and_wait(
            REQUEST_TOPIC,
            json.dumps(request).encode(),
        )
        print(f"[FASTAPI] Sent request to topic={REQUEST_TOPIC}")

        try:
            response = await asyncio.wait_for(future, timeout=TIMEOUT_SECONDS)
            print("[FASTAPI] Returning response to caller")
            return response
        except asyncio.TimeoutError:
            self.pending.pop(correlation_id, None)
            return {
                "correlation_id": correlation_id,
                "success": False,
                "error": "Kafka response timeout",
            }
