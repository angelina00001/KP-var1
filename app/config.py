from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_sync: str

    # Redis
    redis_url: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Firebase
    fcm_credentials_path: str
    fcm_project_id: str

    # Admin
    admin_username: str = "admin"
    admin_password_hash: str

    # App
    app_name: str = "2FA Service"
    debug: bool = False

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
