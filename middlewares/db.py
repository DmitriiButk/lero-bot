from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для предоставления сессии базы данных в хендлеры.
    """

    def __init__(self, session_pool: async_sessionmaker):
        """
        Инициализирует middleware с пулом сессий.

        :param session_pool: Фабрика асинхронных сессий SQLAlchemy.
        """
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Выполняет middleware.

        Открывает сессию из пула, добавляет ее в данные, вызывает хендлер
        и гарантирует закрытие сессии.
        """
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)
