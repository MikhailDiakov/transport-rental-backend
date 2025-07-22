import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "User service"

    # DB
    DB_URL_ASYNC: str = os.getenv(
        "DATABASE_URL_ASYNC", "sqlite+aiosqlite:///./barbershop.db"
    )
    DB_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC", "sqlite:///./barbershop.db")

    # Test database URL
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"
    )

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
    )
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


settings = Settings()
