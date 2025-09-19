from typing import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Cart, Category, Order, Product


def get_category_keyboard(categories: Sequence[Category], admin_mode: bool = False) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру со списком категорий.

    :param categories: Список объектов категорий.
    :param admin_mode: Если True, добавляет специальный префикс в callback_data для админских хендлеров.
    :return: Сгенерированная клавиатура.
    """
    builder = InlineKeyboardBuilder()
    for category in categories:
        callback_data = f"admin_category_{category.id}" if admin_mode else f"category_{category.id}"
        builder.add(InlineKeyboardButton(text=category.name, callback_data=callback_data))
    builder.adjust(2)
    return builder.as_markup()


def get_products_keyboard(products: Sequence[Product]) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру со списком товаров.

    :param products: Список объектов товаров.
    :return: Сгенерированная клавиатура.
    """
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.add(InlineKeyboardButton(text=product.name, callback_data=f"product_{product.id}"))
    builder.add(InlineKeyboardButton(text="Назад к категориям", callback_data="to_catalog"))
    builder.adjust(1)  # 1 кнопка в ряду
    return builder.as_markup()


def get_product_card_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру для карточки товара.

    :param product_id: ID товара.
    :param category_id: ID категории товара (для кнопки 'Назад').
    :return: Сгенерированная клавиатура.
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Добавить в корзину", callback_data=f"cart_add_{product_id}"))
    builder.add(InlineKeyboardButton(text="Назад к товарам", callback_data=f"category_{category_id}"))
    return builder.as_markup()


def get_cart_keyboard(cart_items: Sequence[Cart]) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру для корзины покупок.

    :param cart_items: Список объектов товаров в корзине.
    :return: Сгенерированная клавиатура.
    """
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        builder.row(
            InlineKeyboardButton(text="-", callback_data=f"cart_decr_{item.id}"),
            InlineKeyboardButton(text=f"{item.quantity} шт.", callback_data="noop"),
            InlineKeyboardButton(text="+", callback_data=f"cart_incr_{item.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"cart_del_{item.id}"),
        )
    builder.row(InlineKeyboardButton(text="Оформить заказ", callback_data="order_create"))
    builder.row(InlineKeyboardButton(text="Назад в каталог", callback_data="to_catalog"))
    return builder.as_markup()


def get_orders_keyboard(orders: Sequence[Order]) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру со списком заказов для админ-панели.

    :param orders: Список объектов заказов.
    :return: Сгенерированная клавиатура.
    """
    builder = InlineKeyboardBuilder()
    for order in orders:
        text = f"Заказ №{order.id} от {order.created_at.strftime('%d.%m.%y')} ({order.status})"
        builder.add(InlineKeyboardButton(text=text, callback_data=f"admin_order_{order.id}"))
    builder.adjust(1)
    return builder.as_markup()


def get_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру для изменения статуса заказа.

    :param order_id: ID заказа.
    :return: Сгенерированная клавиатура.
    """
    statuses = ["Принят", "В обработке", "Отправлен", "Выполнен", "Отменен"]
    builder = InlineKeyboardBuilder()
    for status in statuses:
        builder.add(InlineKeyboardButton(text=status, callback_data=f"status_{order_id}_{status}"))
    builder.add(InlineKeyboardButton(text="Назад к заказам", callback_data="to_orders"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_category_management_keyboard(categories: Sequence[Category]) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для управления категориями.

    :param categories: Список всех категорий.
    :return: Сгенерированная клавиатура.
    """
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.add(InlineKeyboardButton(text=category.name, callback_data="noop"))  # Просто для отображения
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="admin_category_add"),
        InlineKeyboardButton(text="❌ Удалить", callback_data="admin_category_delete_menu"),
    )
    return builder.as_markup()


def get_category_delete_keyboard(categories: Sequence[Category]) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для выбора категории для удаления.

    :param categories: Список всех категорий.
    :return: Сгенерированная клавиатура.
    """
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.add(InlineKeyboardButton(text=f"❌ {category.name}", callback_data=f"admin_category_del_{category.id}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="Назад", callback_data="manage_categories"))
    return builder.as_markup()
