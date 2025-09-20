# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import tempfile
import os

from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from ..config.paths import get_paths_config
from ..core.logging import error, info
from ..router import router


async def send_paths_as_file(message: Message, content: str, filename: str, caption: str) -> None:
    """Отправляет содержимое путей как файл"""
    try:
        # Создаем BufferedInputFile из содержимого
        input_file = BufferedInputFile(
            content.encode('utf-8'),
            filename=filename
        )
        
        await message.bot.send_document(
            chat_id=message.chat.id,
            document=input_file,
            caption=caption
        )
        info(f"Successfully sent paths file: {filename}")
    except Exception as e:
        error(f"Failed to send paths file {filename}: {e}")
        await message.answer("❌ Ошибка при отправке файла с путями")


@router.message(Command("path_global_list"))
async def handle_path_global_list(message: Message) -> None:
    """Показать системные пути (только чтение)"""
    config = get_paths_config()
    default_paths = config.default_paths

    if not default_paths:
        await message.answer("ℹ️ Нет системных путей")
        return

    # Создаем содержимое файла
    file_content = "Системные пути (из PATH):\n"
    file_content += "=" * 50 + "\n\n"
    
    for name, path in sorted(default_paths.items()):
        if isinstance(path, list):
            file_content += f"{name}: {len(path)} вариантов\n"
            for i, p in enumerate(path, 1):
                file_content += f"  {i}. {p}\n"
        else:
            file_content += f"{name}: {path}\n"
        file_content += "\n"
    
    # Отправляем файл
    await send_paths_as_file(
        message=message,
        content=file_content,
        filename=f"system_paths_{len(default_paths)}_items.txt",
        caption=f"🌐 <b>Системные пути</b>\n\n📊 Всего путей: {len(default_paths)}\n📁 Загружено из системного PATH"
    )


@router.message(Command("path_user_add"))
async def handle_path_user_add(message: Message) -> None:
    """Добавить пользовательский путь"""
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Используйте: /path_user_add `имя` `путь`")
        return

    name = args[1]
    path = args[2]
    user_id = message.from_user.id

    config = get_paths_config()
    if config.add_user_path(user_id, name, path):
        await message.answer(f"✅ Пользовательский путь сохранен:\n{name} → {config.get_path(user_id, name)}")
    else:
        await message.answer(f"⚠️ Путь не существует: {path}")


@router.message(Command("path_user_list"))
async def handle_path_user_list(message: Message) -> None:
    """Показать пользовательские пути"""
    user_id = message.from_user.id
    config = get_paths_config()
    user_paths = config.load_user_paths(user_id)

    if not user_paths:
        await message.answer("ℹ️ Нет пользовательских путей")
        return

    # Если путей немного, отправляем обычным сообщением
    if len(user_paths) <= 20:
        response = f"👤 <b>Пользовательские пути (ID: {user_id}):</b>\n\n"
        for name, path in sorted(user_paths.items()):
            if isinstance(path, list):
                response += f"• <b>{name}</b>: {len(path)} вариантов\n"
                for i, p in enumerate(path, 1):
                    response += f"  {i}. {p}\n"
            else:
                response += f"• <b>{name}</b>: {path}\n"
        
        await message.answer(response)
        return

    # Если путей много, отправляем файлом
    file_content = f"Пользовательские пути (ID: {user_id}):\n"
    file_content += "=" * 50 + "\n\n"
    
    for name, path in sorted(user_paths.items()):
        if isinstance(path, list):
            file_content += f"{name}: {len(path)} вариантов\n"
            for i, p in enumerate(path, 1):
                file_content += f"  {i}. {p}\n"
        else:
            file_content += f"{name}: {path}\n"
        file_content += "\n"
    
    # Отправляем файл
    await send_paths_as_file(
        message=message,
        content=file_content,
        filename=f"user_paths_{user_id}_{len(user_paths)}_items.txt",
        caption=f"👤 <b>Пользовательские пути</b>\n\n📊 Всего путей: {len(user_paths)}\n📁 ID пользователя: {user_id}"
    )


@router.message(Command("path_user_del"))
async def handle_path_user_del(message: Message) -> None:
    """Удалить пользовательский путь"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите имя пути для удаления")
        return

    name = args[1]
    user_id = message.from_user.id
    config = get_paths_config()

    if config.remove_user_path(user_id, name):
        await message.answer(f"✅ Пользовательский путь удален: {name}")
    else:
        await message.answer(f"⚠️ Пользовательский путь не найден: {name}")


@router.message(Command("paths_reload"))
async def handle_paths_reload(message: Message) -> None:
    """Перезагрузить все пути из файлов"""
    config = get_paths_config()
    config.reload_paths()
    
    user_id = message.from_user.id
    stats = config.get_stats(user_id)
    
    response = "🔄 <b>Пути перезагружены:</b>\n"
    response += f"• Системные: {stats['default_paths']}\n"
    response += f"• Пользовательские: {stats['user_paths']}\n"
    response += f"• Всего доступно: {stats['total_paths']}"
    
    await message.answer(response)


@router.message(Command("paths_show_all"))
async def handle_paths_show_all(message: Message) -> None:
    """Показать все доступные пути (пользовательские + системные)"""
    user_id = message.from_user.id
    config = get_paths_config()
    all_paths = config.get_all_paths(user_id)

    if not all_paths:
        await message.answer("ℹ️ Нет доступных путей")
        return

    # Создаем содержимое файла
    file_content = f"Все доступные пути (ID: {user_id}):\n"
    file_content += "=" * 50 + "\n\n"
    
    # Сначала добавляем пользовательские пути
    user_paths = config.load_user_paths(user_id)
    if user_paths:
        file_content += "ПОЛЬЗОВАТЕЛЬСКИЕ ПУТИ (приоритет):\n"
        file_content += "-" * 30 + "\n"
        for name, path in sorted(user_paths.items()):
            file_content += f"{name}: {path}\n"
        file_content += "\n"
    
    # Затем системные пути (исключая те, что уже есть в пользовательских)
    system_paths = {k: v for k, v in config.default_paths.items() if k not in user_paths}
    if system_paths:
        file_content += "СИСТЕМНЫЕ ПУТИ (из PATH):\n"
        file_content += "-" * 30 + "\n"
        for name, path in sorted(system_paths.items()):
            file_content += f"{name}: {path}\n"
    
    # Отправляем файл
    await send_paths_as_file(
        message=message,
        content=file_content,
        filename=f"all_paths_user_{user_id}_{len(all_paths)}_items.txt",
        caption=f"📁 <b>Все доступные пути</b>\n\n👤 Пользовательские: {len(user_paths)}\n🌐 Системные: {len(system_paths)}\n📊 Всего: {len(all_paths)}"
    )