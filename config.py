from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.

    Атрибуты:
        BOT_TOKEN: Токен для телеграм-бота.
        ADMIN_IDS: Список ID администраторов в Telegram.
        DB_HOST: Хост базы данных.
        DB_PORT: Порт базы данных.
        DB_USER: Пользователь базы данных.
        DB_PASS: Пароль пользователя базы данных.
        DB_NAME: Название базы данных.
    """

    BOT_TOKEN: str
    ADMIN_IDS: list[int] = Field(default=[])

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> list[int]:
        """Парсит строку с ID администраторов, разделенную запятыми, в список чисел."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(i.strip()) for i in v.split(",")]
        if isinstance(v, int):
            return [v]
        return v

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def database_url(self) -> str:
        """Собирает асинхронный URL для подключения к базе данных из компонентов."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

