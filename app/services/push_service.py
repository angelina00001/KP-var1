import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional
import secrets
import json
from app.config import settings


class PushService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                cred = credentials.Certificate(settings.fcm_credentials_path)
                firebase_admin.initialize_app(cred)
                self._initialized = True
                print("FCM initialized successfully")
            except Exception as e:
                print(f"Failed to initialize FCM: {e}")
                self._initialized = False

    async def send_2fa_challenge(
        self, fcm_token: str, user_id: int, user_email: str, device_name: str
    ) -> str:
        """
        Send a 2FA challenge push notification.
        Returns a nonce that should be stored in Redis.
        """
        nonce = secrets.token_hex(32)

        message = messaging.Message(
            notification=messaging.Notification(
                title="🔐 2FA Authentication Request",
                body=f"Approve sign-in attempt to {user_email} on {device_name}",
            ),
            data={
                "type": "2fa_challenge",
                "nonce": nonce,
                "user_id": str(user_id),
                "action": "approve",
                "timestamp": str(secrets.token_hex(8)),
            },
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="2fa_channel",
                    priority="high",
                ),
            ),
            apns=messaging.APNSConfig(
                headers={"apns-priority": "10"},
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default",
                        badge=1,
                    ),
                ),
            ),
            token=fcm_token,
        )

        try:
            response = messaging.send(message)
            print(f"Push notification sent: {response}")
            return nonce
        except Exception as e:
            print(f"Failed to send push notification: {e}")
            raise

    @staticmethod
    def create_2fa_response_payload(approved: bool, nonce: str) -> dict:
        """Create the payload that the mobile app should send back"""
        return {
            "nonce": nonce,
            "approved": approved,
            "timestamp": secrets.token_hex(8),
        }


# Mock version for development (when Firebase is not configured)
class MockPushService:
    async def send_2fa_challenge(
        self, fcm_token: str, user_id: int, user_email: str, device_name: str
    ) -> str:
        nonce = secrets.token_hex(32)
        print(f"[MOCK] Push notification sent to {fcm_token}")
        print(f"[MOCK] Nonce: {nonce}")
        return nonce
