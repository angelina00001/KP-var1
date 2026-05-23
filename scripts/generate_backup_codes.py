#!/usr/bin/env python3
"""
Скрипт для генерации резервных кодов для существующего пользователя.
Использование: python scripts/generate_backup_codes.py --email user@example.com
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models import User, Device, BackupCode
from app.services.totp_service import TOTPService
from sqlalchemy import select


async def generate_backup_codes_for_user(email: str):
    """Generate new backup codes for a user"""
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ User with email {email} not found")
            return

        # Find user's devices
        result = await db.execute(select(Device).where(Device.user_id == user.id))
        devices = result.scalars().all()

        if not devices:
            print(f"❌ No devices found for user {email}")
            return

        print(f"\n📱 User: {user.email} ({user.full_name})")
        print(f"🔐 2FA Enabled: {user.tfa_enabled}")
        print(f"📟 Devices found: {len(devices)}\n")

        for device in devices:
            print(f"  Device: {device.device_name} (Type: {device.device_type})")

            # Delete old unused backup codes
            result = await db.execute(
                select(BackupCode).where(
                    BackupCode.device_id == device.id,
                    BackupCode.is_used == False
                )
            )
            old_codes = result.scalars().all()
            for code in old_codes:
                await db.delete(code)

            # Generate new backup codes
            new_codes = TOTPService.generate_backup_codes(5)
            codes_display = []

            for plain_code, hashed_code in new_codes:
                backup_code = BackupCode(
                    device_id=device.id,
                    code_hash=hashed_code,
                )
                db.add(backup_code)
                codes_display.append(plain_code)

            await db.commit()

            print(f"    ✅ Generated {len(codes_display)} new backup codes:")
            for code in codes_display:
                print(f"       • {code}")

            print()

        print("⚠️  WARNING: Save these codes in a safe place! They will not be shown again.")


async def main():
    parser = argparse.ArgumentParser(description="Generate backup codes for a user")
    parser.add_argument("--email", "-e", required=True, help="User email address")
    args = parser.parse_args()

    await generate_backup_codes_for_user(args.email)


if __name__ == "__main__":
    asyncio.run(main())