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


_bootstrap_test_env()
