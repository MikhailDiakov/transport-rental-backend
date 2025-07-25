import pytest
from app.models.car import Car


@pytest.mark.asyncio
async def test_create_car_success(client_admin):
    payload = {"brand": "Tesla", "model": "Model S", "year": 2023, "is_available": True}
    response = await client_admin.post("/cars/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["brand"] == payload["brand"]
    assert data["model"] == payload["model"]
    assert data["year"] == payload["year"]
    assert data["is_available"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_car_forbidden(client_user):
    payload = {"brand": "Tesla", "model": "Model S", "year": 2023}
    response = await client_user.post("/cars/", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_car_validation_error(client_admin):
    payload = {"model": "Model S", "year": 2023}
    response = await client_admin.post("/cars/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_car_success(db_session_with_rollback, client_admin):
    new_car = Car(
        brand="BMW",
        model="X5",
        year=2020,
        is_available=True,
    )
    db_session_with_rollback.add(new_car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(new_car)

    car_id = new_car.id

    response = await client_admin.get(f"/cars/{car_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == car_id
    assert data["brand"] == "BMW"
    assert data["model"] == "X5"
    assert data["is_available"] is True


@pytest.mark.asyncio
async def test_get_car_not_found(client_user):
    response = await client_user.get("/cars/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_cars_success(db_session_with_rollback, client_admin):
    cars = [
        Car(brand="Audi", model="A4", year=2021, is_available=True),
        Car(brand="Mercedes", model="C300", year=2022, is_available=True),
    ]
    db_session_with_rollback.add_all(cars)
    await db_session_with_rollback.commit()

    response = await client_admin.get("/cars/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_list_cars_not_found(client_admin):
    response = await client_admin.get("/cars/")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_car_success(db_session_with_rollback, client_admin):
    car = Car(
        brand="Toyota",
        model="Corolla",
        year=2018,
        is_available=True,
    )
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    update_payload = {"model": "Camry", "year": 2019}
    response = await client_admin.put(f"/cars/{car.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "Camry"
    assert data["year"] == 2019


@pytest.mark.asyncio
async def test_update_car_not_found(client_admin):
    response = await client_admin.put("/cars/999999", json={"model": "NonExist"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_car_forbidden(client_user):
    response = await client_user.put("/cars/1", json={"model": "FailUpdate"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_car_success(db_session_with_rollback, client_admin):
    car = Car(
        brand="Ford",
        model="Focus",
        year=2017,
        is_available=True,
    )
    db_session_with_rollback.add(car)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(car)

    response = await client_admin.delete(f"/cars/{car.id}")
    assert response.status_code == 204

    deleted_car = await db_session_with_rollback.get(Car, car.id)
    assert deleted_car is None


@pytest.mark.asyncio
async def test_delete_car_forbidden(client_user):
    response = await client_user.delete("/cars/1")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_car_not_found(client_admin):
    response = await client_admin.delete("/cars/999999")
    assert response.status_code == 404
