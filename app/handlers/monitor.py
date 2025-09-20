# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

from aiogram.filters import Command
from aiogram.types import Message

from ..core.logging import debug, error, info, warning
from ..router import router
from ..services.monitor import FileMonitor

monitor = FileMonitor()


@router.message(Command("monitor_add"))
async def handle_monitor_add(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        warning("Команда /monitor_add вызвана без параметров", "monitor")
        await message.answer("❌ Укажите путь для мониторинга")
        return

    path = os.path.abspath(args[1])
    info(f"Попытка добавить мониторинг для пути: {path}", "monitor")
    
    if not os.path.exists(path):
        warning(f"Путь для мониторинга не существует: {path}", "monitor")
        await message.answer(f"⚠️ Путь не существует: {path}")
        return

    try:
        await monitor.add_path(path, message.bot, message.from_user.id)
        info(f"Мониторинг успешно добавлен для: {path}", "monitor")
        await message.answer(f"👁️ Мониторинг добавлен для: {path}")
    except Exception as e:
        error(f"Ошибка при добавлении мониторинга для {path}: {e}", "monitor")
        await message.answer(f"❌ Ошибка при добавлении мониторинга: {e}")


@router.message(Command("monitor_remove"))
async def handle_monitor_remove(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите путь для удаления")
        return

    path = os.path.abspath(args[1])
    removed = await monitor.remove_path(path)
    if removed:
        await message.answer(f"⛔ Мониторинг удален для: {path}")
    else:
        await message.answer(f"ℹ️ Путь не в списке мониторинга: {path}")


@router.message(Command("monitor_list"))
async def handle_monitor_list(message: Message) -> None:
    paths = await monitor.get_paths()
    if not paths:
        await message.answer("ℹ️ Нет активных мониторингов")
        return
    response = "👁️ Отслеживаемые пути:\n" + "\n".join(paths)
    await message.answer(response)


@router.message(Command("monitor_stop"))
async def handle_monitor_stop(message: Message) -> None:
    await monitor.stop()
    await message.answer("⛔ Мониторинг полностью остановлен и очищен")
