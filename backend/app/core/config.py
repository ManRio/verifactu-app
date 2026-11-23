from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    postgres_db: str = Field(validation_alias="POSTGRES_DB")
    postgres_user: str = Field(validation_alias="POSTGRES_USER")
    postgres_password: str = Field(validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(
        default="localhost",
        validation_alias="POSTGRES_HOST",
    )
    postgres_port: int = Field(
        default=5432,
        validation_alias="POSTGRES_PORT",
    )

    jwt_secret_key: str = Field(
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    app_environment: str = Field(default="development", validation_alias="APP_ENVIRONMENT")
    frontend_base_url: str = Field(default="http://localhost:5173", validation_alias="FRONTEND_BASE_URL")
    email_backend: str = Field(default="console", validation_alias="EMAIL_BACKEND")
    smtp_host: str = Field(default="", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_from: str = Field(default="", validation_alias="SMTP_FROM")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    smtp_ssl: bool = Field(default=False, validation_alias="SMTP_SSL")
    smtp_starttls: bool = Field(default=True, validation_alias="SMTP_STARTTLS")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()