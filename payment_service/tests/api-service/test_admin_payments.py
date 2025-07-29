from datetime import UTC, datetime

from app.models.payment import Payment
from app.schemas.payment import PaymentStatus
from fastapi import status


async def test_admin_list_payments(client_admin, db_session_with_rollback):
    payment = Payment(
        booking_id=1,
        user_id=1,
        provider="stripe",
        amount=100.0,
        currency="USD",
        status=PaymentStatus.succeeded,
        provider_payment_id="pi_12345",
        created_at=datetime.now(UTC),
    )

    db_session_with_rollback.add(payment)
    await db_session_with_rollback.commit()

    response = await client_admin.get("/admin/payments/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(p["id"] == payment.id for p in data)


async def test_admin_get_payment_success(client_admin, db_session_with_rollback):
    payment = Payment(
        booking_id=1,
        user_id=1,
        provider="stripe",
        amount=50.0,
        currency="EUR",
        status=PaymentStatus.pending,
        provider_payment_id="pi_99999",
        created_at=datetime.now(UTC),
    )
    db_session_with_rollback.add(payment)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(payment)

    response = await client_admin.get(f"/admin/payments/{payment.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == payment.id
    assert data["status"] == "pending"


async def test_admin_get_payment_not_found(client_admin):
    response = await client_admin.get("/admin/payments/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


async def test_admin_update_payment_status_success(
    client_admin, db_session_with_rollback
):
    payment = Payment(
        booking_id=2,
        user_id=1,
        provider="stripe",
        amount=120.0,
        currency="GBP",
        status=PaymentStatus.pending,
        provider_payment_id="pi_test123",
        created_at=datetime.now(UTC),
    )
    db_session_with_rollback.add(payment)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(payment)

    update_payload = {"status": "cancelled"}

    response = await client_admin.patch(
        f"/admin/payments/{payment.id}", json=update_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


async def test_admin_update_payment_status_not_found(client_admin):
    update_payload = {"status": "failed"}

    response = await client_admin.patch("/admin/payments/999999", json=update_payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


async def test_user_cannot_access_admin_payment_endpoints(client_user):
    endpoints = [
        ("get", "/admin/payments/"),
        ("get", "/admin/payments/1"),
        ("patch", "/admin/payments/1", {"json": {"status": "cancelled"}}),
    ]

    for method, url, *args in endpoints:
        kwargs = args[0] if args else {}
        response = await getattr(client_user, method)(url, **kwargs)
        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            f"{method.upper()} {url} must be forbidden"
        )
