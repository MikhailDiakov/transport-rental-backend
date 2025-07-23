import json
from typing import Optional

from aiokafka import AIOKafkaProducer
from app.core.config import settings

producer: Optional[AIOKafkaProducer] = None


async def get_kafka_producer() -> AIOKafkaProducer:
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        await producer.start()
    return producer


async def send_log(message: dict):
    prod = await get_kafka_producer()
    data = json.dumps(message).encode("utf-8")
    await prod.send_and_wait(settings.KAFKA_TOPIC, data)


async def close_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None
