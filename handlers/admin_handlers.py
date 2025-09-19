import logging

from aiogram import F, Router
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from FSM.add_product import AddCategoryStates, AddProductStates
from config import settings
from database.requests import (
    add_category,
    add_product,
    delete_category,
    get_categories,
    get_order_details,
    get_orders,
    update_order_status,
)
from keyboards.inline import (
    get_category_delete_keyboard,
    get_category_keyboard,
    get_category_management_keyboard,
    get_orders_keyboard,
    get_status_keyboard,
)
from keyboards.reply import get_admin_keyboard

router = Router()
logger = logging.getLogger(__name__)


class IsAdmin(Filter):
    """Кастомный фильтр для проверки, является ли пользователь администратором."""

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel_handler(message: Message) -> None:
    """
    Обрабатывает команду /admin.

    Отображает клавиатуру админ-панели для администраторов
    или сообщение об отказе в доступе для остальных.
    """
    if message.from_user.id in settings.ADMIN_IDS:
        logger.info("Администратор %d получил доступ к админ-панели", message.from_user.id)
        await message.answer("Добро пожаловать в админ-панель!", reply_markup=get_admin_keyboard())
    else:
        logger.warning("Пользователь %d попытался получить доступ к админ-панели", message.from_user.id)
        await message.answer("У вас нет доступа к админ-панели.")


@router.message(F.text == "Добавить товар", IsAdmin())
async def start_add_product_handler(message: Message, state: FSMContext) -> None:
    """
    Запускает FSM для добавления нового товара.
    """
    await state.set_state(AddProductStates.enter_name)
    await message.answer("Введите название нового товара:")


@router.message(F.text == "Список заказов", IsAdmin())
async def list_orders_handler(message: Message, session: AsyncSession) -> None:
    """
    Отображает список всех заказов.
    """
    try:
        orders = await get_orders(session)
        if not orders:
            await message.answer("На данный момент заказов нет.")
            return

        keyboard = get_orders_keyboard(orders)
        await message.answer("Список заказов:", reply_markup=keyboard)
    except Exception as e:
        logger.error("Ошибка в list_orders_handler для администратора %d: %s", message.from_user.id, e)
        await message.answer("Не удалось загрузить список заказов.")


@router.callback_query(F.data == "to_orders")
async def to_orders_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Обрабатывает нажатие кнопки 'Назад к заказам'.
    """
    try:
        orders = await get_orders(session)
        if not orders:
            await callback.message.edit_text("На данный момент заказов нет.")
            return

        keyboard = get_orders_keyboard(orders)
        await callback.message.edit_text("Список заказов:", reply_markup=keyboard)
    except Exception as e:
        logger.error("Ошибка в to_orders_handler для администратора %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось загрузить список заказов.", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("admin_order_"))
async def view_order_details_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Отображает детали конкретного заказа.
    """
    try:
        order_id = int(callback.data.split("_")[2])

        order = await get_order_details(session, order_id)
        if not order:
            await callback.answer("Заказ не найден.", show_alert=True)
            return

        details_text = (
            f"<b>Детали заказа №{order.id}</b>\n\n"
            f"<b>Статус:</b> {order.status}\n"
            f"<b>Имя клиента:</b> {order.name}\n"
            f"<b>Телефон:</b> {order.phone}\n"
            f"<b>Адрес:</b> {order.address}\n\n"
            f"<b>Состав заказа:</b>\n"
        )
        for item in order.items:
            details_text += f"- {item.product.name} (x{item.quantity}) - {item.price * item.quantity} руб.\n"
        details_text += f"\n<b>Итоговая стоимость:</b> {order.total_cost} руб."

        keyboard = get_status_keyboard(order_id)
        await callback.message.answer(details_text, reply_markup=keyboard)
    except (IndexError, ValueError) as e:
        logger.warning("Неверные callback-данные для view_order_details: %s. Ошибка: %s", callback.data, e)
        await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error("Ошибка в view_order_details_handler для администратора %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось загрузить детали заказа.", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("status_"))
async def change_order_status_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Изменяет статус заказа.
    """
    try:
        _, order_id_str, new_status = callback.data.split("_")
        order_id = int(order_id_str)
        logger.info("Администратор %d изменил статус заказа %d на '%s'", callback.from_user.id, order_id, new_status)

        await update_order_status(session, order_id, new_status)
        await callback.answer(f"Статус заказа №{order_id} изменен на '{new_status}'.")

        order = await get_order_details(session, order_id)
        if order:
            details_text = (
                f"<b>Детали заказа №{order.id}</b>\n\n"
                f"<b>Статус:</b> {order.status}\n"
                f"<b>Имя клиента:</b> {order.name}\n"
                f"<b>Телефон:</b> {order.phone}\n"
                f"<b>Адрес:</b> {order.address}\n\n"
                f"<b>Состав заказа:</b>\n"
            )
            for item in order.items:
                details_text += f"- {item.product.name} (x{item.quantity}) - {item.price * item.quantity} руб.\n"
            details_text += f"\n<b>Итоговая стоимость:</b> {order.total_cost} руб."

            keyboard = get_status_keyboard(order_id)
            await callback.message.edit_text(details_text, reply_markup=keyboard)
    except (IndexError, ValueError) as e:
        logger.warning("Неверные callback-данные для change_order_status: %s. Ошибка: %s", callback.data, e)
        await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error("Ошибка в change_order_status_handler для администратора %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось изменить статус заказа.", show_alert=True)


@router.message(AddProductStates.enter_name)
async def enter_product_name_handler(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод названия товара."""
    await state.update_data(name=message.text)
    await state.set_state(AddProductStates.enter_description)
    await message.answer("Теперь введите описание товара:")


@router.message(AddProductStates.enter_description)
async def enter_product_description_handler(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод описания товара."""
    await state.update_data(description=message.text)
    await state.set_state(AddProductStates.enter_price)
    await message.answer("Введите цену товара (в рублях, можно с копейками):")


@router.message(AddProductStates.enter_price)
async def enter_product_price_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Обрабатывает ввод цены товара."""
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AddProductStates.select_category)

        categories = await get_categories(session)
        keyboard = get_category_keyboard(categories, admin_mode=True)
        await message.answer("Теперь выберите категорию для товара:", reply_markup=keyboard)
    except ValueError:
        logger.warning("Администратор %d ввел неверную цену: %s", message.from_user.id, message.text)
        await message.answer("Неверный формат цены. Пожалуйста, введите число.")
    except Exception as e:
        logger.error("Ошибка в enter_product_price_handler для администратора %d: %s", message.from_user.id, e)
        await message.answer("Произошла ошибка. Попробуйте снова.")


@router.callback_query(AddProductStates.select_category, F.data.startswith("admin_category_"))
async def select_product_category_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Обрабатывает выбор категории и завершает добавление товара."""
    try:
        category_id = int(callback.data.split("_")[2])
        await state.update_data(category_id=category_id)

        data = await state.get_data()
        await add_product(session, data)
        await callback.message.answer("Товар успешно добавлен!")
        logger.info("Администратор %d успешно добавил новый товар: %s", callback.from_user.id, data['name'])
        await state.clear()
    except (IndexError, ValueError) as e:
        logger.warning("Неверные callback-данные для select_product_category: %s. Ошибка: %s", callback.data, e)
        await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error("Ошибка в select_product_category_handler для администратора %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось добавить товар. Попробуйте снова.", show_alert=True)
    finally:
        await callback.answer()


@router.message(F.text == "Управление категориями", IsAdmin())
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


@router.message(AddCategoryStates.enter_name, IsAdmin())
async def enter_category_name_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Обрабатывает ввод названия новой категории и сохраняет ее.
    """
    try:
        new_category = await add_category(session, message.text)
        await message.answer(f"Категория «{new_category.name}» успешно добавлена!")
        await state.clear()
        await manage_categories_handler(message, session)
    except IntegrityError:
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

        await manage_categories_handler(callback, session)
    except (IndexError, ValueError):
        await callback.answer("Ошибка! Неверный ID категории.", show_alert=True)
    except Exception as e:
        logger.error("Ошибка при удалении категории: %s", e)
        await callback.answer("Произошла ошибка при удалении.", show_alert=True)
