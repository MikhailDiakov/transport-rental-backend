from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from app.models.booking import Booking
from fastapi import status


@pytest.mark.asyncio
async def test_admin_create_booking_success(client_admin):
    today = date.today()
    payload = {
        "car_id": 1,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=2)).isoformat(),
        "user_id": 42,
    }

    grpc_response = AsyncMock()
    grpc_response.success = True
    grpc_response.total_price = 777.0
    grpc_response.message = "Created"

    with (
        patch(
            "app.services.admin.admin_booking_service.validate_user_exists",
            return_value=True,
        ),
        patch(
            "app.services.admin.admin_booking_service.book_car_via_grpc",
            return_value=grpc_response,
        ),
    ):
        response = await client_admin.post("/admin/booking/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["car_id"] == 1
    assert data["user_id"] == 42
    assert data["total_price"] == 777.0


@pytest.mark.asyncio
async def test_admin_create_booking_user_not_found(client_admin):
    today = date.today()
    payload = {
        "car_id": 1,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=2)).isoformat(),
        "user_id": 999,
    }

    with (
        patch(
            "app.services.admin.admin_booking_service.validate_user_exists",
            return_value=False,
        ),
    ):
        response = await client_admin.post("/admin/booking/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "User does not exist"


@pytest.mark.asyncio
async def test_admin_get_booking_success(client_admin, db_session_with_rollback):
    booking = Booking(
        user_id=10,
        car_id=1,
        start_date=date.today(),
        end_date=date.today(),
        total_price=100.0,
        status="active",
    )
    db_session_with_rollback.add(booking)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(booking)

    response = await client_admin.get(f"/admin/booking/{booking.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == booking.id
    assert data["user_id"] == 10


@pytest.mark.asyncio
async def test_admin_get_booking_not_found(client_admin):
    response = await client_admin.get("/admin/booking/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.asyncio
async def test_admin_list_bookings(client_admin, db_session_with_rollback):
    booking = Booking(
        user_id=1,
        car_id=2,
        start_date=date.today(),
        end_date=date.today(),
        total_price=150.0,
        status="active",
    )
    db_session_with_rollback.add(booking)
    await db_session_with_rollback.commit()

    response = await client_admin.get("/admin/booking/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["bookings"], list)
    assert any(b["id"] == booking.id for b in data["bookings"])


@pytest.mark.asyncio
async def test_admin_update_booking_success(client_admin, db_session_with_rollback):
    booking = Booking(
        user_id=10,
        car_id=2,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        total_price=200.0,
        status="active",
    )
    db_session_with_rollback.add(booking)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(booking)

    update_payload = {
        "status": "cancelled",
        "total_price": 123.0,
    }

    response = await client_admin.put(
        f"/admin/booking/{booking.id}", json=update_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["total_price"] == 123.0


@pytest.mark.asyncio
async def test_admin_update_booking_not_found(client_admin):
    response = await client_admin.put(
        "/admin/booking/999999", json={"status": "cancelled"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.asyncio
async def test_admin_delete_booking_success(client_admin, db_session_with_rollback):
    booking = Booking(
        user_id=10,
        car_id=1,
        start_date=date.today(),
        end_date=date.today(),
        total_price=100.0,
        status="active",
    )
    db_session_with_rollback.add(booking)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(booking)

    grpc_response = AsyncMock()
    grpc_response.success = True

    with (
        patch(
            "app.services.admin.admin_booking_service.restore_availability_via_grpc",
            return_value=grpc_response,
        ),
    ):
        response = await client_admin.delete(f"/admin/booking/{booking.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_delete_booking_not_found(client_admin):
    grpc_response = AsyncMock()
    grpc_response.success = True

    with (
        patch(
            "app.services.admin.admin_booking_service.restore_availability_via_grpc",
            return_value=grpc_response,
        ),
    ):
        response = await client_admin.delete("/admin/booking/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found or failed to delete"


@pytest.mark.asyncio
async def test_user_cannot_access_admin_booking_endpoints(client_user):
    today = date.today()
    payload = {
        "car_id": 1,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=2)).isoformat(),
        "user_id": 42,
    }

    endpoints = [
        ("post", "/admin/booking/", {"json": payload}),
        ("get", "/admin/booking/1", {}),
        ("get", "/admin/booking/", {}),
        ("put", "/admin/booking/1", {"json": {"status": "cancelled"}}),
        ("delete", "/admin/booking/1", {}),
    ]

    for method, url, kwargs in endpoints:
        response = await getattr(client_user, method)(url, **kwargs)
        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            f"{method.upper()} {url} should return 403"
        )
