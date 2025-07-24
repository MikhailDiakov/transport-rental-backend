from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_my_user(client_user):
    response = await client_user.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "clientuser"
    assert data["email"] == "clientuser@example.com"


@pytest.mark.asyncio
async def test_get_my_user_admin(admin_client):
    response = await admin_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "adminka"
    assert data["email"] == "admin@example.com"


@pytest.mark.asyncio
async def test_get_my_user_unauthorized(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_my_profile_success(client_user):
    response = await client_user.put(
        "/users/me/update",
        json={
            "email": "updateduser@example.com",
            "old_password": "client123#",
            "new_password": "newclient123#",
            "confirm_password": "newclient123#",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updateduser@example.com"


@pytest.mark.asyncio
async def test_update_my_profile_wrong_old_password(client_user):
    response = await client_user.put(
        "/users/me/update",
        json={
            "email": "newmail@example.com",
            "old_password": "wrong_old_pass",
            "new_password": "newpass123#",
            "confirm_password": "newpass123#",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] in [
        "Old password required to change email",
        "Old password is incorrect",
    ]


@pytest.mark.asyncio
async def test_update_my_profile_passwords_do_not_match(client_user):
    response = await client_user.put(
        "/users/me/update",
        json={
            "old_password": "client123#",
            "new_password": "newpass123#",
            "confirm_password": "different123#",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("Passwords do not match" in err.get("msg", "") for err in errors)


@pytest.mark.asyncio
async def test_update_email_without_old_password(client_user):
    response = await client_user.put(
        "/users/me/update",
        json={"email": "trychange@example.com"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Old password required to change email"


@pytest.mark.asyncio
async def test_update_user_email_already_exists(client_user):
    response = await client_user.put(
        "/users/me/update", json={"email": "admin@example.com"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "email" in data["detail"].lower()


@pytest.mark.asyncio
@patch("app.services.user_service.is_reset_request_allowed", new_callable=AsyncMock)
@patch("app.services.user_service.get_user_by_email", new_callable=AsyncMock)
@patch("app.services.user_service.set_token", new_callable=AsyncMock)
@patch("app.services.user_service.send_notification_email", new_callable=AsyncMock)
async def test_request_password_reset_route_success(
    mock_send_notification_email,
    mock_set_token,
    mock_get_user_by_email,
    mock_is_reset_request_allowed,
    client,
):
    mock_get_user_by_email.return_value = AsyncMock(id=1, username="testuser")
    mock_is_reset_request_allowed.return_value = True

    response = await client.post(
        "/users/request-password-reset", json={"email": "test@example.com"}
    )
    assert response.status_code == 200
    assert "If the email exists" in response.json().get("message", "")

    mock_set_token.assert_called_once()
    mock_send_notification_email.assert_called_once()
    mock_get_user_by_email.assert_called_once()
    mock_is_reset_request_allowed.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.user_service.is_reset_request_allowed", new_callable=AsyncMock)
@patch("app.services.user_service.get_user_by_email", new_callable=AsyncMock)
async def test_request_password_reset_route_rate_limited(
    mock_get_user_by_email,
    mock_is_reset_request_allowed,
    client,
):
    mock_is_reset_request_allowed.return_value = False
    mock_get_user_by_email.return_value = AsyncMock(id=1, username="testuser")

    response = await client.post(
        "/users/request-password-reset", json={"email": "test@example.com"}
    )
    assert response.status_code == 429
    assert "once per minute" in response.json().get("detail", "")

    mock_is_reset_request_allowed.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
@patch("app.services.user_service.get_user_by_email", new_callable=AsyncMock)
@patch("app.services.user_service.delete_token", new_callable=AsyncMock)
async def test_reset_password_route_success(
    mock_delete_token,
    mock_get_user_by_email,
    mock_get_email_by_token,
    client,
    db_session_with_rollback,
):
    mock_get_email_by_token.return_value = "test@example.com"
    mock_get_user_by_email.return_value = AsyncMock(
        id=1, hashed_password="hashed", username="testuser"
    )
    db_session_with_rollback.commit = AsyncMock()

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "validtoken",
            "new_password": "Newpass1#",
            "confirm_password": "Newpass1#",
        },
    )

    assert response.status_code == 200
    assert response.json().get("message") == "Password reset successful"

    mock_get_email_by_token.assert_called_once()
    mock_get_user_by_email.assert_called_once()
    mock_delete_token.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
async def test_reset_password_route_password_too_short(mock_get_email_by_token, client):
    mock_get_email_by_token.return_value = "test@example.com"

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "validtoken",
            "new_password": "A1#",
            "confirm_password": "A1#",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("at least 6 characters" in err.get("msg", "") for err in errors)


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
async def test_reset_password_route_password_no_digit(mock_get_email_by_token, client):
    mock_get_email_by_token.return_value = "test@example.com"

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "validtoken",
            "new_password": "Password#!",
            "confirm_password": "Password#!",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("at least one digit" in err.get("msg", "") for err in errors)


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
async def test_reset_password_route_password_no_letter(mock_get_email_by_token, client):
    mock_get_email_by_token.return_value = "test@example.com"

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "validtoken",
            "new_password": "1234567#",
            "confirm_password": "1234567#",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("at least one letter" in err.get("msg", "") for err in errors)


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
async def test_reset_password_route_password_no_special_char(
    mock_get_email_by_token, client
):
    mock_get_email_by_token.return_value = "test@example.com"

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "validtoken",
            "new_password": "Password1",
            "confirm_password": "Password1",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("at least one special character" in err.get("msg", "") for err in errors)


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
async def test_reset_password_route_passwords_do_not_match(
    mock_get_email_by_token, client
):
    mock_get_email_by_token.return_value = "test@example.com"

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "validtoken",
            "new_password": "Password1#",
            "confirm_password": "Password2#",
        },
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("Passwords do not match" in err.get("msg", "") for err in errors)


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
async def test_reset_password_route_invalid_token(
    mock_get_email_by_token,
    client,
):
    mock_get_email_by_token.return_value = None

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "badtoken",
            "new_password": "Newpass1#",
            "confirm_password": "Newpass1#",
        },
    )

    assert response.status_code == 400
    assert "Invalid or expired reset code" in response.json().get("detail", "")

    mock_get_email_by_token.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.user_service.get_email_by_token", new_callable=AsyncMock)
@patch("app.services.user_service.get_user_by_email", new_callable=AsyncMock)
async def test_reset_password_route_user_not_found(
    mock_get_user_by_email,
    mock_get_email_by_token,
    client,
):
    mock_get_email_by_token.return_value = "test@example.com"
    mock_get_user_by_email.return_value = None

    response = await client.post(
        "/users/reset-password",
        json={
            "token": "validtoken",
            "new_password": "Newpass1#",
            "confirm_password": "Newpass1#",
        },
    )

    assert response.status_code == 400
    assert "User not found" in response.json().get("detail", "")

    mock_get_email_by_token.assert_called_once()
    mock_get_user_by_email.assert_called_once()
