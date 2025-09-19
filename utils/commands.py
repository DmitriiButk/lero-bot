from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot):
    """
    Устанавливает команды для бота в меню Telegram.
    """

    bot_commands = [
        BotCommand(command="start", description="🚀 Перезапустить бота"),
        BotCommand(command="admin", description="⚙️ Админ-панель"),
    ]

    await bot.set_my_commands(commands=bot_commands, scope=BotCommandScopeDefault())
