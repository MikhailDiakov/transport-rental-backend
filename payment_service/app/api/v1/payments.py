from app.api.deps import get_current_user_info, get_session
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.payment_service import create_payment
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/")
async def initiate_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    payment, url = await create_payment(db, data, current_user)
    return {
        "payment": PaymentRead.model_validate(payment),
        "payment_url": url,
    }


@router.get("/success", include_in_schema=False)
async def payment_success():
    return {"message": "Payment succeeded. You can close this page."}


@router.get("/cancel", include_in_schema=False)
async def payment_cancel():
    return {"message": "Payment was cancelled. You can close this page."}
