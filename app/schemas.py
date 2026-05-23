from __future__ import annotations

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str
    tfa_enabled: bool = False
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    admin_code: Optional[str] = None


class UserResponse(UserBase):
    id: int
    tfa_enabled: bool
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    id: int
    user_id: int
    device_name: str
    device_type: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class AdminDeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int


class TOTPEnableResponse(BaseModel):
    secret: str
    qr_code_base64: str
    backup_codes: List[str] = []


class TOTPVerifyRequest(BaseModel):
    code: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False
    temp_token: Optional[str] = None


class TFAVerifyRequest(BaseModel):
    code: Optional[str] = None
