import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.database import async_session_factory
from handlers import (
    admin_handlers,
    cart_handlers,
    catalog_handlers,
    category_management_handlers,
    checkout_handlers,
    common_handlers,
)
from middlewares.db import DbSessionMiddleware
from utils.commands import set_commands


async def main() -> None:
    """
    Основная функция для запуска бота.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    storage = MemoryStorage()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_factory))

    dp.include_router(admin_handlers.router)
    dp.include_router(category_management_handlers.router)
    dp.include_router(common_handlers.router)
    dp.include_router(catalog_handlers.router)
    dp.include_router(cart_handlers.router)
    dp.include_router(checkout_handlers.router)

    await set_commands(bot)

    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен пользователем.")
