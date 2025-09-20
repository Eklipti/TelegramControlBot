# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Утилиты для потокового чтения stdout/stderr подпроцессов и обновления сообщений Telegram.
"""
from __future__ import annotations

import asyncio
import html
from typing import Optional, Callable

from aiogram import Bot

from ..config import get_settings
from ..core.logging import debug, error, info, log_call


@log_call("cmd_stream")
async def stream_process_to_message(
    *,
    chat_id: int,
    message_id: int,
    proc: asyncio.subprocess.Process,
    bot: Bot,
    force_refresh_event: Optional[asyncio.Event] = None,
    max_tail_lines: int = 50,
    final_tail_lines: int = 100,
    status_line: Optional[Callable[[int, int], str]] = None,
    session_storage: Optional[dict] = None,
) -> None:
    """
    Читает вывод процесса и периодически обновляет сообщение.
    - Показывает «хвост» последних N строк (по умолчанию 50).
    - При завершении показывает «хвост» последних 100 строк и статус.
    - Поддерживает «форс-обновление» через asyncio.Event.
    """
    encoding = get_settings().get_encoding()
    full_output = ""
    start_time = asyncio.get_event_loop().time()
    last_update = start_time
    line_count = 0
    buffer = b""
    BATCH_SIZE = 512

    def _status(elapsed_s: int, lines: int) -> str:
        if status_line:
            return status_line(elapsed_s, lines)
        return f"⏱️ {elapsed_s}s | 📜 {lines} lines"

    try:
        while True:
            # Читаем порцию вывода
            should_force = force_refresh_event.is_set() if force_refresh_event else False
            chunk = await proc.stdout.read(BATCH_SIZE) if proc.stdout else b""

            # Нет данных прямо сейчас
            if not chunk:
                if proc.returncode is not None:
                    break
                if should_force:
                    current = asyncio.get_event_loop().time()
                    elapsed = int(current - start_time)
                    lines = full_output.split("\n")
                    display_lines = lines[-max_tail_lines:] if len(lines) > max_tail_lines else lines
                    display_output = html.escape("\n".join(display_lines))
                    content = f"<code>{_status(elapsed, line_count)}\n{'-' * 20}\n{display_output}</code>"
                    try:
                        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=content)
                    except Exception:
                        pass
                    last_update = current
                await asyncio.sleep(0.01)
                continue

            buffer += chunk
            current = asyncio.get_event_loop().time()

            # Пытаемся декодировать, не теряя границы символов
            try:
                text = buffer.decode(encoding, errors="strict")
                buffer = b""
            except UnicodeDecodeError:
                # Ждём следующую порцию, чтобы декодировать корректно
                continue

            full_output += text
            line_count += text.count("\n")
            
            # Сохраняем полный вывод в сессии для доступа через cmd_dump
            if session_storage is not None:
                session_storage["full_output"] = full_output

            # Троттлинг обновлений — не чаще раза в ~0.7 сек или по форс-сигналу
            if (current - last_update) >= 0.7 or should_force:
                elapsed = int(current - start_time)
                lines = full_output.split("\n")
                display_lines = lines[-max_tail_lines:] if len(lines) > max_tail_lines else lines
                display_output = html.escape("\n".join(display_lines))
                content = f"<code>{_status(elapsed, line_count)}\n{'-' * 20}\n{display_output}</code>"
                try:
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=content)
                except Exception:
                    pass
                last_update = current
    finally:
        # Финальный «хвост» и статус
        if buffer:
            try:
                text = buffer.decode(encoding, errors="replace")
                full_output += text
                line_count += text.count("\n")
                # Сохраняем финальный вывод в сессии
                if session_storage is not None:
                    session_storage["full_output"] = full_output
            except Exception:
                pass

        rc = proc.returncode if proc.returncode is not None else await proc.wait()
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        status = "✅ Успешно" if rc == 0 else f"❌ Ошибка (код: {rc})"
        lines = full_output.split("\n")
        display_lines = lines[-final_tail_lines:] if len(lines) > final_tail_lines else lines
        display_output = html.escape("\n".join(display_lines))
        content = f"{status}\n<code>{_status(elapsed, line_count)}\n{'-' * 20}\n{display_output}</code>"
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=content)
        except Exception:
            pass

        debug(f"proc finished rc={rc}, elapsed={elapsed}s, lines={line_count}", "cmd_stream")
