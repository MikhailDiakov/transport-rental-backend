import pytest
from fastapi import status

NON_SUPERADMIN_ERROR_MSG = "Access denied: only superadmins can perform this action"


@pytest.mark.asyncio
async def test_list_admins_superadmin(super_admin_client):
    response = await super_admin_client.get("/superadmin/users/admins")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert all(u["role_id"] in [1, 0] for u in data)


@pytest.mark.asyncio
async def test_list_all_users_superadmin(super_admin_client):
    response = await super_admin_client.get("/superadmin/users/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_user_by_id_superadmin(super_admin_client):
    response = await super_admin_client.get("/superadmin/users/3")
    if response.status_code == status.HTTP_404_NOT_FOUND:
        pytest.skip("User with id=1 not found in test DB")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "username" in data


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(super_admin_client):
    response = await super_admin_client.get("/superadmin/users/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "User with id=99999 not found"


@pytest.mark.asyncio
async def test_update_user_by_admin_success(super_admin_client):
    update_data = {
        "email": "newemail@example.com",
        "username": "newusername",
        "password": "newpassword123#",
        "role": 2,
    }
    response = await super_admin_client.put("/superadmin/users/2", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == update_data["email"]
    assert data["username"] == update_data["username"]
    assert data["role_id"] == update_data["role"]


@pytest.mark.asyncio
async def test_update_user_not_found(super_admin_client):
    update_data = {
        "email": "newemail@example.com",
        "username": "newusername",
        "password": "newpassword123#",
        "role": 2,
    }
    response = await super_admin_client.put("/superadmin/users/99999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_user_by_admin_cannot_edit_self(super_admin_client):
    update_data = {"email": "test@example.com"}
    response = await super_admin_client.put("/superadmin/users/1", json=update_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "You cannot edit your own account"


@pytest.mark.asyncio
async def test_update_user_by_admin_email_already_exists(super_admin_client):
    update_data = {"email": "admin@example.com"}
    response = await super_admin_client.put("/superadmin/users/3", json=update_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already in use"


@pytest.mark.asyncio
async def test_update_user_by_admin_cannot_assign_superadmin_role(super_admin_client):
    update_data = {"role": 0}
    response = await super_admin_client.put("/superadmin/users/2", json=update_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Cannot assign superadmin role"


@pytest.mark.asyncio
async def test_delete_user_success(super_admin_client):
    response = await super_admin_client.delete("/superadmin/users/3")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_user_not_found(super_admin_client):
    response = await super_admin_client.delete("/superadmin/users/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "User not found"


@pytest.mark.asyncio
async def test_delete_user_cannot_delete_self(super_admin_client):
    response = await super_admin_client.delete("/superadmin/users/1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "You cannot delete your own account"


@pytest.mark.asyncio
async def test_non_superadmins_cannot_access_superadmin_endpoints(
    admin_client, client_user, client
):
    async def check_access_denied(client):
        user_id = 2

        endpoints = [
            ("get", "/superadmin/users/admins"),
            ("get", "/superadmin/users/"),
            ("get", f"/superadmin/users/{user_id}"),
            ("put", f"/superadmin/users/{user_id}"),
            ("delete", f"/superadmin/users/{user_id}"),
        ]

        for method, url in endpoints:
            kwargs = {"json": {"email": "test@example.com"}} if method == "put" else {}
            resp = await getattr(client, method)(url, **kwargs)
            assert resp.status_code in (
                status.HTTP_403_FORBIDDEN,
                status.HTTP_401_UNAUTHORIZED,
            ), f"{method.upper()} {url} unexpected status {resp.status_code}"

    await check_access_denied(admin_client)
    await check_access_denied(client_user)
    await check_access_denied(client)
