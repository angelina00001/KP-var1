from datetime import timedelta

from app.services.auth_service import AuthService


class TestAuthService:
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "my_secret_password123"
        hashed = AuthService.get_password_hash(password)
        assert hashed != password
        assert AuthService.verify_password(password, hashed) is True
        assert AuthService.verify_password("wrong", hashed) is False

    def test_create_access_token(self):
        """Test access token creation"""
        token = AuthService.create_access_token(data={"sub": "123"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = AuthService.create_refresh_token(data={"sub": "123"})
        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        token = AuthService.create_access_token(data={"sub": "456"})
        payload = AuthService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "456"
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        payload = AuthService.decode_token("invalid.token.here")
        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding an expired token"""
        # Create token that expires in -1 minute
        token = AuthService.create_access_token(
            data={"sub": "789"}, expires_delta=timedelta(minutes=-1)
        )
        payload = AuthService.decode_token(token)
        assert payload is None  # Should be expired

    def test_create_temp_2fa_token(self):
        """Test temporary 2FA token creation"""
        token = AuthService.create_temp_2fa_token(123)
        payload = AuthService.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["type"] == "2fa_temp"

    def test_verify_temp_2fa_token(self):
        """Test temporary 2FA token verification"""
        token = AuthService.create_temp_2fa_token(123)
        user_id = AuthService.verify_temp_2fa_token(token)
        assert user_id == 123

    def test_verify_invalid_temp_token(self):
        """Test verification of invalid temporary token"""
        user_id = AuthService.verify_temp_2fa_token("invalid")
        assert user_id is None
