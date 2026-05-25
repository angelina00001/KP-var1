"""Переменные окружения для pytest до импорта приложения."""

import json
import os
import tempfile


def _bootstrap_test_env() -> None:
    if os.environ.get("PYTEST_2FA_BOOTSTRAPPED"):
        return

    fd, fake_fcm = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(fake_fcm, "w", encoding="utf-8") as fh:
        json.dump({"type": "service_account", "project_id": "test"}, fh)

    defaults = {
        "DATABASE_URL": "postgresql+asyncpg://postgres:secret@localhost:5432/test_db",
        "DATABASE_URL_SYNC": "postgresql://postgres:secret@localhost:5432/test_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "SECRET_KEY": "test_secret_key_for_pytest_only",
        "FCM_CREDENTIALS_PATH": fake_fcm,
        "FCM_PROJECT_ID": "test",
        "ADMIN_PASSWORD_HASH": "$argon2id$v=19$m=65536,t=3,p=4$test$test",
        "APP_NAME": "2FA Service",
        "DEBUG": "false",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)

    os.environ["PYTEST_2FA_BOOTSTRAPPED"] = "1"


# Загружаем переменные ДО импортов
_bootstrap_test_env()

# Импорты с отключением проверки flake8
import pytest  # noqa: E402
from httpx import AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    database_url = os.environ.get("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
