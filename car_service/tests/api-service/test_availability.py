from datetime import date, timedelta

import pytest
from app.models.availability import CarAvailability
from app.models.car import Car


@pytest.mark.asyncio
async def test_create_availability_success(db_session_with_rollback, client_admin):
    car = Car(brand="Tesla", model="Model 3", year=2021, is_available=True)
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    start = date.today()
    end = start + timedelta(days=5)

    payload = {
        "car_id": car.id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "price_per_day": 50.0,
    }
    response = await client_admin.post("/cars-availability/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["car_id"] == car.id
    assert data["price_per_day"] == 50.0
    assert "id" in data


@pytest.mark.asyncio
async def test_create_availability_for_unavailable_car(
    db_session_with_rollback, client_admin
):
    car = Car(brand="Audi", model="A6", year=2019, is_available=False)
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    start = date.today()
    end = start + timedelta(days=3)

    payload = {
        "car_id": car.id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "price_per_day": 30.0,
    }
    response = await client_admin.post("/cars-availability/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot add availability for an unavailable car"


@pytest.mark.asyncio
async def test_create_availability_overlap(db_session_with_rollback, client_admin):
    car = Car(brand="BMW", model="X3", year=2020, is_available=True)
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    availability1 = CarAvailability(
        car_id=car.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=5),
        price_per_day=40.0,
    )
    db_session_with_rollback.add(availability1)
    await db_session_with_rollback.commit()

    payload = {
        "car_id": car.id,
        "start_date": (date.today() + timedelta(days=3)).isoformat(),
        "end_date": (date.today() + timedelta(days=7)).isoformat(),
        "price_per_day": 45.0,
    }
    response = await client_admin.post("/cars-availability/", json=payload)
    assert response.status_code == 400
    assert "overlap" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_availability_success(db_session_with_rollback, client_admin):
    car = Car(brand="Honda", model="Civic", year=2018, is_available=True)
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    availability = CarAvailability(
        car_id=car.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=2),
        price_per_day=25.0,
    )
    db_session_with_rollback.add(availability)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(availability)

    response = await client_admin.get(f"/cars-availability/{availability.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == availability.id
    assert data["car_id"] == car.id


@pytest.mark.asyncio
async def test_get_availability_not_found(client_user):
    response = await client_user.get("/cars-availability/9999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_availabilities_success(db_session_with_rollback, client_admin):
    car = Car(brand="Ford", model="Focus", year=2017, is_available=True)
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    availabilities = [
        CarAvailability(
            car_id=car.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            price_per_day=20.0,
        ),
        CarAvailability(
            car_id=car.id,
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=4),
            price_per_day=22.0,
        ),
    ]
    db_session_with_rollback.add_all(availabilities)
    await db_session_with_rollback.commit()

    response = await client_admin.get(f"/cars-availability/?car_id={car.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_list_availabilities_not_found(client_admin):
    response = await client_admin.get("/cars-availability/")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_availability_success(db_session_with_rollback, client_admin):
    car = Car(brand="Kia", model="Rio", year=2019, is_available=True)
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    availability = CarAvailability(
        car_id=car.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=3),
        price_per_day=18.0,
    )
    db_session_with_rollback.add(availability)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(availability)

    update_payload = {"price_per_day": 20.0}
    response = await client_admin.put(
        f"/cars-availability/{availability.id}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price_per_day"] == 20.0


@pytest.mark.asyncio
async def test_update_availability_not_found(client_admin):
    update_payload = {"price_per_day": 100.0}
    response = await client_admin.put("/cars-availability/999999", json=update_payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_availability_forbidden(client_user):
    response = await client_user.put(
        "/cars-availability/1", json={"price_per_day": 100}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_availability_success(db_session_with_rollback, client_admin):
    car = Car(brand="Mazda", model="3", year=2020, is_available=True)
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    availability = CarAvailability(
        car_id=car.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        price_per_day=15.0,
    )
    db_session_with_rollback.add(availability)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(availability)

    response = await client_admin.delete(f"/cars-availability/{availability.id}")
    assert response.status_code == 204

    deleted = await db_session_with_rollback.get(CarAvailability, availability.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_availability_forbidden(client_user):
    response = await client_user.delete("/cars-availability/1")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_availability_not_found(client_admin):
    response = await client_admin.delete("/cars-availability/999999")
    assert response.status_code == 404
