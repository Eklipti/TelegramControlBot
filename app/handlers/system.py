# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import psutil
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from ..router import router


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
