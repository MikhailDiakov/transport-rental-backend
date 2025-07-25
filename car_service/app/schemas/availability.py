from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CarAvailabilityBase(BaseModel):
    car_id: int
    start_date: date
    end_date: date
    price_per_day: float = Field(gt=0)


class CarAvailabilityCreate(CarAvailabilityBase):
    pass


class CarAvailabilityUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    price_per_day: Optional[float] = None


class CarAvailabilityRead(CarAvailabilityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
