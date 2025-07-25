import asyncio
import json

from aiokafka import AIOKafkaConsumer

from .config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from .email_sender import send_email
from .kafka import send_log


async def consume_notifications():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service-group",
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    await consumer.start()
    await send_log(
        {
            "service": "notification_service",
            "event": "service_start",
            "message": "Notification service started, waiting for messages...",
        }
    )
    try:
        async for message in consumer:
            data = message.value
            msg_type = data.get("type")

            log_base = {
                "service": "notification_service",
                "event": "consume_notification",
                "type": msg_type,
                "to": data.get("to"),
            }

            if msg_type == "email":
                try:
                    await send_email(
                        to_email=data["to"],
                        subject=data.get("subject", ""),
                        body=data.get("body", ""),
                    )
                    log = {**log_base, "result": "success"}

                except Exception as e:
                    log = {**log_base, "result": "failure", "reason": str(e)}
            else:
                log = {
                    **log_base,
                    "result": "failure",
                    "reason": f"Unknown notification type: {msg_type}",
                }
            await send_log(log)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume_notifications())
