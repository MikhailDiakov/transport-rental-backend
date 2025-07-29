import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "User service"

    # DB
    DB_URL_ASYNC: str = os.getenv(
        "USER_DATABASE_URL_ASYNC", "sqlite+aiosqlite:///./test.db"
    )
    DB_URL_SYNC: str = os.getenv("USER_DATABASE_URL_SYNC", "sqlite:///./test.db")

    # Test database URL
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"
    )

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # SuperAdmin
    SUPERADMIN_LOGIN: str = os.getenv("SUPERADMIN_LOGIN", "admin123")
    SUPERADMIN_PASSWORD: str = os.getenv("SUPERADMIN_PASSWORD", "admin123")
    SUPERADMIN_EMAIL: str = os.getenv("SUPERADMIN_EMAIL", "admin@gmail.com")

    # GRPC PORT
    GRPC_PORT: int = os.getenv("GRPC_PORT_FOR_USER_SERVICE", 50051)

    # KAFKA SETTINGS
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC_LOGS = os.getenv("KAFKA_TOPIC_LOGS", "logs")
    KAFKA_TOPIC_NOTIFICATIONS = os.getenv("KAFKA_TOPIC_NOTIFICATIONS", "notifications")


settings = Settings()
