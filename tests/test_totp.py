import pyotp

from app.services.totp_service import TOTPService


class TestTOTPService:
    def test_generate_secret(self):
        """Test TOTP secret generation"""
        secret = TOTPService.generate_secret()
        assert secret is not None
        assert len(secret) >= 16
        assert secret.isalnum()  # Base32 only contains alphanumeric

    def test_generate_qr_code(self):
        """Test QR code generation"""
        secret = TOTPService.generate_secret()
        qr_base64 = TOTPService.generate_qr_code(secret, "test@example.com")
        assert qr_base64 is not None
        assert isinstance(qr_base64, str)
        assert len(qr_base64) > 100  # QR code should be substantial

    def test_verify_correct_code(self):
        """Test verification of correct TOTP code"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert TOTPService.verify_code(secret, code) is True

    def test_verify_incorrect_code(self):
        """Test verification of incorrect TOTP code"""
        secret = pyotp.random_base32()
        assert TOTPService.verify_code(secret, "000000") is False

    def test_verify_expired_code(self):
        """Test verification of expired code (using window=1)"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        # Generate a code that will be invalid after time passes
        # This is a simplified test
        code = totp.at(0)  # Very old code
        # Should be invalid
        assert TOTPService.verify_code(secret, code) is False

    def test_generate_backup_codes(self):
        """Test backup code generation"""
        codes = TOTPService.generate_backup_codes(5)
        assert len(codes) == 5
        for plain, hashed in codes:
            assert len(plain) == 8  # 8 characters from token_hex(4)
            assert plain.isalnum()
            assert plain.isupper()
            assert hashed.startswith("$argon2")  # Argon2 hash

    def test_verify_backup_code(self):
        """Test backup code verification"""
        plain_code, hashed_code = TOTPService.generate_backup_codes(1)[0]
        assert TOTPService.verify_backup_code(plain_code, hashed_code) is True
        assert TOTPService.verify_backup_code("wrong", hashed_code) is False
