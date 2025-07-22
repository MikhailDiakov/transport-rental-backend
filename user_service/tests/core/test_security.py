from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token


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
