from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CarBase(BaseModel):
    brand: str
    model: str
    year: Optional[int]


class CarCreate(CarBase):
    is_available: Optional[bool] = True


class CarUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    is_available: Optional[bool] = None


class CarRead(CarBase):
    id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
