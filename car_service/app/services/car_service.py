from typing import List

from app.models.car import Car
from app.utils.kafka_producer import send_log
from app.utils.selectors.car import get_car_by_id, list_cars_with_pagination
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


async def create_car(db: AsyncSession, car_data: dict, admin_id: int) -> Car:
    log = {
        "service": "car_service",
        "event": "create_car",
        "admin_id": admin_id,
        "car_data": car_data,
    }
    try:
        car = Car(**car_data)
        db.add(car)
        await db.commit()
        await db.refresh(car)
        log["result"] = "success"
        log["car_id"] = car.id
        await send_log(log)
        return car
    except Exception as e:
        log["result"] = "failure"
        log["error"] = str(e)
        await send_log(log)
        raise


async def get_car(db: AsyncSession, car_id: int, user_id: int | None = None) -> Car:
    log = {
        "service": "car_service",
        "event": "get_car",
        "car_id": car_id,
        "admin_id": user_id,
    }
    car = await get_car_by_id(db, car_id)
    if not car:
        log.update({"result": "failure", "reason": "Car not found"})
        await send_log(log)
        raise HTTPException(status_code=404, detail="Car not found")
    log["result"] = "success"
    await send_log(log)
    return car


async def list_cars(
    db: AsyncSession, skip: int = 0, limit: int = 100, user_id: int | None = None
) -> List[Car]:
    log = {
        "service": "car_service",
        "event": "list_cars",
        "skip": skip,
        "limit": limit,
        "admin_id": user_id,
    }
    cars = await list_cars_with_pagination(db, skip, limit)
    if not cars:
        log.update({"result": "failure", "reason": "No cars found"})
        await send_log(log)
        raise HTTPException(status_code=404, detail="No cars found")
    log["result"] = "success"
    log["count"] = len(cars)
    await send_log(log)
    return cars


async def update_car(
    db: AsyncSession, car_id: int, car_data: dict, admin_id: int
) -> Car:
    log = {
        "service": "car_service",
        "event": "update_car",
        "car_id": car_id,
        "admin_id": admin_id,
        "update_data": car_data,
    }
    try:
        car = await get_car(db, car_id, admin_id)
        for field, value in car_data.items():
            setattr(car, field, value)
        await db.commit()
        await db.refresh(car)
        log["result"] = "success"
        await send_log(log)
        return car
    except Exception as e:
        log["result"] = "failure"
        log["error"] = str(e)
        await send_log(log)
        raise


async def delete_car(db: AsyncSession, car_id: int, admin_id: int) -> None:
    log = {
        "service": "car_service",
        "event": "delete_car",
        "car_id": car_id,
        "admin_id": admin_id,
    }
    try:
        car = await get_car(db, car_id, admin_id)
        await db.delete(car)
        await db.commit()
        log["result"] = "success"
        await send_log(log)
    except Exception as e:
        log["result"] = "failure"
        log["error"] = str(e)
        await send_log(log)
        raise
