from app.auth import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("demo123")
    assert hashed != "demo123"
    assert verify_password("demo123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    token = create_access_token(1, "student1", "student")
    payload = decode_access_token(token)
    assert payload["sub"] == "1"
    assert payload["username"] == "student1"
    assert payload["role"] == "student"
