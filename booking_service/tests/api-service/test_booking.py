from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from app.models.booking import Booking


@pytest.mark.asyncio
async def test_book_car_success(client_user):
    today = date.today()
    payload = {
        "car_id": 1,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=3)).isoformat(),
    }

    mock_response = AsyncMock()
    mock_response.success = True
    mock_response.total_price = 500.0
    mock_response.message = "Booking successful"

    with (
        patch(
            "app.services.booking_service.book_car_via_grpc", return_value=mock_response
        ),
    ):
        response = await client_user.post("/booking/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["car_id"] == 1
    assert data["total_price"] == 500.0


@pytest.mark.asyncio
async def test_book_car_failure_from_grpc(client_user):
    today = date.today()
    payload = {
        "car_id": 2,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=2)).isoformat(),
    }

    mock_response = AsyncMock()
    mock_response.success = False
    mock_response.message = "Car unavailable"

    with (
        patch(
            "app.services.booking_service.book_car_via_grpc", return_value=mock_response
        ),
    ):
        response = await client_user.post("/booking/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Car unavailable"


@pytest.mark.asyncio
async def test_get_user_bookings(client_user, db_session_with_rollback, normal_user):
    booking = Booking(
        user_id=normal_user["id"],
        car_id=1,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        total_price=150.0,
        status="active",
    )
    db_session_with_rollback.add(booking)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(booking)

    response = await client_user.get("/booking/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["bookings"], list)
    assert any(b["id"] == booking.id for b in data["bookings"])


@pytest.mark.asyncio
async def test_delete_booking_success(
    client_user, db_session_with_rollback, normal_user
):
    booking = Booking(
        user_id=normal_user["id"],
        car_id=3,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=2),
        total_price=200.0,
        status="active",
    )
    db_session_with_rollback.add(booking)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(booking)

    mock_response = AsyncMock()
    mock_response.success = True

    with patch(
        "app.services.booking_service.restore_availability_via_grpc",
        return_value=mock_response,
    ):
        response = await client_user.delete(f"/booking/{booking.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_booking_not_found(client_user):
    response = await client_user.delete("/booking/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found or forbidden"


@pytest.mark.asyncio
async def test_book_car_invalid_date_range(client_user):
    today = date.today()
    payload = {
        "car_id": 1,
        "start_date": today.isoformat(),
        "end_date": (today - timedelta(days=1)).isoformat(),
    }

    response = await client_user.post("/booking/", json=payload)
    assert response.status_code == 400
