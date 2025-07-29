from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class PaymentMethod(str, Enum):
    stripe = "stripe"
    # in the future paypal, liqpay, etc


class PaymentCreate(BaseModel):
    booking_id: int
    method: PaymentMethod


class PaymentRead(BaseModel):
    id: int
    booking_id: int
    amount: float
    currency: str
    status: str
    provider: str
    provider_payment_id: str | None

    model_config = ConfigDict(from_attributes=True)


class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class AdminPaymentRead(BaseModel):
    id: int
    booking_id: int
    provider: str
    amount: float
    currency: str
    status: PaymentStatus
    provider_payment_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentUpdate(BaseModel):
    status: PaymentStatus
