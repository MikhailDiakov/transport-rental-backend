from unittest.mock import AsyncMock, patch

import pytest


async def test_register_user(client):
    response = await client.post(
        "/users/register",
        json={
            "username": "testreguser",
            "email": "testreguser@example.com",
            "password": "testreguser1#",
            "confirm_password": "testreguser1#",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testreguser"
    assert data["email"] == "testreguser@example.com"


@pytest.mark.parametrize(
    "payload, expected_error",
    [
        (
            {
                "username": "u",
                "email": "test@example.com",
                "password": "pass123#",
                "confirm_password": "pass123#",
            },
            "Username must be between 3 and 50 characters",
        ),
        (
            {
                "username": "user",
                "email": "invalid-email",
                "password": "pass123#",
                "confirm_password": "pass123#",
            },
            "value is not a valid email address",
        ),
        (
            {
                "username": "user",
                "email": "test@example.com",
                "password": "pass",
                "confirm_password": "pass",
            },
            "Password must be at least 6 characters",
        ),
        (
            {
                "username": "user",
                "email": "test@example.com",
                "password": "pass123#",
                "confirm_password": "pass124#",
            },
            "Passwords do not match",
        ),
    ],
)
async def test_register_invalid_input(client, payload, expected_error):
    response = await client.post("/users/register", json=payload)
    assert response.status_code == 422
    assert expected_error in response.text


async def test_login_user(client):
    response = await client.post(
        "/users/login",
        data={"username": "clientuser", "password": "client123#"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


async def test_login_admin(client):
    response = await client.post(
        "/users/login",
        data={"username": "adminka", "password": "adminka"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


@pytest.mark.parametrize(
    "data, expected_status, expected_detail",
    [
        (
            {"username": "wronguser", "password": "client123#"},
            401,
            "Invalid credentials",
        ),
        (
            {"username": "clientuser", "password": "wrongpassword"},
            401,
            "Invalid credentials",
        ),
        ({"username": "testuser"}, 422, None),
        ({}, 422, None),
    ],
)
async def test_login_invalid_cases(client, data, expected_status, expected_detail):
    response = await client.post(
        "/users/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json()["detail"] == expected_detail


async def test_token_refresh_success(client):
    token = "valid_refresh_token"
    payload = {"id": "3", "role": "3"}

    with (
        patch("app.services.user_service.decode_refresh_token", return_value=payload),
        patch(
            "app.services.user_service.get_refresh_token", new_callable=AsyncMock
        ) as mock_get_token,
        patch(
            "app.services.user_service.create_access_token",
            return_value="new_access_token",
        ),
    ):
        mock_get_token.return_value = token

        client.cookies.set("refresh_token", token)
        response = await client.post("/users/refresh")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["token_type"] == "bearer"


@pytest.mark.parametrize(
    "cookie, decode_return, redis_token, expected_detail",
    [
        (None, None, None, "Missing refresh token"),
        ("invalid_token", None, None, "Invalid refresh token"),
        ("mismatch_token", {"id": "3", "role": "3"}, "another_token", "Token mismatch"),
    ],
)
async def test_token_refresh_failures(
    client, cookie, decode_return, redis_token, expected_detail
):
    with (
        patch(
            "app.services.user_service.decode_refresh_token", return_value=decode_return
        ),
        patch(
            "app.services.user_service.get_refresh_token",
            new_callable=AsyncMock,
            return_value=redis_token,
        ),
    ):
        if cookie:
            client.cookies.set("refresh_token", cookie)
        else:
            client.cookies.clear()

        response = await client.post("/users/refresh")
        assert response.status_code == 401, response.text
        assert expected_detail in response.text


async def test_logout_user_success(super_admin_client):
    with patch("app.utils.redis_client.delete_refresh_token", new_callable=AsyncMock):
        response = await super_admin_client.post("/users/logout")
        assert response.status_code == 200
        assert response.json() == {"message": "Logged out"}
        assert "refresh_token" not in response.cookies
