from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):
    car_id: int
    start_date: date
    end_date: date


class AdminBookingCreate(BookingCreate):
    user_id: int


class BookingRead(BaseModel):
    id: int
    user_id: int
    car_id: int
    start_date: date
    end_date: date
    total_price: float
    status: str

    model_config = ConfigDict(from_attributes=True)


class BookingListRead(BaseModel):
    bookings: list[BookingRead]


class BookingUpdate(BaseModel):
    status: Optional[str] = None
    total_price: Optional[float] = None
