from app.core.hash import get_password_hash, verify_password


def test_password_hash_and_verify_match():
    plain = "secret123"
    hashed = get_password_hash(plain)
    assert verify_password(plain, hashed) is True


def test_password_hash_and_verify_fail_on_wrong_password():
    plain = "secret123"
    hashed = get_password_hash(plain)
    assert verify_password("wrongpass", hashed) is False
