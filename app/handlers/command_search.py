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

import asyncio
import os
import subprocess
import time

from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from ..config import get_settings
from ..core.logging import info, warning
from ..help_texts import get_command_help_text
from ..router import router


@router.message(Command("find"))
async def handle_find(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        warning("Команда /find вызвана без параметров", "command_search")
        await message.answer(get_command_help_text("find"))
        return

    search_params = args[1]
    info(f"Начало поиска файлов с параметрами: {search_params}", "command_search")
    msg = await message.answer("🔍 Поиск файлов...")

    async def run_async() -> None:
        try:
            name_filter = None
            size_filter = None
            ext_filter = None
            root_dir = None
            limit_count = 1000
            timeout_sec = 20
            params = search_params.split()
            for param in params:
                if param.startswith("name:"):
                    name_filter = param[5:]
                elif param.startswith("size:"):
                    size_filter = param[5:]
                elif param.startswith("ext:"):
                    ext_filter = param[4:].split(",")
                elif param.startswith("root:"):
                    root_dir = param[5:]
                elif param.startswith("limit:"):
                    try:
                        limit_count = max(1, min(int(param[6:]), 10000))
                    except Exception:
                        pass
                elif param.startswith("timeout:"):
                    try:
                        timeout_sec = max(5, min(int(param[8:]), 600))
                    except Exception:
                        pass

            is_windows = os.name == "nt"
            encoding = get_settings().get_encoding()
            timed_out = False
            started_at = time.time()

            if is_windows:
                if not root_dir:
                    # Безопасный дефолт, чтобы не сканировать весь диск
                    root_dir = os.getcwd()
                cmd = ["where", "/R", root_dir, name_filter or "*"]
            else:
                # На *nix требуем явный root
                if not root_dir:
                    try:
                        await message.bot.edit_message_text(
                            chat_id=msg.chat.id,
                            message_id=msg.message_id,
                            text="⚠️ Укажите корень поиска: root:/path (на *nix обязательно)",
                        )
                    except Exception:
                        pass
                    return
                cmd = ["find", root_dir, "-type", "f"]
                if name_filter:
                    cmd += ["-name", name_filter]
                if size_filter:
                    cmd += ["-size", size_filter]

            # Краткое сообщение о параметрах и лимитах
            try:
                progress = (
                    "🔍 Поиск файлов...\n"
                    f"- Root: {root_dir}\n"
                    f"- Name: {name_filter or '*'}\n"
                    f"- Ext: {','.join(ext_filter) if ext_filter else '-'}\n"
                    f"- Size: {size_filter or '-'}\n"
                    f"- Limit: {limit_count}, Timeout: {timeout_sec}s"
                )
                await message.bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=progress)
            except Exception:
                pass

            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding=encoding,
                    timeout=timeout_sec,
                )
                stdout_text = result.stdout or ""
                stderr_text = result.stderr or ""
            except subprocess.TimeoutExpired as e:
                timed_out = True
                stdout_text = (e.output or e.stdout or "") if hasattr(e, "stdout") else (e.output or "")
                stderr_text = (e.stderr or "") if hasattr(e, "stderr") else ""

            raw_files = [f for f in stdout_text.split("\n") if f.strip()]

            # Постфильтрация по расширениям (кроссплатформенно)
            files = raw_files
            if ext_filter:
                normalized_exts = [e.lower().lstrip(".") for e in ext_filter]

                def has_ext(path: str) -> bool:
                    lower = path.lower()
                    return any(lower.endswith("." + ext) or lower.endswith(ext) for ext in normalized_exts)

                files = [f for f in files if has_ext(f)]

            # Лимит результатов на уровне приложения
            if limit_count is not None:
                files = files[:limit_count]

            response = f"🔍 Найдено файлов: {len(files)}\n" + "\n".join(files[:50])
            if len(files) > 50:
                response += f"\n...и еще {len(files) - 50} файлов"

            try:
                await message.bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=response)
            except Exception:
                pass

            if files:
                duration_ms = int((time.time() - started_at) * 1000)
                stderr_lines = [line for line in (stderr_text or "").split("\n") if line.strip()]
                summary_lines = [
                    "Search summary:",
                    f"- Root: {root_dir}",
                    f"- Name: {name_filter or '*'}",
                    f"- Ext: {','.join(ext_filter) if ext_filter else '-'}",
                    f"- Size: {size_filter or '-'}",
                    f"- Limit: {limit_count}",
                    f"- Timeout: {timeout_sec}s (timed out: {'yes' if timed_out else 'no'})",
                    f"- Duration: {duration_ms} ms",
                    f"- Raw matches: {len(raw_files)}",
                    f"- Filtered matches (<= limit): {len(files)}",
                    f"- Stderr lines: {len(stderr_lines)}",
                    "",
                    f"Results (up to {limit_count}):",
                ]
                detailed = "\n".join(summary_lines + files)
                body_size_bytes = len(detailed.encode("utf-8"))
                detailed = detailed + f"\n- Body bytes: {body_size_bytes}"
                buf = BufferedInputFile(detailed.encode("utf-8"), filename="search_results.txt")
                await message.bot.send_document(chat_id=msg.chat.id, document=buf)
        except Exception as e:

            def _mask(text: str) -> str:
                # Hide sensitive error details: length + first/last char [[memory:4740490]]
                if not text:
                    return "len=0"
                return f"len={len(text)}, first='{text[0]}', last='{text[-1]}'"

            try:
                await message.bot.edit_message_text(
                    chat_id=msg.chat.id, message_id=msg.message_id, text=f"⚠️ Ошибка поиска: {_mask(str(e))}"
                )
            except Exception:
                pass

    asyncio.create_task(run_async())
