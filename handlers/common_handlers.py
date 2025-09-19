import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.reply import get_user_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Обрабатывает команду /start.

    Приветствует пользователя и отображает основную клавиатуру.
    """
    logger.info("Пользователь %d запустил бота", message.from_user.id)
    try:
        await message.answer(
            f"Привет, {message.from_user.full_name}!",
            reply_markup=get_user_keyboard()
        )
    except Exception as e:
        logger.error("Ошибка в обработчике /start для пользователя %d: %s", message.from_user.id, e)
        await message.answer("Произошла ошибка при запуске. Попробуйте снова позже.")


@router.message(F.text.in_(["Добавить товар", "Список заказов", "Управление категориями"]))
async def non_admin_access_handler(message: Message) -> None:
    """
    Обрабатывает попытку не-администратора использовать админские команды.
    """
    logger.warning("Пользователь %d попытался использовать админскую команду: %s", message.from_user.id, message.text)
    await message.answer("У вас нет доступа к этой функции.")
