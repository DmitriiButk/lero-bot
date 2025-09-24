from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.

    Атрибуты:
        BOT_TOKEN: Токен для телеграм-бота.
        DB_HOST: Хост базы данных.
        DB_PORT: Порт базы данных.
        DB_USER: Пользователь базы данных.
        DB_PASS: Пароль пользователя базы данных.
        DB_NAME: Название базы данных.
    """

    BOT_TOKEN: str

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
