from datetime import timedelta

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from jose import jwt


def test_create_access_token_encodes_expected_payload():
    data = {"id": 1, "role": "user"}
    token = create_access_token(data)
    assert isinstance(token, str)

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["id"] == 1
    assert decoded["role"] == "user"
    assert "exp" in decoded


def test_decode_access_token_returns_payload():
    data = {"id": 42, "role": "admin"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["id"] == 42
    assert payload["role"] == "admin"


def test_decode_access_token_returns_none_on_invalid_token():
    invalid_token = "this.is.not.valid"
    payload = decode_access_token(invalid_token)
    assert payload is None


def test_create_refresh_token_encodes_expected_payload():
    data = {"id": 5, "role": "client"}
    token = create_refresh_token(data)
    assert isinstance(token, str)

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["id"] == 5
    assert decoded["role"] == "client"
    assert "exp" in decoded


def test_decode_refresh_token_returns_payload():
    data = {"id": 123, "role": "superadmin"}
    token = create_refresh_token(data)
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload["id"] == 123
    assert payload["role"] == "superadmin"


def test_decode_refresh_token_returns_none_on_invalid_token():
    invalid_token = "completely.broken.token"
    payload = decode_refresh_token(invalid_token)
    assert payload is None


def test_refresh_token_expires_correctly():
    data = {"id": 99, "role": "tester"}
    token = create_refresh_token(data, expires_delta=timedelta(seconds=1))
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert "exp" in decoded
