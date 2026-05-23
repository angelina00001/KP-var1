import base64
import io
import secrets
from typing import List, Tuple

import pyotp
import qrcode

from app.services.auth_service import AuthService


class TOTPService:
    @staticmethod
    def generate_secret() -> str:
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(secret: str, email: str, issuer: str = "2FA Service") -> str:
        uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)
        qr = qrcode.make(uri)
        buffered = io.BytesIO()
        qr.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        return pyotp.TOTP(secret).verify(code, valid_window=1)

    @staticmethod
    def generate_backup_codes(count: int = 5) -> List[Tuple[str, str]]:
        """Возвращает пары (открытый код, хеш) для сохранения в БД."""
        pairs: List[Tuple[str, str]] = []
        for _ in range(count):
            plain = secrets.token_hex(4).upper()
            pairs.append((plain, AuthService.get_password_hash(plain)))
        return pairs

    @staticmethod
    def verify_backup_code(plain_code: str, stored_hash: str) -> bool:
        return AuthService.verify_password(plain_code, stored_hash)
