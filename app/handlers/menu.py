# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Система inline-меню для навигации по командам бота
"""

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..core.logging import info, warning
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
    
    Args:
        page: Номер страницы (1, 2, или 3)
    
    Returns:
        InlineKeyboardMarkup с кнопками категорий и навигацией
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
    
    Args:
        category: Название категории
    
    Returns:
        InlineKeyboardMarkup с кнопками команд и справкой
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
                # Используем короткое название команды для кнопки
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
    """
    Форматирует сообщение для отображения категории команд
    
    Args:
        category: Название категории
    
    Returns:
        Отформатированный текст сообщения
    """
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
    """
    Форматирует полную справку по всем командам категории
    
    Args:
        category: Название категории
    
    Returns:
        Отформатированный текст справки
    """
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
    """
    Обработчик навигации по страницам главного меню
    
    Callback data format: menu:page:N (где N = 1, 2, или 3)
    """
    try:
        # Извлекаем номер страницы
        page = int(callback.data.split(":")[-1])
        
        info(f"Пользователь {callback.from_user.id} переключился на страницу меню {page}", "menu")
        
        # Получаем текст приветственного сообщения
        welcome_text = (
            "🤖 <b>Добро пожаловать в ControlBot!</b>\n\n"
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
        
        # Создаем клавиатуру для выбранной страницы
        keyboard = create_main_menu_keyboard(page)
        
        # Редактируем сообщение
        await callback.message.edit_text(welcome_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        warning(f"Ошибка навигации по меню: {e}", "menu")
        await callback.answer("⚠️ Ошибка навигации", show_alert=True)


@router.callback_query(F.data.startswith("category:"))
async def handle_category_display(callback: CallbackQuery) -> None:
    """
    Обработчик отображения команд категории
    
    Callback data format: category:название_категории
    """
    try:
        # Извлекаем название категории
        category = callback.data.split(":", 1)[1]
        
        info(f"Пользователь {callback.from_user.id} открыл категорию '{category}'", "menu")
        
        # Проверяем, существует ли категория
        if category not in COMMAND_CATEGORIES:
            warning(f"Запрошена несуществующая категория: {category}", "menu")
            await callback.answer("⚠️ Категория не найдена", show_alert=True)
            return
        
        # Форматируем сообщение
        message_text = format_category_message(category)
        
        # Создаем клавиатуру с командами
        keyboard = create_category_keyboard(category)
        
        # Отправляем новое сообщение
        await callback.message.answer(message_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        warning(f"Ошибка отображения категории: {e}", "menu")
        await callback.answer("⚠️ Ошибка отображения категории", show_alert=True)


@router.callback_query(F.data.startswith("exec:"))
async def handle_command_execution(callback: CallbackQuery) -> None:
    """
    Обработчик выполнения команды через inline-кнопку
    
    Callback data format: exec:/команда
    """
    try:
        # Извлекаем команду
        command = callback.data.split(":", 1)[1]
        
        info(f"Пользователь {callback.from_user.id} выполнил команду '{command}' через меню", "menu")
        
        # Создаем синтетическое сообщение для обработки командой
        if callback.message:
            # Создаем Message объект с командой, используя chat из callback.message
            from aiogram.types import Chat, User
            
            # Создаем синтетическое сообщение
            synthetic_message = Message(
                message_id=callback.message.message_id + 1000000,  # Уникальный ID
                date=callback.message.date,
                chat=callback.message.chat,
                from_user=callback.from_user,
                text=command,
                bot=callback.bot
            )
            
            # Обрабатываем сообщение через диспетчер
            # Получаем диспетчер из бота
            from aiogram import Dispatcher
            from aiogram.types import Update
            
            # Создаем update с синтетическим сообщением
            update = Update(
                update_id=999999999,  # Временный ID
                message=synthetic_message
            )
            
            # Важно: получаем диспетчер из контекста бота
            # и обрабатываем update через него
            try:
                # Пытаемся получить диспетчер и обработать
                dp = Dispatcher.get_current()
                await dp.feed_update(callback.bot, update)
            except Exception:
                # Если не получилось через диспетчер, пробуем через роутер
                await router.feed_update(callback.bot, update)
            
            await callback.answer(f"⚡ Выполняется: {command}")
        
    except Exception as e:
        warning(f"Ошибка выполнения команды через меню: {e}", "menu")
        await callback.answer("⚠️ Ошибка выполнения команды", show_alert=True)


@router.callback_query(F.data.startswith("help_cat:"))
async def handle_category_help(callback: CallbackQuery) -> None:
    """
    Обработчик отображения полной справки по категории
    
    Callback data format: help_cat:название_категории
    """
    try:
        # Извлекаем название категории
        category = callback.data.split(":", 1)[1]
        
        info(f"Пользователь {callback.from_user.id} запросил справку по категории '{category}'", "menu")
        
        # Проверяем, существует ли категория
        if category not in COMMAND_CATEGORIES:
            warning(f"Запрошена справка для несуществующей категории: {category}", "menu")
            await callback.answer("⚠️ Категория не найдена", show_alert=True)
            return
        
        # Форматируем справку
        help_text = format_category_help_message(category)
        
        # Telegram ограничивает длину сообщения до 4096 символов
        if len(help_text) > 4096:
            # Разбиваем на части
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
            
            # Отправляем части
            for i, part in enumerate(parts):
                await callback.message.answer(part)
        else:
            # Отправляем одним сообщением
            await callback.message.answer(help_text)
        
        await callback.answer("📖 Справка отправлена")
        
    except Exception as e:
        warning(f"Ошибка отображения справки по категории: {e}", "menu")
        await callback.answer("⚠️ Ошибка отображения справки", show_alert=True)

