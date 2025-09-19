from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=True)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def create_tables() -> None:
    """
    Создает все таблицы в базе данных на основе моделей.

    Эта функция обычно вызывается один раз при запуске приложения.
    Теперь управляется Alembic и может быть устаревшей или использоваться для первоначальных настроек.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
