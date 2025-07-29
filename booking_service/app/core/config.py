import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Booking service"

    # DB
    DB_URL_ASYNC: str = os.getenv(
        "BOOKING_DATABASE_URL_ASYNC", "sqlite+aiosqlite:///./test.db"
    )
    DB_URL_SYNC: str = os.getenv("BOOKING_DATABASE_URL_SYNC", "sqlite:///./test.db")

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
    GRPC_HOST_FOR_USER_SERVICE: str = os.getenv(
        "GRPC_HOST_FOR_USER_SERVICE", "user_service"
    )
    GRPC_PORT_FOR_USER_SERVICE: int = int(
        os.getenv("GRPC_PORT_FOR_USER_SERVICE", 50051)
    )
    GRPC_HOST_FOR_CAR_SERVICE: str = os.getenv(
        "GRPC_HOST_FOR_CAR_SERVICE", "car_service"
    )
    GRPC_PORT_FOR_CAR_SERVICE: int = int(os.getenv("GRPC_PORT_FOR_CAR_SERVICE", 50052))
    GRPC_HOST_FOR_BOOKING_SERVICE: str = os.getenv(
        "GRPC_HOST_FOR_BOOKING_SERVICE", "booking_service"
    )
    GRPC_PORT_FOR_BOOKING_SERVICE: int = int(
        os.getenv("GRPC_PORT_FOR_BOOKING_SERVICE", 50053)
    )

    @property
    def CAR_GRPC_HOST(self) -> str:
        return f"{self.GRPC_HOST_FOR_CAR_SERVICE}:{self.GRPC_PORT_FOR_CAR_SERVICE}"

    @property
    def USER_GRPC_HOST(self) -> str:
        return f"{self.GRPC_HOST_FOR_USER_SERVICE}:{self.GRPC_PORT_FOR_USER_SERVICE}"

    # KAFKA SETTINGS
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC_LOGS = os.getenv("KAFKA_TOPIC_LOGS", "logs")
    KAFKA_TOPIC_NOTIFICATIONS = os.getenv("KAFKA_TOPIC_NOTIFICATIONS", "notifications")


settings = Settings()
