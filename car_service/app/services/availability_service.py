from datetime import date, datetime
from typing import List, Optional

from app.core.config import settings
from app.models.availability import CarAvailability
from app.utils.kafka_producer import send_log
from app.utils.selectors.car import get_car_by_id
from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

SERVICE = settings.PROJECT_NAME


def serialize_dates(d: dict) -> dict:
    return {
        k: (v.isoformat() if isinstance(v, (date, datetime)) else v)
        for k, v in d.items()
    }


async def create_availability(
    db: AsyncSession, data: dict, admin_id: int
) -> CarAvailability:
    log = {
        "service": SERVICE,
        "event": "create_availability",
        "admin_id": admin_id,
        "data": serialize_dates(data),
    }
    try:
        car = await get_car_by_id(db, data["car_id"])
        if not car:
            log.update({"result": "failure", "reason": "Car not found"})
            await send_log(log)
            raise HTTPException(status_code=404, detail="Car not found")

        if not car.is_available:
            log.update({"result": "failure", "reason": "Car is marked as unavailable"})
            await send_log(log)
            raise HTTPException(
                status_code=400,
                detail="Cannot add availability for an unavailable car",
            )
        overlapping_stmt = select(CarAvailability).where(
            CarAvailability.car_id == data["car_id"],
            or_(
                and_(
                    CarAvailability.start_date <= data["start_date"],
                    CarAvailability.end_date >= data["start_date"],
                ),
                and_(
                    CarAvailability.start_date <= data["end_date"],
                    CarAvailability.end_date >= data["end_date"],
                ),
                and_(
                    CarAvailability.start_date >= data["start_date"],
                    CarAvailability.end_date <= data["end_date"],
                ),
            ),
        )
        result = await db.execute(overlapping_stmt)
        if result.scalars().first():
            log.update({"result": "failure", "reason": "Overlap detected"})
            await send_log(log)
            raise HTTPException(
                status_code=400, detail="Availability dates overlap with existing entry"
            )

        availability = CarAvailability(**data)
        db.add(availability)
        await db.commit()
        await db.refresh(availability)
        log.update({"result": "success", "availability_id": availability.id})
        await send_log(log)
        return availability

    except Exception as e:
        log.update({"result": "failure", "error": str(e)})
        await send_log(log)
        raise


async def get_availability(
    db: AsyncSession, availability_id: int, user_id: Optional[int] = None
) -> CarAvailability:
    log = {
        "service": SERVICE,
        "event": "get_availability",
        "availability_id": availability_id,
        "user_id": user_id,
    }
    availability = await db.get(CarAvailability, availability_id)
    if not availability:
        log.update({"result": "failure", "reason": "Availability not found"})
        await send_log(log)
        raise HTTPException(status_code=404, detail="Availability not found")
    log.update({"result": "success"})
    await send_log(log)
    return availability


async def list_availabilities(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    car_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> List[CarAvailability]:
    log = {
        "service": SERVICE,
        "event": "list_availabilities",
        "skip": skip,
        "limit": limit,
        "car_id": car_id,
        "user_id": user_id,
    }
    stmt = select(CarAvailability)
    if car_id:
        stmt = stmt.where(CarAvailability.car_id == car_id)
    result = await db.execute(stmt.offset(skip).limit(limit))
    items = result.scalars().all()
    if not items:
        log.update({"result": "failure", "reason": "No availabilities found"})
        await send_log(log)
        raise HTTPException(status_code=404, detail="No availabilities found")
    log.update({"result": "success", "count": len(items)})
    await send_log(log)
    return items


async def update_availability(
    db: AsyncSession, availability_id: int, data: dict, admin_id: int
) -> CarAvailability:
    log = {
        "service": SERVICE,
        "event": "update_availability",
        "availability_id": availability_id,
        "admin_id": admin_id,
        "update_data": data,
    }
    try:
        availability = await get_availability(db, availability_id)
        for field, value in data.items():
            setattr(availability, field, value)
        await db.commit()
        await db.refresh(availability)
        log.update({"result": "success"})
        await send_log(log)
        return availability
    except Exception as e:
        log.update({"result": "failure", "error": str(e)})
        await send_log(log)
        raise


async def delete_availability(db: AsyncSession, availability_id: int, admin_id: int):
    log = {
        "service": SERVICE,
        "event": "delete_availability",
        "availability_id": availability_id,
        "admin_id": admin_id,
    }
    try:
        availability = await get_availability(db, availability_id)
        await db.delete(availability)
        await db.commit()
        log.update({"result": "success"})
        await send_log(log)
    except Exception as e:
        log.update({"result": "failure", "error": str(e)})
        await send_log(log)
        raise
