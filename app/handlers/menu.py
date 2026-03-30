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

"""
Система inline-меню для навигации по командам бота
"""

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..core.logging import error, info, warning
from ..help_texts import COMMAND_CATEGORIES, COMMAND_HELP
from ..router import router

# Структура страниц меню
MENU_PAGES = {
    1: ["Процессы", "Пути", "Файлы", "Мониторинг"],
    2: ["Командная строка", "Удаленное управление", "Прочее"],
    3: ["Мышь", "Клавиатура", "Экран"],
}


def create_main_menu_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру главного меню для указанной страницы
    """
    if page not in MENU_PAGES:
        page = 1
    
    categories = MENU_PAGES[page]
    keyboard = []
    
    # Добавляем кнопки категорий (по 2 в ряд)
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                category = categories[i + j]
                row.append(InlineKeyboardButton(
                    text=f"📁 {category}",
                    callback_data=f"category:{category}"
                ))
        keyboard.append(row)
    
    # Добавляем навигационную кнопку
    if page == 1:
        keyboard.append([InlineKeyboardButton(
            text="➡️ Далее (1/3)",
            callback_data="menu:page:2"
        )])
    elif page == 2:
        keyboard.append([InlineKeyboardButton(
            text="➡️ Далее (2/3)",
            callback_data="menu:page:3"
        )])
    else:  # page == 3
        keyboard.append([InlineKeyboardButton(
            text="⬅️ К началу (3/3)",
            callback_data="menu:page:1"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_category_keyboard(category: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с командами для указанной категории
    """
    keyboard = []
    
    # Получаем список команд для категории
    commands = COMMAND_CATEGORIES.get(category, [])
    
    # Добавляем кнопки для каждой команды (по 2 в ряд)
    for i in range(0, len(commands), 2):
        row = []
        for j in range(2):
            if i + j < len(commands):
                cmd = commands[i + j]
                cmd_text = f"/{cmd}"
                row.append(InlineKeyboardButton(
                    text=cmd_text,
                    callback_data=f"exec:/{cmd}"
                ))
        keyboard.append(row)
    
    # Добавляем кнопку для полной справки по категории
    keyboard.append([InlineKeyboardButton(
        text="📖 Справка по категории",
        callback_data=f"help_cat:{category}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def format_category_message(category: str) -> str:
    """Форматирует сообщение для отображения категории команд"""
    commands = COMMAND_CATEGORIES.get(category, [])
    
    # Заголовок
    message = f"📋 <b>Категория: {category}</b>\n\n"
    message += "Доступные команды:\n"
    
    # Список команд с описаниями
    for cmd in commands:
        cmd_info = COMMAND_HELP.get(cmd, {})
        description = cmd_info.get("description", "")
        message += f"<code>/{cmd}</code> - {description}\n"
    
    # Инструкция
    message += "\n💡 <b>Нажмите на кнопку</b> для выполнения команды или <b>скопируйте команду</b> для ручного ввода."
    
    return message


def format_category_help_message(category: str) -> str:
    """Форматирует полную справку по всем командам категории"""
    commands = COMMAND_CATEGORIES.get(category, [])
    
    # Заголовок
    message = f"📖 <b>Полная справка: {category}</b>\n\n"
    
    # Подробная справка для каждой команды
    for cmd in commands:
        cmd_info = COMMAND_HELP.get(cmd, {})
        detailed = cmd_info.get("detailed", f"Справка для /{cmd} не найдена")
        message += f"{detailed}\n\n"
        message += "─" * 30 + "\n\n"
    
    return message.rstrip()


@router.callback_query(F.data.startswith("menu:page:"))
async def handle_menu_page_navigation(callback: CallbackQuery) -> None:
    """Обработчик навигации по страницам главного меню"""
    try:
        page = int(callback.data.split(":")[-1])
        
        info(f"Пользователь {callback.from_user.id} переключился на страницу меню {page}", "menu")
        
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
            "⚖️ <b>Правовое предупреждение:</b> Бот предназначен для администрирования собственных машин."
            "Использование без явного разрешения владельца запрещено."
        )
        
        keyboard = create_main_menu_keyboard(page)
        await callback.message.edit_text(welcome_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        warning(f"Ошибка навигации по меню: {e}", "menu")
        await callback.answer("⚠️ Ошибка навигации", show_alert=True)


@router.callback_query(F.data.startswith("category:"))
async def handle_category_display(callback: CallbackQuery) -> None:
    """Обработчик отображения команд категории"""
    try:
        category = callback.data.split(":", 1)[1]
        info(f"Пользователь {callback.from_user.id} открыл категорию '{category}'", "menu")
        
        if category not in COMMAND_CATEGORIES:
            warning(f"Запрошена несуществующая категория: {category}", "menu")
            await callback.answer("⚠️ Категория не найдена", show_alert=True)
            return
        
        message_text = format_category_message(category)
        keyboard = create_category_keyboard(category)
        
        await callback.message.answer(message_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        warning(f"Ошибка отображения категории: {e}", "menu")
        await callback.answer("⚠️ Ошибка отображения категории", show_alert=True)


@router.callback_query(F.data.startswith("exec:"))
async def handle_command_execution(callback: CallbackQuery) -> None:
    """
    Обработчик выполнения команды через inline-кнопку.
    Использует прямой вызов обработчиков вместо роутинга обновлений.
    """
    try:
        command_full = callback.data.split(":", 1)[1]
        command_name = command_full.lstrip("/").split()[0]

        info(f"Пользователь {callback.from_user.id} выполнил команду '{command_full}' через меню", "menu")

        # Импортируем обработчики локально во избежание циклических импортов
        try:
            from app.handlers.cancel import handle_cancel
            from app.handlers.cmd import (
                handle_cmd_dump,
                handle_cmd_session_start,
                handle_cmd_session_stop,
                handle_cmd_update,
            )
            from app.handlers.logs_export import (
                handle_logs_export,
                handle_logs_export_csv,
                handle_logs_export_json,
                handle_logs_export_txt,
                handle_logs_export_xml,
            )
            from app.handlers.monitor import handle_monitor_list, handle_monitor_stop
            from app.handlers.mouse_keyboard import handle_screen_mark
            from app.handlers.paths_handlers import (
                handle_path_global_list,
                handle_path_user_list,
                handle_paths_reload,
                handle_paths_show_all,
            )
            from app.handlers.processes import handle_processes
            from app.handlers.remote_desktop import handle_rdp_start, handle_rdp_stop
            from app.handlers.screen import handle_screen, handle_screen_find
            from app.handlers.stats import (
                handle_stats,
                handle_stats_audit,
                handle_stats_commands,
                handle_stats_export,
                handle_stats_patterns,
                handle_stats_performance,
                handle_stats_users,
            )
            from app.handlers.system import handle_reload, handle_tasklist

            # Маппинг команд на их обработчики (только для команд без обязательных аргументов)
            pure_handlers = {
                "reload": handle_reload,
                "tasklist": handle_tasklist,
                "processes": handle_processes,
                "path_global_list": handle_path_global_list,
                "path_user_list": handle_path_user_list,
                "paths_show_all": handle_paths_show_all,
                "paths_reload": handle_paths_reload,
                "monitor_list": handle_monitor_list,
                "monitor_stop": handle_monitor_stop,
                "cmd_session_start": handle_cmd_session_start,
                "cmd_session_stop": handle_cmd_session_stop,
                "cmdupdate": handle_cmd_update,
                "cmd_dump": handle_cmd_dump,
                "rdp_start": handle_rdp_start,
                "rdp_stop": handle_rdp_stop,
                "screen": handle_screen,
                "screen_find": handle_screen_find,
                "screen_mark": handle_screen_mark,
                "cancel": handle_cancel,
                # Статистика
                "stats": handle_stats,
                "stats_commands": handle_stats_commands,
                "stats_users": handle_stats_users,
                "stats_performance": handle_stats_performance,
                "stats_patterns": handle_stats_patterns,
                "stats_audit": handle_stats_audit,
                "stats_export": handle_stats_export,
                # Логи
                "logs_export": handle_logs_export,
                "logs_export_json": handle_logs_export_json,
                "logs_export_csv": handle_logs_export_csv,
                "logs_export_xml": handle_logs_export_xml,
                "logs_export_txt": handle_logs_export_txt,
            }
        except Exception as import_error:
            error(f"Ошибка импорта обработчиков команд: {import_error}", "menu")
            await callback.answer("⚠️ Внутренняя ошибка бота", show_alert=True)
            return

        # Если команда поддерживается для прямого запуска
        if command_name in pure_handlers:
            # Создаем синтетическое сообщение.
            # Важно передать bot=callback.bot для корректной привязки контекста
            synthetic_message = Message(
                message_id=callback.message.message_id,
                date=callback.message.date,
                chat=callback.message.chat,
                from_user=callback.from_user,
                text=command_full
            )
            
            if callback.bot:
                synthetic_message._bot = callback.bot

            await callback.answer(f"⚡ Выполняется: {command_name}")
            
            # Вызываем обработчик напрямую
            await pure_handlers[command_name](synthetic_message)
            
        else:
            # Если команда требует аргументов (например, /on, /type, /upload)
            await callback.answer(
                f"⌨️ Эта команда требует ввода параметров.\nСкопируйте: {command_full} [параметры]", 
                show_alert=True
            )

    except Exception as e:
        error(f"Ошибка выполнения команды через меню: {e}", "menu")
        # В продакшене можно скрыть детали ошибки
        await callback.answer(f"⚠️ Ошибка: {str(e)[:100]}", show_alert=True)


@router.callback_query(F.data.startswith("help_cat:"))
async def handle_category_help(callback: CallbackQuery) -> None:
    """Обработчик отображения полной справки по категории"""
    try:
        category = callback.data.split(":", 1)[1]
        info(f"Пользователь {callback.from_user.id} запросил справку по категории '{category}'", "menu")
        
        if category not in COMMAND_CATEGORIES:
            warning(f"Запрошена справка для несуществующей категории: {category}", "menu")
            await callback.answer("⚠️ Категория не найдена", show_alert=True)
            return
        
        help_text = format_category_help_message(category)
        
        # Telegram ограничивает длину сообщения до 4096 символов
        if len(help_text) > 4096:
            parts = []
            current_part = ""
            for line in help_text.split("\n"):
                if len(current_part) + len(line) + 1 > 4096:
                    parts.append(current_part)
                    current_part = line + "\n"
                else:
                    current_part += line + "\n"
            if current_part:
                parts.append(current_part)
            
            for part in parts:
                await callback.message.answer(part)
        else:
            await callback.message.answer(help_text)
        
        await callback.answer("📖 Справка отправлена")
        
    except Exception as e:
        warning(f"Ошибка отображения справки по категории: {e}", "menu")
        await callback.answer("⚠️ Ошибка отображения справки", show_alert=True)