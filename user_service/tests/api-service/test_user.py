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
