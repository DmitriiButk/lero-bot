from typing import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Cart, Category, Order, OrderItem, Product


async def get_categories(session: AsyncSession) -> Sequence[Category]:
    """
    Получает все категории из базы данных.

    :param session: Асинхронная сессия базы данных.
    :return: Последовательность объектов Category.
    """
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


async def get_products_by_category(
    session: AsyncSession, category_id: int
) -> Sequence[Product]:
    """
    Получает все товары по ID категории.

    :param session: Асинхронная сессия базы данных.
    :param category_id: ID категории.
    :return: Последовательность объектов Product.
    """
    query = select(Product).where(Product.category_id == category_id)
    result = await session.execute(query)
    return result.scalars().all()


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    """
    Получает конкретный товар по его ID.

    :param session: Асинхронная сессия базы данных.
    :param product_id: ID товара.
    :return: Объект Product или None, если товар не найден.
    """
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def add_to_cart(session: AsyncSession, user_id: int, product_id: int) -> None:
    """
    Добавляет товар в корзину пользователя или увеличивает его количество.

    :param session: Асинхронная сессия базы данных.
    :param user_id: ID пользователя.
    :param product_id: ID товара.
    """
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    cart_item = await session.scalar(query)

    if cart_item:
        cart_item.quantity += 1
    else:
        session.add(Cart(user_id=user_id, product_id=product_id))

    await session.commit()


async def get_cart_items(session: AsyncSession, user_id: int) -> Sequence[Cart]:
    """
    Получает все товары в корзине пользователя.

    :param session: Асинхронная сессия базы данных.
    :param user_id: ID пользователя.
    :return: Последовательность объектов Cart.
    """
    query = select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


async def update_cart_quantity(session: AsyncSession, cart_id: int, action: str) -> bool:
    """
    Обновляет количество товара в корзине (увеличивает, уменьшает или удаляет).

    :param session: Асинхронная сессия базы данных.
    :param cart_id: ID записи в корзине.
    :param action: Действие ('incr' или 'decr').
    :return: True, если операция прошла успешно, иначе False.
    """
    query = select(Cart).where(Cart.id == cart_id)
    cart_item = await session.scalar(query)

    if not cart_item:
        return False

    if action == "incr":
        cart_item.quantity += 1
    elif action == "decr":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            await session.delete(cart_item)

    await session.commit()
    return True


async def delete_cart_item(session: AsyncSession, cart_id: int) -> None:
    """
    Удаляет товар из корзины по ID записи в корзине.

    :param session: Асинхронная сессия базы данных.
    :param cart_id: ID записи в корзине.
    """
    query = delete(Cart).where(Cart.id == cart_id)
    await session.execute(query)
    await session.commit()


async def create_order(session: AsyncSession, user_id: int, user_data: dict) -> Order:
    """
    Создает новый заказ, переносит в него товары из корзины и очищает корзину.

    :param session: Асинхронная сессия базы данных.
    :param user_id: ID пользователя.
    :param user_data: Данные пользователя (имя, телефон, адрес).
    :return: Новый созданный объект Order.
    """
    cart_items = await get_cart_items(session, user_id)
    total_cost = sum(item.product.price * item.quantity for item in cart_items)

    new_order = Order(
        user_id=user_id,
        name=user_data["name"],
        phone=user_data["phone"],
        address=user_data["address"],
        total_cost=total_cost,
    )
    session.add(new_order)
    await session.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price,
        )
        session.add(order_item)
        await session.delete(item)

    await session.commit()
    await session.refresh(new_order)
    return new_order


async def add_product(session: AsyncSession, data: dict) -> None:
    """
    Добавляет новый товар в базу данных.

    :param session: Асинхронная сессия базы данных.
    :param data: Данные товара (название, описание, цена, ID категории).
    """
    product = Product(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        category_id=data["category_id"],
    )
    session.add(product)
    await session.commit()


async def get_orders(session: AsyncSession, status: str | None = None) -> Sequence[Order]:
    """
    Получает список заказов, опционально фильтруя по статусу.

    :param session: Асинхронная сессия базы данных.
    :param status: Статус для фильтрации (опционально).
    :return: Последовательность объектов Order.
    """
    if status:
        query = select(Order).where(Order.status == status).order_by(Order.created_at.desc())
    else:
        query = select(Order).order_by(Order.created_at.desc())

    result = await session.execute(query)
    return result.unique().scalars().all()


async def get_order_details(session: AsyncSession, order_id: int) -> Order | None:
    """
    Получает детали конкретного заказа со всеми товарами.

    :param session: Асинхронная сессия базы данных.
    :param order_id: ID заказа.
    :return: Объект Order или None, если заказ не найден.
    """
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_order_status(session: AsyncSession, order_id: int, status: str) -> None:
    """
    Обновляет статус заказа по его ID.

    :param session: Асинхронная сессия базы данных.
    :param order_id: ID заказа.
    :param status: Новый статус.
    """
    query = update(Order).where(Order.id == order_id).values(status=status)
    await session.execute(query)
    await session.commit()


async def add_category(session: AsyncSession, name: str) -> Category:
    """
    Добавляет новую категорию в базу данных.

    :param session: Асинхронная сессия базы данных.
    :param name: Название новой категории.
    :return: Созданный объект Category.
    """
    new_category = Category(name=name)
    session.add(new_category)
    await session.commit()
    await session.refresh(new_category)
    return new_category


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """
    Удаляет категорию, если в ней нет товаров.

    :param session: Асинхронная сессия базы данных.
    :param category_id: ID удаляемой категории.
    :return: True, если категория удалена, иначе False.
    """
    products_in_category = await get_products_by_category(session, category_id)
    if products_in_category:
        return False

    query = delete(Category).where(Category.id == category_id)
    await session.execute(query)
    await session.commit()
    return True
