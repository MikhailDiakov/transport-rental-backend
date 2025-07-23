import json

from kafka import KafkaConsumer

from app.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from app.elastic import save_log


def consume_logs():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="log-consumer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    for message in consumer:
        save_log(message.value)
