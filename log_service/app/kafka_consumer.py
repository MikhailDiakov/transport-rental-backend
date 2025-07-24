import json

from aiokafka import AIOKafkaConsumer

from app.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from app.elastic import save_log


async def consume_logs():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="log-consumer-group",
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    print("Log service started, waiting for messages...")
    try:
        async for message in consumer:
            await save_log(message.value)
    finally:
        await consumer.stop()
        await es.close()
