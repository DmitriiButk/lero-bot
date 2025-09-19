import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import get_categories, get_product, get_products_by_category
from keyboards.inline import (
    get_category_keyboard,
    get_product_card_keyboard,
    get_products_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Каталог")
async def catalog_handler(message: Message, session: AsyncSession) -> None:
    """
    Обрабатывает нажатие кнопки 'Каталог'.

    Запрашивает все категории и отображает их в виде инлайн-клавиатуры.
    """
    try:
        categories = await get_categories(session)
        if not categories:
            await message.answer("К сожалению, в данный момент нет доступных категорий.")
            return

        keyboard = get_category_keyboard(categories)
        await message.answer("Выберите категорию:", reply_markup=keyboard)
    except Exception as e:
        logger.error("Ошибка в catalog_handler для пользователя %d: %s", message.from_user.id, e)
        await message.answer("Не удалось загрузить каталог. Попробуйте снова позже.")


@router.callback_query(F.data == "to_catalog")
async def to_catalog_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Обрабатывает нажатие кнопки 'Назад к категориям'.

    Редактирует текущее сообщение, чтобы отобразить список категорий.
    """
    try:
        categories = await get_categories(session)
        if not categories:
            await callback.message.edit_text("К сожалению, в данный момент нет доступных категорий.")
            await callback.answer()
            return

        keyboard = get_category_keyboard(categories)
        await callback.message.edit_text("Выберите категорию:", reply_markup=keyboard)
    except Exception as e:
        logger.error("Ошибка в to_catalog_handler для пользователя %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось загрузить каталог. Попробуйте снова позже.", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def category_select_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Обрабатывает выбор категории.

    Запрашивает товары для выбранной категории и отображает их.
    """
    try:
        category_id = int(callback.data.split("_")[1])

        products = await get_products_by_category(session, category_id)
        if not products:
            await callback.answer("В этой категории пока нет товаров.", show_alert=True)
            return

        keyboard = get_products_keyboard(products)
        await callback.message.edit_text("Выберите товар:", reply_markup=keyboard)
    except (IndexError, ValueError) as e:
        logger.warning("Неверные callback-данные: %s. Ошибка: %s", callback.data, e)
        await callback.answer("Произошла ошибка. Попробуйте снова.", show_alert=True)
    except Exception as e:
        logger.error("Ошибка в category_select_handler для пользователя %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось загрузить товары. Попробуйте снова позже.", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def product_select_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Обрабатывает выбор товара.

    Запрашивает и отображает карточку товара с деталями и кнопками действий.
    """
    try:
        product_id = int(callback.data.split("_")[1])

        product = await get_product(session, product_id)
        if not product:
            await callback.answer("Товар не найден.", show_alert=True)
            return

        caption = (
            f"<b>{product.name}</b>\n\n"
            f"{product.description}\n\n"
            f"<b>Цена:</b> {product.price} руб."
        )

        keyboard = get_product_card_keyboard(product_id=product.id, category_id=product.category_id)
        await callback.message.edit_text(caption, reply_markup=keyboard)
    except (IndexError, ValueError) as e:
        logger.warning("Неверные callback-данные: %s. Ошибка: %s", callback.data, e)
        await callback.answer("Произошла ошибка. Попробуйте снова.", show_alert=True)
    except Exception as e:
        logger.error("Ошибка в product_select_handler для пользователя %d: %s", callback.from_user.id, e)
        await callback.answer("Не удалось загрузить товар. Попробуйте снова позже.", show_alert=True)
    finally:
        await callback.answer()
