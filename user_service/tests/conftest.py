from unittest.mock import AsyncMock

import pytest_asyncio
from app.api.deps import get_session
from app.core.config import settings
from app.core.hash import get_password_hash
from app.db.base import Base
from app.main import app
from app.models.role import RoleEnum
from app.models.user import User
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = settings.TEST_DATABASE_URL

engine = create_async_engine(TEST_DATABASE_URL, echo=False)

TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            users = [
                User(
                    username=settings.SUPERADMIN_LOGIN,
                    email="superadmin@example.com",
                    hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                    role_id=RoleEnum.SUPERADMIN.value,
                ),
                User(
                    username="adminka",
                    email="admin@example.com",
                    hashed_password=get_password_hash("adminka"),
                    role_id=RoleEnum.ADMIN.value,
                ),
                User(
                    username="clientuser",
                    email="clientuser@example.com",
                    hashed_password=get_password_hash("client123#"),
                    role_id=RoleEnum.CLIENT.value,
                ),
            ]
            session.add_all(users)
            await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session_with_rollback():
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            async with TestingSessionLocal(bind=connection) as session:
                yield session
            await transaction.rollback()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def mock_external_dependencies(monkeypatch):
    # Mock FastAPI Limiter
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

    # Mock Redis Client
    from app.utils import redis_client as redis_module

    monkeypatch.setattr(redis_module, "redis_client", AsyncMock())

    # Mock Kafka Producer
    mock_producer = AsyncMock()
    monkeypatch.setattr(
        "app.utils.kafka_producer.get_kafka_producer",
        AsyncMock(return_value=mock_producer),
    )
    monkeypatch.setattr("app.utils.kafka_producer.send_log", AsyncMock())
    monkeypatch.setattr("app.utils.kafka_producer.close_producer", AsyncMock())


@pytest_asyncio.fixture(scope="function")
async def client(db_session_with_rollback):
    app.dependency_overrides[get_session] = lambda: db_session_with_rollback

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def get_authorized_client(username: str, password: str, db_session):
    app.dependency_overrides[get_session] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/users/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        ac.headers.update({"Authorization": f"Bearer {token}"})
        yield ac


@pytest_asyncio.fixture(scope="function")
async def client_user(db_session_with_rollback):
    async for ac in get_authorized_client(
        "clientuser", "client123#", db_session_with_rollback
    ):
        yield ac


@pytest_asyncio.fixture(scope="function")
async def admin_client(db_session_with_rollback):
    async for ac in get_authorized_client(
        "adminka", "adminka", db_session_with_rollback
    ):
        yield ac


@pytest_asyncio.fixture(scope="function")
async def super_admin_client(db_session_with_rollback):
    async for ac in get_authorized_client(
        settings.SUPERADMIN_LOGIN,
        settings.SUPERADMIN_PASSWORD,
        db_session_with_rollback,
    ):
        yield ac
