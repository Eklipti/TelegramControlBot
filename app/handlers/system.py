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

import psutil
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from ..router import router
from ..config import reload_settings
from ..core.logging import info, error


@router.message(Command("reload"))
async def handle_reload(message: Message) -> None:
    from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager

    manager = get_confirmation_manager()
    action_config = DANGEROUS_ACTIONS["reload"]

    await manager.create_confirmation(
        chat_id=message.chat.id,
        action_type="reload",
        action_data={"action_type": "reload", "action_data": {}},
        warning_message=action_config["warning"],
        timeout=action_config["timeout"],
    )

@router.message(Command("tasklist"))
async def handle_tasklist(message: Message) -> None:
    try:
        summary: dict[str, dict[str, int]] = {}
        detailed_lines: list[str] = []

        for proc in psutil.process_iter(attrs=["pid", "name", "memory_info", "username"]):
            try:
                info = proc.info
                name = info.get("name") or "<unknown>"
                pid = info.get("pid")
                mem = info.get("memory_info").rss if info.get("memory_info") else 0
                username = info.get("username") or "-"

                if name not in summary:
                    summary[name] = {"count": 0, "total_rss": 0}
                summary[name]["count"] += 1
                summary[name]["total_rss"] += int(mem)

                mem_mb = mem / (1024 * 1024)
                detailed_lines.append(f"{name}\n<code>PID: {pid} | User: {username} | RSS: {mem_mb:.1f} MB</code>")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if not summary:
            await message.answer("❌ Не найдено активных процессов")
            return

        response = "🖥️ <b>Сводка по процессам:</b>\n"
        sorted_processes = sorted(summary.items(), key=lambda x: x[1]["total_rss"], reverse=True)
        for process, data in sorted_processes[:10]:
            mem_mb = data["total_rss"] / (1024 * 1024)
            response += f"\n• {process}: {data['count']} экз., {mem_mb:.1f} MB"

        await message.answer(response)
        if detailed_lines:
            detailed_text = "\n\n".join(detailed_lines)
            await message.answer_document(
                BufferedInputFile(detailed_text.encode("utf-8"), filename="process_details.txt"),
                caption="📋 Детальный список процессов",
            )
    except Exception as e:
        # Mask error details per policy [[memory:4740490]]
        err = str(e)
        masked = f"len={len(err)}, first='{err[0] if err else ''}', last='{err[-1] if err else ''}'"
        await message.answer(f"⚠️ Ошибка: {masked}")
