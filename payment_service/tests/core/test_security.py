import pytest
from app.core.config import settings
from app.core.security import decode_access_token
from jose import jwt


@pytest.fixture
def valid_token():
    payload = {"sub": "user123", "role": "admin"}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def test_decode_access_token_valid(valid_token):
    result = decode_access_token(valid_token)
    assert result is not None
    assert result.get("sub") == "user123"
    assert result.get("role") == "admin"


def test_decode_access_token_invalid():
    fake_token = "this.is.not.a.valid.token"
    result = decode_access_token(fake_token)
    assert result is None


def test_decode_access_token_expired():
    payload = {"sub": "user123", "exp": 1}
    expired_token = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    result = decode_access_token(expired_token)
    assert result is None
