from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.DB_URL_ASYNC, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)
