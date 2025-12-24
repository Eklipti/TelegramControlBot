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

import asyncio
import logging
import os

from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..config import get_settings
from ..core.logging import debug, error, info, log_call, warning
from ..core.metrics_decorator import track_command_metrics
from ..help_texts import get_command_help_text
from ..router import router
from ..services.process_stream import stream_process_to_message

cmd_sessions: dict[int, dict] = {}
update_intervals: dict[int, float] = {}  # Хранит интервалы обновления для каждого чата


def _create_update_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой обновления для cmd сессий"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Обновить", callback_data="cmd_update")]]
    )


# Логика стриминга перенесена в services/process_stream.stream_process_to_message


@router.message(Command("cmd_session_start"))
@track_command_metrics("cmd_session_start")
@log_call("cmd_handler")
async def handle_cmd_session_start(message: Message) -> None:
    """Запуск новой cmd сессии"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    command_text = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None

    info(f"Пользователь {user_id} ({username}) запросил запуск cmd сессии в чате {chat_id}", "cmd_handler")
    if command_text:
        debug(f"Команда для выполнения: {command_text}", "cmd_handler")

    if chat_id in cmd_sessions and cmd_sessions[chat_id]["active"]:
        warning(f"Попытка запуска cmd сессии в чате {chat_id}, где уже есть активная сессия", "cmd_handler")
        await message.answer("ℹ️ Сессия уже активна. Используйте /cmd_session_stop для завершения")
        return

    shell_cmd = ["cmd.exe"] if os.name == "nt" else ["/bin/bash"]
    debug(f"Запуск оболочки: {shell_cmd}", "cmd_handler")
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        info(f"Оболочка успешно запущена для чата {chat_id}, PID: {proc.pid}", "cmd_handler")
    except Exception as e:
        error(f"Ошибка запуска оболочки в чате {chat_id}: {e}", "cmd_handler")
        logging.exception("Ошибка запуска оболочки в cmd_session_start")
        await message.answer(f"⚠️ Ошибка запуска оболочки: {e}")
        return

    msg = await message.answer("⌛ Запуск командной сессии...")
    session = {"process": proc, "last_message_id": msg.message_id, "active": True, "force_refresh": asyncio.Event()}
    cmd_sessions[chat_id] = session
    info(f"Cmd сессия создана для чата {chat_id}, message_id: {msg.message_id}", "cmd_handler")

    # Стартуем поток чтения и обновления
    asyncio.create_task(
        stream_process_to_message(
            chat_id=chat_id,
            message_id=msg.message_id,
            proc=proc,
            bot=message.bot,
            force_refresh_event=session["force_refresh"],
            session_storage=session,
        )
    )

    if command_text:
        try:
            proc.stdin.write((command_text + "\n").encode(get_settings().get_encoding()))  # type: ignore[attr-defined]
            await proc.stdin.drain()  # type: ignore[attr-defined]
            info(f"Команда '{command_text}' отправлена в cmd сессию чата {chat_id}", "cmd_handler")
        except Exception as e:
            error(f"Ошибка отправки команды '{command_text}' в чате {chat_id}: {e}", "cmd_handler")
            logging.exception("Ошибка отправки команды при запуске cmd_session_start")
            await message.answer(f"⚠️ Ошибка отправки команды: {e}")


@router.message(Command("cmd"))
@track_command_metrics("cmd")
@log_call("cmd_handler")
async def handle_cmd(message: Message) -> None:
    """Отправка команды в активную cmd сессию"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    command_text = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None

    info(f"Пользователь {user_id} ({username}) отправил команду в чат {chat_id}: {command_text}", "cmd_handler")

    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]["active"]:
        warning(f"Попытка отправить команду в неактивную cmd сессию в чате {chat_id}", "cmd_handler")
        await message.answer("ℹ️ Нет активной cmd сессии. Используйте /cmd_session_start для запуска")
        return

    if not command_text:
        warning(f"Пустая команда от пользователя {user_id} в чате {chat_id}", "cmd_handler")
        await message.answer(get_command_help_text("cmd"))
        return

    try:
        proc: asyncio.subprocess.Process = cmd_sessions[chat_id]["process"]
        proc.stdin.write((command_text + "\n").encode(get_settings().get_encoding()))  # type: ignore[attr-defined]
        await proc.stdin.drain()  # type: ignore[attr-defined]
        info(f"Команда '{command_text}' успешно отправлена в cmd сессию чата {chat_id}", "cmd_handler")
        await message.answer(f"⌨ Команда отправлена: {command_text}")
    except Exception as e:
        error(f"Ошибка отправки команды '{command_text}' в чате {chat_id}: {e}", "cmd_handler")
        logging.exception("Ошибка отправки команды в cmd")
        await message.answer(f"⚠️ Ошибка отправки команды: {e}")

@router.message(Command("cmd_session_stop"))
@log_call("cmd_handler")
async def handle_cmd_session_stop(message: Message) -> None:
    """Остановка cmd сессии"""
    chat_id = message.chat.id
    if chat_id in cmd_sessions:
        session = cmd_sessions[chat_id]
        if session["active"]:
            try:
                session["process"].terminate()
            except Exception:
                try:
                    session["process"].kill()
                except Exception:
                    pass
            session["active"] = False
            # Очищаем настройки интервала для этого чата
            if chat_id in update_intervals:
                del update_intervals[chat_id]
            await message.answer("⛔ Cmd сессия завершена")
        else:
            await message.answer("ℹ️ Нет активной cmd сессии")
    else:
        await message.answer("ℹ️ Нет активной cmd сессии")


@router.message(Command("cmdupdate"))
@log_call("cmd_handler")
async def handle_cmd_update(message: Message) -> None:
    """Обновить отображение активной cmd сессии"""
    chat_id = message.chat.id
    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]["active"]:
        await message.answer("ℹ️ Нет активной cmd сессии для обновления")
        return

    session = cmd_sessions[chat_id]
    try:
        # Устанавливаем флаг для принудительного обновления
        if "force_refresh" in session:
            session["force_refresh"].set()
        # Отвечаем только через callback, не спамим чат
        await message.answer("🔄 Обновление...", reply_to_message_id=message.message_id)
    except Exception as e:
        logging.exception("Ошибка обновления cmd сессии")
        await message.answer(f"⚠️ Ошибка обновления: {e}")


@router.callback_query(F.data == "cmd_update")
@log_call("cmd_handler")
async def handle_cmd_update_callback(callback: CallbackQuery) -> None:
    """Обработчик callback для кнопки обновления cmd сессии"""
    chat_id = callback.message.chat.id  # type: ignore[attr-defined]
    user_id = callback.from_user.id
    username = callback.from_user.username or "без username"

    info(f"Пользователь {user_id} ({username}) нажал кнопку обновления cmd сессии в чате {chat_id}", "cmd_handler")

    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]["active"]:
        warning(f"Попытка обновления неактивной cmd сессии в чате {chat_id}", "cmd_handler")
        await callback.answer("ℹ️ Нет активной cmd сессии", show_alert=True)
        return

    session = cmd_sessions[chat_id]
    try:
        # Устанавливаем флаг для принудительного обновления
        if "force_refresh" in session:
            session["force_refresh"].set()
            debug(f"Флаг force_refresh установлен для чата {chat_id}", "cmd_handler")
        info(f"Принудительное обновление cmd сессии запрошено в чате {chat_id}", "cmd_handler")
        await callback.answer("🔄 Принудительное обновление...")
    except Exception as e:
        error(f"Ошибка обновления cmd сессии через callback в чате {chat_id}: {e}", "cmd_handler")
        logging.exception("Ошибка обновления cmd сессии через callback")
        await callback.answer(f"⚠️ Ошибка: {e}", show_alert=True)


@router.message(Command("cmd_dump"))
@log_call("cmd_handler")
async def handle_cmd_dump(message: Message) -> None:
    """Отправить полный вывод cmd сессии файлом"""
    chat_id = message.chat.id
    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]["active"]:
        await message.answer("ℹ️ Нет активной cmd сессии для дампа")
        return

    # Получаем полный вывод из сессии (если доступен)
    session = cmd_sessions[chat_id]
    if "full_output" not in session:
        await message.answer("⚠️ Полный вывод недоступен. Попробуйте после выполнения команды.")
        return

    full_output = session["full_output"]
    if not full_output.strip():
        await message.answer("ℹ️ Вывод пуст")
        return

    try:
        # Создаем временный файл
        import tempfile
        from datetime import datetime

        from aiogram.types import FSInputFile

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            f.write("Полный вывод cmd сессии\n")
            f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'=' * 50}\n\n")
            f.write(full_output)
            temp_file_path = f.name

        # Отправляем файл
        file_input = FSInputFile(temp_file_path, filename="cmd_output.txt")
        await message.answer_document(file_input, caption="📄 Полный вывод cmd сессии")

        # Удаляем временный файл
        os.unlink(temp_file_path)

    except Exception as e:
        logging.exception("Ошибка создания дампа cmd сессии")
        await message.answer(f"⚠️ Ошибка создания дампа: {e}")


@router.message(F.text & ~F.text.startswith("/"))
@log_call("cmd_handler")
async def handle_session_text(message: Message) -> None:
    chat_id = message.chat.id
    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]["active"]:
        return
    try:
        proc: asyncio.subprocess.Process = cmd_sessions[chat_id]["process"]
        proc.stdin.write((message.text + "\n").encode(get_settings().get_encoding()))  # type: ignore[attr-defined]
        await proc.stdin.drain()  # type: ignore[attr-defined]
        await message.answer(f"⌨ Команда отправлена: {message.text}")
    except Exception as e:
        logging.exception("Ошибка отправки команды в handle_session_text")
        await message.answer(f"⚠️ Ошибка отправки команды: {e}")
