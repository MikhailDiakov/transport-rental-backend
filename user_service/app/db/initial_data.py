import asyncio

from app.core.config import settings
from app.core.hash import get_password_hash
from app.db.session import async_session
from app.models.role import RoleEnum
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def create_superadmin(session: AsyncSession):
    result = await session.execute(
        select(User).where(User.role_id == RoleEnum.SUPERADMIN.value)
    )
    if not result.scalars().first():
        superadmin = User(
            username=settings.SUPERADMIN_LOGIN,
            hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
            email=settings.SUPERADMIN_EMAIL,
            role_id=RoleEnum.SUPERADMIN.value,
        )
        session.add(superadmin)
        await session.commit()


async def main():
    async with async_session() as session:
        await create_superadmin(session)


if __name__ == "__main__":
    asyncio.run(main())
