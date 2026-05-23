import pytest

from app.services.push_service import MockPushService, PushService


class TestPushService:
    @pytest.mark.asyncio
    async def test_send_push_challenge(self):
        """Test sending push challenge (mock)"""
        service = MockPushService()
        nonce = await service.send_2fa_challenge(
            fcm_token="test_token_123",
            user_id=1,
            user_email="test@example.com",
            device_name="Test Device",
        )
        assert nonce is not None
        assert isinstance(nonce, str)
        assert len(nonce) == 64  # 32 bytes = 64 hex chars

    @pytest.mark.asyncio
    async def test_send_multiple_push(self):
        """Test sending multiple push challenges"""
        service = MockPushService()
        nonce1 = await service.send_2fa_challenge(
            "token1", 1, "test1@example.com", "Device1"
        )
        nonce2 = await service.send_2fa_challenge(
            "token2", 2, "test2@example.com", "Device2"
        )
        assert nonce1 != nonce2  # Each should be unique

    def test_create_response_payload(self):
        """Test creating response payload"""
        payload = PushService.create_2fa_response_payload(
            approved=True, nonce="test_nonce"
        )
        assert payload["approved"] is True
        assert payload["nonce"] == "test_nonce"
        assert "timestamp" in payload

    def test_create_response_payload_declined(self):
        """Test creating declined response payload"""
        payload = PushService.create_2fa_response_payload(
            approved=False, nonce="test_nonce"
        )
        assert payload["approved"] is False
