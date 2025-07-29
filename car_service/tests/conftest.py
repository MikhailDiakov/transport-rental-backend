from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user_info, get_session, require_admin
from app.core.config import settings
from app.db.base import Base
from app.main import app

TEST_DATABASE_URL = settings.TEST_DATABASE_URL

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session_with_rollback():
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            async_session = async_sessionmaker(
                bind=connection, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                yield session
            await transaction.rollback()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def mock_kafka(monkeypatch):
    monkeypatch.setattr("app.utils.kafka_producer.get_kafka_producer", AsyncMock())
    monkeypatch.setattr("app.utils.kafka_producer.send_log", AsyncMock())
    monkeypatch.setattr("app.utils.kafka_producer.close_producer", AsyncMock())


@pytest_asyncio.fixture(scope="function")
async def admin_user():
    return {"id": 1, "role": 1}


@pytest_asyncio.fixture(scope="function")
async def normal_user():
    return {"id": 10, "role": 2}


@pytest_asyncio.fixture(scope="function")
async def client_admin(db_session_with_rollback, admin_user):
    app.dependency_overrides[get_session] = lambda: db_session_with_rollback
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_current_user_info] = lambda: admin_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def client_user(db_session_with_rollback, normal_user):
    app.dependency_overrides[get_session] = lambda: db_session_with_rollback

    def raise_forbidden():
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not admin")

    app.dependency_overrides[require_admin] = raise_forbidden

    app.dependency_overrides[get_current_user_info] = lambda: normal_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
