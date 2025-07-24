import asyncio

from app.kafka_consumer import consume_logs

if __name__ == "__main__":
    print("Log service started, waiting for messages...")
    asyncio.run(consume_logs())
