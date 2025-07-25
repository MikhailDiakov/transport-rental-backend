import json
import os
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaProducer
from app.core.config import settings

USE_KAFKA = os.getenv("USE_KAFKA", "true").lower() == "true"

producer: Optional[AIOKafkaProducer] = None


async def get_kafka_producer() -> Optional[AIOKafkaProducer]:
    global producer
    if not USE_KAFKA:
        return None
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        await producer.start()
    return producer


async def send_log(message: dict):
    if not USE_KAFKA:
        return
    prod = await get_kafka_producer()
    if prod is None:
        return
    message_with_time = message.copy()
    message_with_time["timestamp"] = datetime.now(timezone.utc).isoformat()
    data = json.dumps(message_with_time, default=str).encode("utf-8")
    await prod.send_and_wait(settings.KAFKA_TOPIC_LOGS, data)


async def send_notification_email(to_email: str, subject: str, body: str):
    if not USE_KAFKA:
        return
    prod = await get_kafka_producer()
    if prod is None:
        return
    message = {
        "type": "email",
        "to": to_email,
        "subject": subject,
        "body": body,
    }
    data = json.dumps(message).encode("utf-8")
    await prod.send_and_wait(settings.KAFKA_TOPIC_NOTIFICATIONS, data)


async def close_producer():
    global producer
    if producer:
        await producer.stop()
        producer = None
