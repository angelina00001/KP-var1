from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import secrets

from app.database import get_db
from app.models import User, Device, BackupCode
from app.schemas import TOTPEnableResponse, TOTPVerifyRequest, TFAVerifyRequest, LoginResponse
from app.services.totp_service import TOTPService
from app.services.auth_service import AuthService
from app.services.push_service import PushService
from app.services.totp_session import save_setup_session, pop_setup_session
from app.dependencies import get_current_user, get_redis

router = APIRouter()
push_service = PushService()


@router.post("/enable-totp", response_model=TOTPEnableResponse)
async def enable_totp(
    device_name: str,
    current_user: User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    """Шаг 1: создаём секрет и QR-код для нового устройства"""
    secret = TOTPService.generate_secret()
    qr = TOTPService.generate_qr_code(secret, current_user.email)
    await save_setup_session(redis_client, current_user.id, device_name, secret)
    return TOTPEnableResponse(secret=secret, qr_code_base64=qr)


@router.post("/verify-totp")
async def verify_totp(
    req: TOTPVerifyRequest,
    device_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """Шаг 2: проверяем код и сохраняем устройство в БД"""
    secret = await pop_setup_session(redis_client, current_user.id, device_name)
    if not secret:
        raise HTTPException(status_code=400, detail="Сессия истекла. Нажмите 'Включить 2FA' заново.")

    if not TOTPService.verify_code(secret, req.code):
        raise HTTPException(status_code=401, detail="Неверный код")

    existing = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.device_name == device_name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Устройство '{device_name}' уже существует")

    device = Device(
        user_id=current_user.id,
        device_name=device_name,
        device_type="totp",
        totp_secret=secret,
    )
    db.add(device)
    await db.flush()

    backup_pairs = TOTPService.generate_backup_codes()
    plain_codes = []
    for plain, hashed in backup_pairs:
        db.add(BackupCode(device_id=device.id, code_hash=hashed))
        plain_codes.append(plain)

    devices_count = (
        await db.execute(select(Device).where(Device.user_id == current_user.id))
    ).scalars().all()
    if len(devices_count) == 1:
        current_user.tfa_enabled = True

    await db.commit()

    return {
        "message": f"Устройство '{device_name}' добавлено",
        "backup_codes": plain_codes,
    }


@router.post("/verify")
async def verify_2fa(
    req: TFAVerifyRequest,
    temp_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Вход с 2FA"""
    user_id = AuthService.verify_temp_2fa_token(temp_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Сессия истекла")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
    devices = (
        await db.execute(
            select(Device).where(Device.user_id == user.id, Device.is_active == True)
        )
    ).scalars().all()

    for d in devices:
        if d.totp_secret and TOTPService.verify_code(d.totp_secret, req.code):
            d.last_used_at = func.now()
            await db.commit()
            return LoginResponse(
                access_token=AuthService.create_access_token({"sub": str(user.id)}),
                refresh_token="",
                requires_2fa=False,
            )

    raise HTTPException(status_code=401, detail="Неверный код 2FA")


class PushApproveRequest(BaseModel):
    nonce: str
    approved: bool


@router.post("/push/challenge")
async def send_push_challenge(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Шаг 1: Пользователь уже ввел пароль, сервер просит подтвердить вход по push.
    Отправляем push-уведомление на телефон пользователя.
    """
    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.device_type == "push",
            Device.is_active == True,
        )
    )
    device = result.scalar_one_or_none()
    if not device or not device.fcm_token:
        raise HTTPException(status_code=400, detail="Push-устройство не найдено")

    nonce = secrets.token_hex(32)
    await redis_client.setex(f"push_challenge:{nonce}", 300, current_user.id)

    await push_service.send_2fa_challenge(
        fcm_token=device.fcm_token,
        user_id=current_user.id,
        user_email=current_user.email,
        device_name=device.device_name,
    )

    return {"status": "push_sent", "message": "Проверьте телефон", "nonce": nonce}


@router.post("/push/verify")
async def verify_push_approval(
    request: PushApproveRequest,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Шаг 2: Мобильное приложение отправляет сюда ответ пользователя (одобрил/отклонил).
    """
    user_id = await redis_client.get(f"push_challenge:{request.nonce}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Сессия подтверждения истекла или не найдена")

    if not request.approved:
        await redis_client.delete(f"push_challenge:{request.nonce}")
        raise HTTPException(status_code=403, detail="Вход отклонен пользователем")

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await redis_client.delete(f"push_challenge:{request.nonce}")

    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
