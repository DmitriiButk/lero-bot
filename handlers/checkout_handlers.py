import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from FSM.checkout import CheckoutStates
from database.requests import create_order, get_cart_items

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "order_create")
async def start_checkout_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """
    Запускает процесс оформления заказа.

    Проверяет, не пуста ли корзина, и устанавливает первое состояние для ввода имени.
    """
    try:
        cart_items = await get_cart_items(session, callback.from_user.id)
        if not cart_items:
            await callback.answer("Ваша корзина пуста, нечего оформлять.", show_alert=True)
            return

        await state.set_state(CheckoutStates.enter_name)
        await callback.message.answer("Для оформления заказа, пожалуйста, введите ваше имя:")
    except Exception as e:
        logger.error("Ошибка в start_checkout_handler для пользователя %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось начать оформление заказа. Попробуйте снова.", show_alert=True)
    finally:
        await callback.answer()


@router.message(CheckoutStates.enter_name)
async def enter_name_handler(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод имени пользователя.
    """
    await state.update_data(name=message.text)
    await state.set_state(CheckoutStates.enter_phone)
    await message.answer("Отлично! Теперь введите ваш номер телефона:")


@router.message(CheckoutStates.enter_phone)
async def enter_phone_handler(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод номера телефона пользователя.
    """
    await state.update_data(phone=message.text)
    await state.set_state(CheckoutStates.enter_address)
    await message.answer("И последний шаг! Введите ваш адрес доставки:")


@router.message(CheckoutStates.enter_address)
async def enter_address_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Обрабатывает ввод адреса и завершает оформление заказа.
    """
    try:
        await state.update_data(address=message.text)
        user_data = await state.get_data()

        order = await create_order(session, message.from_user.id, user_data)

        await message.answer(
            f"Спасибо за заказ! Ваш заказ <b>№{order.id}</b> успешно оформлен.\n"
            f"Мы скоро с вами свяжемся."
        )
        logger.info("Пользователь %d успешно создал заказ %d", message.from_user.id, order.id)
        await state.clear()
    except Exception as e:
        logger.error("Ошибка в enter_address_handler для пользователя %d: %s", message.from_user.id, e)
        await message.answer("Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте снова.")
