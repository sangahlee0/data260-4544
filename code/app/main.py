from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.kafka_rpc import KafkaRPC

rpc = KafkaRPC()


@asynccontextmanager
async def lifespan(app):
    await rpc.start()
    yield
    await rpc.stop()


app = FastAPI(title="Vulnerability Kafka Service", lifespan=lifespan)


@app.get("/")
async def home():
    return {"message": "FastAPI service running"}


@app.post("/vulnerabilities")
async def handle_vulnerability_operation(payload: dict):
    operation = payload.get("operation")
    data = payload.get("data", {})
    return await rpc.make_request(
        operation,
        data,
        correlation_id=payload.get("correlation_id"),
    )
