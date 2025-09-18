# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from aiogram.filters import Command
from aiogram.types import Message

from ..help_texts import COMMAND_HELP
from ..router import router


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    welcome_text = (
        "🤖 <b>Добро пожаловать в ControlBot!</b>\n\n"
        "Этот бот позволяет управлять вашим компьютером удаленно через Telegram.\n\n"
        "🔹 <b>Основные возможности:</b>\n"
        "• Запуск и остановка процессов\n"
        "• Удаленное управление (RDP, командная строка)\n"
        "• Работа с файлами и папками\n"
        "• Мониторинг системы\n"
        "• Управление мышью и клавиатурой\n\n"
        "📚 Для просмотра всех команд используйте /help\n"
        "ℹ️ Для справки по конкретной команде: /help &lt;команда&gt;\n\n"
        "⚠️ <b>Внимание:</b> Используйте бота только на доверенных устройствах!\n"
        "⚖️ <b>Правовое предупреждение:</b> Бот предназначен для администрирования собственных машин. "
        "Использование без явного разрешения владельца запрещено."
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        cmd = args[1].lstrip('/').lower()
        matched_cmd = None
        for command in COMMAND_HELP:
            if command.startswith(cmd):
                matched_cmd = command
                break

        if matched_cmd and matched_cmd in COMMAND_HELP:
            help_data = COMMAND_HELP[matched_cmd]
            response = (
                f"🔹 <b>Команда: /{matched_cmd}</b>\n\n"
                f"ℹ️ {help_data['detailed']}"
            )
            await message.answer(response)
        else:
            await message.answer(
                f"❌ Команда '{cmd}' не найдена. Используйте /help для списка команд"
            )
        return

    response = "📚 <b>Доступные команды:</b>\n\n"
    categories = {
        "Процессы": ["on", "off", "reload", "processes"],
        "Система": ["tasklist"],
        "Пути": ["add_path", "list_paths", "del_path", "add_default_path", "list_default_paths", "del_default_path", "reload_paths"],
        "Файлы": ["upload", "download", "cut", "find"],
        "Мониторинг": ["monitor_add", "monitor_remove", "monitor_list", "monitor_stop"],
        "Командная строка": ["cmd_session_start", "cmd_session_stop", "cmd", "cmd_wait", "cmdupdate", "cmd_dump"],
        "Удаленное управление": ["rdp_start", "rdp_stop"],
        "Мышь": [
            "mouse_move",
            "mouse_move_rel",
            "mouse_save",
            "mouse_goto",
            "mouse_speed",
            "mouse_click",
            "mouse_scroll",
        ],
        "Клавиатура": ["key", "type"],
        "Экран": ["screen", "screen_find", "screen_mark"],
        "Прочее": ["start", "help", "cancel"],
    }

    for category, commands in categories.items():
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



