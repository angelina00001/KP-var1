#!/usr/bin/env python3
"""
Скрипт для создания администратора.
Использование: python scripts/init_admin.py --email admin@example.com --password admin123
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models import User
from app.services.auth_service import AuthService
from sqlalchemy import select


async def create_admin(email: str, password: str, full_name: str = "Administrator"):
    """Create an admin user"""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"⚠️  User {email} already exists")
            return

        # Create admin user
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            tfa_enabled=False,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        print(f"✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.id}")
        print(f"\n⚠️  Note: Admin privileges are based on email whitelist.")
        print(f"   Add {email} to admin_emails list in app/api/admin.py")


async def main():
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--email", "-e", required=True, help="Admin email")
    parser.add_argument("--password", "-p", required=True, help="Admin password")
    parser.add_argument("--name", "-n", default="Administrator", help="Full name")
    args = parser.parse_args()

    await create_admin(args.email, args.password, args.name)


if __name__ == "__main__":
    asyncio.run(main())