import logging
from typing import Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import (
    add_to_cart,
    delete_cart_item,
    get_cart_items,
    update_cart_quantity,
)
from keyboards.inline import get_cart_keyboard

router = Router()
logger = logging.getLogger(__name__)


async def render_cart(
        session: AsyncSession, user_id: int
) -> Tuple[str, InlineKeyboardMarkup | None]:
    """
    Формирует и отображает содержимое корзины и клавиатуру для пользователя.

    :param session: Асинхронная сессия базы данных.
    :param user_id: ID пользователя.
    :return: Кортеж с текстом корзины и соответствующей клавиатурой (или None, если корзина пуста).
    """
    cart_items = await get_cart_items(session, user_id)

    if not cart_items:
        return "Ваша корзина пуста.", None

    total_cost = 0
    cart_text = "<b>Ваша корзина:</b>\n\n"
    for item in cart_items:
        item_cost = item.product.price * item.quantity
        cart_text += f"▪️ {item.product.name}\n"
        cart_text += f"   - Цена: {item_cost} руб.\n\n"
        total_cost += item_cost

    cart_text += f"<b>Итого:</b> {total_cost} руб."
    keyboard = get_cart_keyboard(cart_items)
    return cart_text, keyboard


@router.message(F.text == "Корзина")
async def cart_handler(message: Message, session: AsyncSession) -> None:
    """
    Обрабатывает нажатие кнопки 'Корзина'.

    Отображает текущую корзину пользователя.
    """
    try:
        cart_text, keyboard = await render_cart(session, message.from_user.id)
        await message.answer(cart_text, reply_markup=keyboard)
    except Exception as e:
        logger.error("Ошибка в cart_handler для пользователя %d: %s", message.from_user.id, e)
        await message.answer("Не удалось отобразить корзину. Попробуйте снова позже.")


@router.callback_query(F.data.startswith("cart_add_"))
async def add_to_cart_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Обрабатывает добавление товара в корзину.
    """
    try:
        product_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        logger.info("Пользователь %d добавляет товар %d в корзину", user_id, product_id)

        await add_to_cart(session, user_id, product_id)
        await callback.answer("Товар добавлен в корзину!")

        cart_text, keyboard = await render_cart(session, user_id)
        await callback.message.answer(cart_text, reply_markup=keyboard)
    except (IndexError, ValueError) as e:
        logger.warning(
            "Неверные callback-данные для add_to_cart: %s. Ошибка: %s",
            callback.data,
            e,
        )
        await callback.answer("Произошла ошибка при добавлении товара.", show_alert=True)
    except Exception as e:
        logger.error(
            "Ошибка в add_to_cart_handler для пользователя %d: %s",
            callback.from_user.id,
            e,
        )
        await callback.answer(
            "Не удалось добавить товар в корзину. Попробуйте снова.", show_alert=True
        )


@router.callback_query(F.data.startswith("cart_"))
async def cart_action_handler(
        callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """
    Обрабатывает действия с товарами в корзине (увеличение, уменьшение, удаление).
    """
    current_state = await state.get_state()
    if current_state is not None:
        await callback.answer("Пожалуйста, завершите оформление заказа.", show_alert=True)
        return

    try:
        _, action, item_id_str = callback.data.split("_")
        item_id = int(item_id_str)

        if action == "del":
            await delete_cart_item(session, item_id)
        elif action in ["incr", "decr"]:
            await update_cart_quantity(session, item_id, action)

        cart_text, keyboard = await render_cart(session, callback.from_user.id)
        await callback.message.edit_text(cart_text, reply_markup=keyboard)
    except (IndexError, ValueError) as e:
        logger.warning(
            "Неверные callback-данные для cart_action: %s. Ошибка: %s",
            callback.data,
            e,
        )
        await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error(
            "Ошибка в cart_action_handler для пользователя %d: %s",
            callback.from_user.id,
            e,
        )
        await callback.answer("Не удалось обновить корзину. Попробуйте снова.", show_alert=True)
    finally:
        await callback.answer()
