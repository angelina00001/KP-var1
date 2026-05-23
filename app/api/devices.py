from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, Device
from app.schemas import DeviceResponse
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=list[DeviceResponse])
async def get_devices(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Device).where(Device.user_id == current_user.id))
    return result.scalars().all()


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.user_id == current_user.id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    await db.delete(device)
    remaining = await db.execute(
        select(Device).where(Device.user_id == current_user.id)
    )
    if not remaining.scalars().all():
        current_user.tfa_enabled = False
    await db.commit()
    return {"message": "Устройство удалено"}
