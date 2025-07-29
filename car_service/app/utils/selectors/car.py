from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.car import Car


async def get_car_by_id(db: AsyncSession, car_id: int) -> Car | None:
    result = await db.execute(select(Car).where(Car.id == car_id))
    return result.scalars().first()


async def list_cars_with_pagination(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Car]:
    result = await db.execute(select(Car).offset(skip).limit(limit))
    return result.scalars().all()
