import json
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaProducer

from .config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_LOGS

producer: Optional[AIOKafkaProducer] = None


async def get_kafka_producer() -> AIOKafkaProducer:
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await producer.start()
    return producer


async def send_log(message: dict):
    prod = await get_kafka_producer()
    message_with_time = message.copy()
    message_with_time["timestamp"] = datetime.now(timezone.utc).isoformat()
    data = json.dumps(message_with_time).encode("utf-8")
    await prod.send_and_wait(KAFKA_TOPIC_LOGS, data)


async def close_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None
