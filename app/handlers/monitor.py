# Telegram Control Bot
# Copyright (C) 2025-2026 Eklipti
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

import os

from aiogram.filters import Command
from aiogram.types import Message

from ..core.logging import error, info, warning
from ..help_texts import get_command_help_text
from ..router import router
from ..services.monitor import FileMonitor

monitor = FileMonitor()


@router.message(Command("monitor_add"))
async def handle_monitor_add(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        warning("Команда /monitor_add вызвана без параметров", "monitor")
        await message.answer(get_command_help_text("monitor_add"))
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
        await message.answer(get_command_help_text("monitor_remove"))
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
