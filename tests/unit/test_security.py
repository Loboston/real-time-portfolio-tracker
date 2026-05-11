import pytest

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mysecretpassword")
        assert hashed != "mysecretpassword"

    def test_correct_password_verifies(self):
        hashed = hash_password("mysecretpassword")
        assert verify_password("mysecretpassword", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("mysecretpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_produces_different_hashes(self):
        hash1 = hash_password("mysecretpassword")
        hash2 = hash_password("mysecretpassword")
        assert hash1 != hash2


class TestJWT:
    def test_encode_and_decode(self):
        token = create_access_token("user-123")
        user_id = decode_access_token(token)
        assert user_id == "user-123"

    def test_invalid_token_returns_none(self):
        assert decode_access_token("not.a.valid.token") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token("user-123")
        tampered = token + "tampered"
        assert decode_access_token(tampered) is None

    def test_empty_token_returns_none(self):
        assert decode_access_token("") is None
