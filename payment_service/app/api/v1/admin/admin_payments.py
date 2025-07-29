from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_admin
from app.schemas.payment import AdminPaymentRead, AdminPaymentUpdate
from app.services.admin.admin_payment_service import (
    admin_get_payment,
    admin_list_payments,
    admin_update_payment_status,
)

router = APIRouter()


@router.get("/", response_model=list[AdminPaymentRead])
async def list_payments_endpoint(
    skip: int = 0,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    return await admin_list_payments(db, skip=skip, limit=limit, admin_id=admin["id"])


@router.get("/{payment_id}", response_model=AdminPaymentRead)
async def get_payment_endpoint(
    payment_id: int,
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    payment = await admin_get_payment(db, payment_id=payment_id, admin_id=admin["id"])
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.patch("/{payment_id}", response_model=AdminPaymentRead)
async def update_payment_status_endpoint(
    payment_id: int,
    data: AdminPaymentUpdate,
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    payment = await admin_update_payment_status(
        db, payment_id=payment_id, new_status=data.status, admin_id=admin["id"]
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
