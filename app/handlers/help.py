# Telegram Control Bot
# Copyright (C) 2025 Eklipti
#
# Этот проект — свободное программное обеспечение: вы можете
# распространять и/или изменять его на условиях
# Стандартной общественной лицензии GNU (GNU GPL)
# третьей версии, опубликованной Фондом свободного ПО.
#
# Программа распространяется в надежде, что она будет полезной,
# но БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ; даже без подразумеваемой гарантии
# ТОВАРНОГО СОСТОЯНИЯ или ПРИГОДНОСТИ ДЛЯ КОНКРЕТНОЙ ЦЕЛИ.
# Подробности см. в Стандартной общественной лицензии GNU.
#
# Вы должны были получить копию Стандартной общественной
# лицензии GNU вместе с этой программой. Если это не так,
# см. <https://www.gnu.org/licenses/>.

from aiogram.filters import Command
from aiogram.types import Message

from ..core.logging import info
from ..help_texts import COMMAND_HELP, COMMAND_CATEGORIES
from ..router import router
from .menu import create_main_menu_keyboard


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    info(f"Пользователь {message.from_user.id} ({message.from_user.username or 'без username'}) запустил бота", "help")
    welcome_text = (
        "🤖 <b>Добро пожаловать в TelegramControlBot!</b>\n\n"
        "Этот бот позволяет управлять вашим компьютером удаленно через Telegram.\n\n"
        "🔹 <b>Основные возможности:</b>\n"
        "• Запуск и остановка процессов\n"
        "• Удаленное управление (RDP, командная строка)\n"
        "• Работа с файлами и папками\n"
        "• Мониторинг системы\n"
        "• Управление мышью и клавиатурой\n\n"
        "📚 Выберите категорию из меню ниже или используйте /help для просмотра команд\n\n"
        "⚠️ <b>Внимание:</b> Используйте бота только на доверенных устройствах!\n"
        "⚖️ <b>Правовое предупреждение:</b> Бот предназначен для администрирования собственных машин. "
        "Использование без явного разрешения владельца запрещено."
    )
    keyboard = create_main_menu_keyboard(page=1)
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        cmd = args[1].lstrip("/").lower()
        matched_cmd = None
        for command in COMMAND_HELP:
            if command.startswith(cmd):
                matched_cmd = command
                break

        if matched_cmd and matched_cmd in COMMAND_HELP:
            help_data = COMMAND_HELP[matched_cmd]
            # Текст в help_texts.py уже содержит всё необходимое форматирование.
            response = help_data['detailed']
            await message.answer(response)
        else:
            await message.answer(f"❌ Команда '{cmd}' не найдена. Используйте /help для списка команд")
        return
    response = "📚 <b>Доступные команды:</b>\n\n"

    for category, commands in COMMAND_CATEGORIES.items():
        response += f"<b>🔹 {category}:</b>\n"
        for cmd in commands:
            if cmd in COMMAND_HELP:
                response += f"• /{cmd} - {COMMAND_HELP[cmd]['description']}\n"
        response += "\n"

    response += (
        "\nℹ️ Для детальной справки по команде используйте:\n"
        "<code>/help &lt;команда&gt;</code>\n\n"
        "Пример: <code>/help on</code>"
    )

    await message.answer(response)
