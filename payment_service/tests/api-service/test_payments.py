from unittest.mock import AsyncMock, patch

from app.models.payment import Payment
from app.schemas.payment import PaymentMethod


async def test_initiate_payment_success(
    client_user, normal_user, db_session_with_rollback
):
    payload = {"booking_id": 1, "method": PaymentMethod.stripe}

    grpc_mock = AsyncMock()
    grpc_mock.success = True
    grpc_mock.user_id = normal_user["id"]
    grpc_mock.can_pay = True
    grpc_mock.total_price = 500.0

    payment_mock = Payment(
        id=123,
        booking_id=1,
        user_id=normal_user["id"],
        amount=500.0,
        currency="usd",
        status="pending",
        provider="stripe",
        provider_payment_id="sess_test_123",
    )

    with (
        patch("app.services.payment_service.get_booking_info", return_value=grpc_mock),
        patch(
            "app.services.providers.stripe_provider.StripePaymentProvider.create_payment",
            return_value=(payment_mock, "https://stripe.com/pay/123"),
        ),
        patch("app.services.payment_service.send_log", new_callable=AsyncMock),
    ):
        response = await client_user.post("/payments/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["payment"]["id"] == 123
    assert data["payment_url"] == "https://stripe.com/pay/123"


async def test_initiate_payment_booking_not_found(client_user):
    payload = {"booking_id": 999, "method": PaymentMethod.stripe}

    grpc_mock = AsyncMock()
    grpc_mock.success = False

    with (
        patch("app.services.payment_service.get_booking_info", return_value=grpc_mock),
        patch("app.services.payment_service.send_log", new_callable=AsyncMock),
    ):
        response = await client_user.post("/payments/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Booking not found or invalid"


async def test_initiate_payment_not_allowed(client_user, normal_user):
    payload = {"booking_id": 1, "method": PaymentMethod.stripe}

    grpc_mock = AsyncMock()
    grpc_mock.success = True
    grpc_mock.user_id = normal_user["id"]
    grpc_mock.can_pay = False
    grpc_mock.total_price = 500.0

    with (
        patch("app.services.payment_service.get_booking_info", return_value=grpc_mock),
        patch("app.services.payment_service.send_log", new_callable=AsyncMock),
    ):
        response = await client_user.post("/payments/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot pay for this booking"


async def test_initiate_payment_unauthorized(client_user):
    payload = {"booking_id": 1, "method": PaymentMethod.stripe}

    grpc_mock = AsyncMock()
    grpc_mock.success = True
    grpc_mock.user_id = 9999
    grpc_mock.can_pay = True
    grpc_mock.total_price = 500.0

    with (
        patch("app.services.payment_service.get_booking_info", return_value=grpc_mock),
        patch("app.services.payment_service.send_log", new_callable=AsyncMock),
    ):
        response = await client_user.post("/payments/", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to pay for this booking"


async def test_payment_success_page(client_user):
    response = await client_user.get("/payments/success")
    assert response.status_code == 200
    assert response.json() == {"message": "Payment succeeded. You can close this page."}


async def test_payment_cancel_page(client_user):
    response = await client_user.get("/payments/cancel")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Payment was cancelled. You can close this page."
    }
