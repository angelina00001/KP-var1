"""Временные сессии настройки TOTP в Redis (TTL 10 минут)."""

TOTP_SETUP_PREFIX = "totp_setup:"
TOTP_SETUP_TTL_SECONDS = 600


def _session_key(user_id: int, device_name: str) -> str:
    return f"{TOTP_SETUP_PREFIX}{user_id}:{device_name}"


async def save_setup_session(redis, user_id: int, device_name: str, secret: str) -> None:
    await redis.setex(_session_key(user_id, device_name), TOTP_SETUP_TTL_SECONDS, secret)


async def pop_setup_session(redis, user_id: int, device_name: str) -> str | None:
    key = _session_key(user_id, device_name)
    secret = await redis.get(key)
    if secret:
        await redis.delete(key)
    return secret
