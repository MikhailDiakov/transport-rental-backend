import json
from unittest.mock import AsyncMock, patch

import pytest
from app.core.config import settings
from app.utils.kafka_producer import close_producer, send_log, send_notification_email


@pytest.mark.asyncio
@patch("app.utils.kafka_producer.get_kafka_producer")
async def test_send_log_sends_message_with_timestamp(mock_get_producer):
    mock_producer = AsyncMock()
    mock_get_producer.return_value = mock_producer

    await send_log({"action": "test"})

    args, kwargs = mock_producer.send_and_wait.call_args
    topic, data = args

    assert topic == settings.KAFKA_TOPIC_LOGS
    assert b"timestamp" in data
    assert b"test" in data


@pytest.mark.asyncio
@patch("app.utils.kafka_producer.get_kafka_producer")
async def test_send_notification_email_sends_correct_message(mock_get_producer):
    mock_producer = AsyncMock()
    mock_get_producer.return_value = mock_producer

    await send_notification_email("user@example.com", "Hello", "This is a test.")

    args, kwargs = mock_producer.send_and_wait.call_args
    topic, data = args

    assert topic == settings.KAFKA_TOPIC_NOTIFICATIONS
    payload = json.loads(data.decode())
    assert payload["to"] == "user@example.com"
    assert payload["type"] == "email"


@pytest.mark.asyncio
@patch("app.utils.kafka_producer.producer", new_callable=AsyncMock)
async def test_close_producer(mock_producer):
    from app.utils import kafka_producer

    kafka_producer.producer = mock_producer

    await close_producer()

    mock_producer.stop.assert_awaited_once()
    assert kafka_producer.producer is None
