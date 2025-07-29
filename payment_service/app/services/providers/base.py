from abc import ABC, abstractmethod

from app.models.payment import Payment
from sqlalchemy.ext.asyncio import AsyncSession


class BasePaymentProvider(ABC):
    @abstractmethod
    async def create_payment(
        self,
        db: AsyncSession,
        booking_id: int,
        user_id: int,
        amount: float,
        currency: str = "usd",
    ) -> tuple[Payment, str]: ...
