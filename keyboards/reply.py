from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Генерирует reply-клавиатуру для админ-панели.

    :return: Сгенерированная клавиатура администратора.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Добавить товар"),
                KeyboardButton(text="Список заказов"),
            ],
            [KeyboardButton(text="Управление категориями")],
        ],
        resize_keyboard=True,
    )


def get_user_keyboard() -> ReplyKeyboardMarkup:
    """
    Генерирует основную reply-клавиатуру для обычного пользователя.

    :return: Сгенерированная клавиатура пользователя.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Каталог"), KeyboardButton(text="Корзина")]],
        resize_keyboard=True,
    )
