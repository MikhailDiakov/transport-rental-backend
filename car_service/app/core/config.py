import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Car service"

    # DB
    DB_URL_ASYNC: str = os.getenv(
        "CAR_DATABASE_URL_ASYNC", "sqlite+aiosqlite:///./test.db"
    )
    DB_URL_SYNC: str = os.getenv("CAR_DATABASE_URL_SYNC", "sqlite:///./test.db")

    # Test database URL
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"
    )

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # GRPC PORT
    GRPC_PORT: int = os.getenv("GRPC_PORT_FOR_CAR_SERVICE", 50052)

    # KAFKA SETTINGS
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC_LOGS = os.getenv("KAFKA_TOPIC_LOGS", "logs")
    KAFKA_TOPIC_NOTIFICATIONS = os.getenv("KAFKA_TOPIC_NOTIFICATIONS", "notifications")


settings = Settings()
