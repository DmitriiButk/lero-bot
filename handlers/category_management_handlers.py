import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from FSM.add_product import AddCategoryStates
from database.requests import add_category, delete_category, get_categories
from keyboards.inline import (
    get_category_delete_keyboard,
    get_category_management_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Управление категориями")
@router.callback_query(F.data == "manage_categories")
async def manage_categories_handler(update: Message | CallbackQuery, session: AsyncSession) -> None:
    """
    Отображает меню управления категориями.
    """
    categories = await get_categories(session)
    keyboard = get_category_management_keyboard(categories)
    text = "Категории в базе данных:" if categories else "В базе данных пока нет категорий."

    if isinstance(update, Message):
        await update.answer(text, reply_markup=keyboard)
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard)
        await update.answer()


@router.callback_query(F.data == "admin_category_add")
async def start_add_category_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Запускает FSM для добавления новой категории.
    """
    await state.set_state(AddCategoryStates.enter_name)
    await callback.message.edit_text("Введите название новой категории:")
    await callback.answer()


@router.message(AddCategoryStates.enter_name)
async def enter_category_name_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Обрабатывает ввод названия новой категории и сохраняет ее.
    """
    try:
        new_category = await add_category(session, message.text)
        await message.answer(f"Категория «{new_category.name}» успешно добавлена!")
        await state.clear()
        # Возвращаемся в меню управления категориями
        await manage_categories_handler(message, session)
    except IntegrityError:  # Обработка случая, если категория уже существует
        await message.answer("Такая категория уже существует. Пожалуйста, введите другое название.")
    except Exception as e:
        logger.error("Ошибка при добавлении категории: %s", e)
        await message.answer("Произошла ошибка при добавлении категории. Попробуйте снова.")
        await state.clear()


@router.callback_query(F.data == "admin_category_delete_menu")
async def show_delete_category_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Отображает меню для выбора категории для удаления.
    """
    categories = await get_categories(session)
    if not categories:
        await callback.answer("Нет категорий для удаления.", show_alert=True)
        return

    keyboard = get_category_delete_keyboard(categories)
    await callback.message.edit_text("Выберите категорию для удаления:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_category_del_"))
async def delete_category_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Удаляет выбранную категорию.
    """
    try:
        category_id = int(callback.data.split("_")[3])
        deleted = await delete_category(session, category_id)

        if deleted:
            await callback.answer("Категория успешно удалена.", show_alert=True)
        else:
            await callback.answer(
                "Нельзя удалить категорию, так как в ней есть товары.",
                show_alert=True,
            )

        # Обновляем меню управления
        await manage_categories_handler(callback, session)
    except (IndexError, ValueError):
        await callback.answer("Ошибка! Неверный ID категории.", show_alert=True)
    except Exception as e:
        logger.error("Ошибка при удалении категории: %s", e)
        await callback.answer("Произошла ошибка при удалении.", show_alert=True)
