# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

from aiogram.filters import Command
from aiogram.types import Message

from ..paths_config import (
    PATHS,
    get_all_paths,
    load_default_paths,
    load_paths,
    save_default_paths,
    save_paths,
)
from ..router import router


@router.message(Command("add_path"))
async def handle_add_path(message: Message) -> None:
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Используйте: /add_path `имя` `путь`")
        return

    name = args[1]
    path = args[2]

    if not os.path.exists(path):
        await message.answer(f"⚠️ Путь не существует: {path}")
        return

    PATHS[name] = os.path.abspath(path)
    save_paths(PATHS)
    await message.answer(f"✅ Путь сохранен:\n{name} → {PATHS[name]}")


@router.message(Command("list_paths"))
async def handle_list_paths(message: Message) -> None:
    if not PATHS:
        await message.answer("ℹ️ Нет зарегистрированных путей")
        return

    response = "📁 Зарегистрированные пути:\n\n"
    for name, path in PATHS.items():
        response += f"• <b>{name}</b>: {path}\n"
    await message.answer(response)


@router.message(Command("del_path"))
async def handle_del_path(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите имя пути для удаления")
        return

    name = args[1]
    if name in PATHS:
        del PATHS[name]
        save_paths(PATHS)
        await message.answer(f"✅ Путь удален: {name}")
    else:
        await message.answer(f"⚠️ Путь не найден: {name}")


@router.message(Command("add_default_path"))
async def handle_add_default_path(message: Message) -> None:
    """Добавить путь в предустановленные (jsons/DEFAULT_PATHS.json)"""
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Используйте: /add_default_path `имя` `путь`")
        return

    name = args[1]
    path = args[2]

    if not os.path.exists(path):
        await message.answer(f"⚠️ Путь не существует: {path}")
        return

    # Загружаем текущие предустановленные пути
    default_paths = load_default_paths()
    default_paths[name] = os.path.abspath(path)
    save_default_paths(default_paths)

    # Обновляем глобальные пути
    global PATHS
    PATHS = get_all_paths()

    await message.answer(f"✅ Предустановленный путь добавлен:\n{name} → {os.path.abspath(path)}")


@router.message(Command("list_default_paths"))
async def handle_list_default_paths(message: Message) -> None:
    """Показать все предустановленные пути"""
    default_paths = load_default_paths()
    if not default_paths:
        await message.answer("ℹ️ Нет предустановленных путей")
        return

    response = "📁 Предустановленные пути (jsons/DEFAULT_PATHS.json):\n\n"
    for name, path in default_paths.items():
        if isinstance(path, list):
            response += f"• <b>{name}</b>: {len(path)} вариантов\n"
            for i, p in enumerate(path, 1):
                response += f"  {i}. {p}\n"
        else:
            response += f"• <b>{name}</b>: {path}\n"
    await message.answer(response)


@router.message(Command("del_default_path"))
async def handle_del_default_path(message: Message) -> None:
    """Удалить путь из предустановленных"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите имя пути для удаления")
        return

    name = args[1]
    default_paths = load_default_paths()

    if name in default_paths:
        del default_paths[name]
        save_default_paths(default_paths)

        # Обновляем глобальные пути
        global PATHS
        PATHS = get_all_paths()

        await message.answer(f"✅ Предустановленный путь удален: {name}")
    else:
        await message.answer(f"⚠️ Предустановленный путь не найден: {name}")


@router.message(Command("reload_paths"))
async def handle_reload_paths(message: Message) -> None:
    """Перезагрузить все пути из файлов"""
    global PATHS
    PATHS = get_all_paths()

    user_count = len(load_paths())
    default_count = len(load_default_paths())
    total_count = len(PATHS)

    await message.answer(
        f"🔄 Пути перезагружены:\n"
        f"• Пользовательские: {user_count}\n"
        f"• Предустановленные: {default_count}\n"
        f"• Всего: {total_count}"
    )


