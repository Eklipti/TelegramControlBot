# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import html
import logging
import os

from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..config import get_encoding
from ..router import router

cmd_sessions: dict[int, dict] = {}
update_intervals: dict[int, float] = {}  # Хранит интервалы обновления для каждого чата


def _create_update_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой обновления для cmd сессий"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="cmd_update")]
    ])


async def _read_stream_and_update(chat_id: int, message_id: int, proc: asyncio.subprocess.Process, bot) -> None:
    encoding = get_encoding()
    full_output = ""
    start_time = asyncio.get_event_loop().time()
    last_update = start_time
    line_count = 0
    buffer = b""
    BATCH_SIZE = 512  # Читаем по 512 байт за раз
    # Получаем ссылку на force_refresh событие и инициализируем full_output в сессии
    force_refresh = None
    if chat_id in cmd_sessions:
        force_refresh = cmd_sessions[chat_id].get('force_refresh')
        cmd_sessions[chat_id]['full_output'] = ""  # Инициализируем для доступа через cmd_dump

    try:
        while True:
            # Проверяем force_refresh событие
            should_force_update = False
            if force_refresh and force_refresh.is_set():
                force_refresh.clear()
                should_force_update = True

            # Читаем батч данных
            chunk = await proc.stdout.read(BATCH_SIZE)  # type: ignore[attr-defined]
            if not chunk:
                if proc.returncode is not None:
                    break
                # Если нет данных, но есть force_refresh, делаем обновление
                if should_force_update:
                    current_time = asyncio.get_event_loop().time()
                    elapsed = int(current_time - start_time)
                    status_bar = f"⏱️ {elapsed}s | 📜 {line_count} lines"
                    # Обрезка по строкам вместо символов
                    lines = full_output.split('\n')
                    display_lines = lines[-50:] if len(lines) > 50 else lines  # Показываем последние 50 строк
                    display_output = html.escape('\n'.join(display_lines))
                    message_content = f"<code>{status_bar}\n{'-'*20}\n{display_output}</code>"
                    try:
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=message_content,
                            reply_markup=_create_update_keyboard()
                        )
                    except Exception:
                        pass
                    last_update = current_time
                await asyncio.sleep(0.01)  # Небольшая пауза при отсутствии данных
                continue

            buffer += chunk
            current_time = asyncio.get_event_loop().time()

            # Декодируем буфер по частям, чтобы не потерять данные на границе символов
            try:
                text = buffer.decode(encoding, errors='replace')
                buffer = b""  # Очищаем буфер после успешного декодирования
            except UnicodeDecodeError:
                # Если не удалось декодировать весь буфер, оставляем последние несколько байт
                # для следующей итерации (на случай, если символ разбит между батчами)
                if len(buffer) > 4:
                    text = buffer[:-4].decode(encoding, errors='replace')
                    buffer = buffer[-4:]
                else:
                    text = ""

            if text:
                full_output += text
                line_count += text.count('\n')
                # Сохраняем в сессии для доступа через cmd_dump
                if chat_id in cmd_sessions:
                    cmd_sessions[chat_id]['full_output'] = full_output

            # Обновляем сообщение не чаще UPDATE_INTERVAL секунд или при force_refresh
            # Читаем актуальный интервал на каждой итерации
            current_interval = update_intervals.get(chat_id, 0.25)
            if current_time - last_update >= current_interval or should_force_update:
                # Небольшая задержка для накопления вывода
                await asyncio.sleep(0.1)

                elapsed = int(current_time - start_time)
                status_bar = f"⏱️ {elapsed}s | 📜 {line_count} lines"
                # Обрезка по строкам вместо символов
                lines = full_output.split('\n')
                display_lines = lines[-50:] if len(lines) > 50 else lines  # Показываем последние 50 строк
                display_output = html.escape('\n'.join(display_lines))
                message_content = f"<code>{status_bar}\n{'-'*20}\n{display_output}</code>"
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=message_content,
                        reply_markup=_create_update_keyboard()
                    )
                except Exception:
                    pass
                last_update = current_time
    finally:
        # Обрабатываем оставшийся буфер
        if buffer:
            try:
                text = buffer.decode(encoding, errors='replace')
                full_output += text
                line_count += text.count('\n')
                # Сохраняем в сессии для доступа через cmd_dump
                if chat_id in cmd_sessions:
                    cmd_sessions[chat_id]['full_output'] = full_output
            except Exception:
                logging.exception("Ошибка обновления сообщения в cmd")
                pass

        exit_code = proc.returncode
        if exit_code is None:
            exit_code = await proc.wait()
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        status = "✅ Успешно" if exit_code == 0 else f"❌ Ошибка (код: {exit_code})"
        # Обрезка по строкам для финального сообщения (показываем последние 100 строк)
        lines = full_output.split('\n')
        final_lines = lines[-100:] if len(lines) > 100 else lines
        final_output = html.escape('\n'.join(final_lines))
        result_message = (
            f"<code>{status} | ⏱️ {elapsed}s | 📜 {line_count} lines\n"
            f"{'-'*20}\n"
            f"{final_output}</code>"
        )
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=result_message,
                reply_markup=_create_update_keyboard()
            )
        except Exception:
            logging.exception("Ошибка финального обновления сообщения в cmd")
            await bot.send_message(chat_id, result_message, reply_markup=_create_update_keyboard())
        if chat_id in cmd_sessions and cmd_sessions[chat_id]['process'] == proc:
            del cmd_sessions[chat_id]


@router.message(Command("cmd_session_start"))
async def handle_cmd_session_start(message: Message) -> None:
    """Запуск новой cmd сессии"""
    chat_id = message.chat.id
    command_text = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None

    if chat_id in cmd_sessions and cmd_sessions[chat_id]['active']:
        await message.answer("ℹ️ Сессия уже активна. Используйте /cmd_session_stop для завершения")
        return

    shell_cmd = ['cmd.exe'] if os.name == 'nt' else ['/bin/bash']
    try:
        proc = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except Exception as e:
        logging.exception("Ошибка запуска оболочки в cmd_session_start")
        await message.answer(f"⚠️ Ошибка запуска оболочки: {e}")
        return

    msg = await message.answer("⌛ Запуск командной сессии...")
    session = {
        "process": proc,
        "last_message_id": msg.message_id,
        "active": True,
        "force_refresh": asyncio.Event()
    }
    cmd_sessions[chat_id] = session

    asyncio.create_task(_read_stream_and_update(chat_id, msg.message_id, proc, message.bot))

    if command_text:
        try:
            proc.stdin.write((command_text + '\n').encode(get_encoding()))  # type: ignore[attr-defined]
            await proc.stdin.drain()  # type: ignore[attr-defined]
        except Exception as e:
            logging.exception("Ошибка отправки команды при запуске cmd_session_start")
            await message.answer(f"⚠️ Ошибка отправки команды: {e}")


@router.message(Command("cmd"))
async def handle_cmd(message: Message) -> None:
    """Отправка команды в активную cmd сессию"""
    chat_id = message.chat.id
    command_text = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None

    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]['active']:
        await message.answer("ℹ️ Нет активной cmd сессии. Используйте /cmd_session_start для запуска")
        return

    if not command_text:
        await message.answer("ℹ️ Укажите команду: /cmd [команда]")
        return

    try:
        proc: asyncio.subprocess.Process = cmd_sessions[chat_id]['process']
        proc.stdin.write((command_text + '\n').encode(get_encoding()))  # type: ignore[attr-defined]
        await proc.stdin.drain()  # type: ignore[attr-defined]
        await message.answer(f"⌨ Команда отправлена: {command_text}")
    except Exception as e:
        logging.exception("Ошибка отправки команды в cmd")
        await message.answer(f"⚠️ Ошибка отправки команды: {e}")


@router.message(Command("cmd_wait"))
async def handle_cmd_wait(message: Message) -> None:
    """Настройка интервала автообновления cmd сессии"""
    chat_id = message.chat.id
    args = message.text.split(maxsplit=2)

    if len(args) < 2:
        await message.answer("ℹ️ Используйте: /cmd_wait [интервал_секунды] [команда]\nПример: /cmd_wait 1.0 dir")
        return

    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]['active']:
        await message.answer("ℹ️ Нет активной cmd сессии. Используйте /cmd_session_start для запуска")
        return

    try:
        interval_seconds = float(args[1])
        if interval_seconds < 0.25:
            await message.answer("⚠️ Минимальный интервал обновления: 0.25 секунды")
            return
        if interval_seconds > 60:
            await message.answer("⚠️ Максимальный интервал обновления: 60 секунд")
            return
    except ValueError:
        await message.answer("⚠️ Неверный формат времени. Используйте число (например: 1.0)")
        return

    # Устанавливаем новый интервал обновления
    update_intervals[chat_id] = interval_seconds

    # Если есть команда, выполняем её
    if len(args) > 2:
        command_text = args[2]
        try:
            proc: asyncio.subprocess.Process = cmd_sessions[chat_id]['process']
            proc.stdin.write((command_text + '\n').encode(get_encoding()))  # type: ignore[attr-defined]
            await proc.stdin.drain()  # type: ignore[attr-defined]
            await message.answer(f"⌨ Команда отправлена: {command_text}")
        except Exception as e:
            logging.exception("Ошибка отправки команды в cmd_wait")
            await message.answer(f"⚠️ Ошибка отправки команды: {e}")

    await message.answer(f"⚙️ Интервал автообновления установлен: {interval_seconds} сек")


@router.message(Command("cmd_session_stop"))
async def handle_cmd_session_stop(message: Message) -> None:
    """Остановка cmd сессии"""
    chat_id = message.chat.id
    if chat_id in cmd_sessions:
        session = cmd_sessions[chat_id]
        if session['active']:
            try:
                session['process'].terminate()
            except Exception:
                try:
                    session['process'].kill()
                except Exception:
                    pass
            session['active'] = False
            # Очищаем настройки интервала для этого чата
            if chat_id in update_intervals:
                del update_intervals[chat_id]
            await message.answer("⛔ Cmd сессия завершена")
        else:
            await message.answer("ℹ️ Нет активной cmd сессии")
    else:
        await message.answer("ℹ️ Нет активной cmd сессии")




@router.message(Command("cmdupdate"))
async def handle_cmd_update(message: Message) -> None:
    """Обновить отображение активной cmd сессии"""
    chat_id = message.chat.id
    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]['active']:
        await message.answer("ℹ️ Нет активной cmd сессии для обновления")
        return

    session = cmd_sessions[chat_id]
    try:
        # Устанавливаем флаг для принудительного обновления
        if 'force_refresh' in session:
            session['force_refresh'].set()
        # Отвечаем только через callback, не спамим чат
        await message.answer("🔄 Обновление...", reply_to_message_id=message.message_id)
    except Exception as e:
        logging.exception("Ошибка обновления cmd сессии")
        await message.answer(f"⚠️ Ошибка обновления: {e}")


@router.callback_query(F.data == "cmd_update")
async def handle_cmd_update_callback(callback: CallbackQuery) -> None:
    """Обработчик callback для кнопки обновления cmd сессии"""
    chat_id = callback.message.chat.id  # type: ignore[attr-defined]

    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]['active']:
        await callback.answer("ℹ️ Нет активной cmd сессии", show_alert=True)
        return

    session = cmd_sessions[chat_id]
    try:
        # Устанавливаем флаг для принудительного обновления
        if 'force_refresh' in session:
            session['force_refresh'].set()
        await callback.answer("🔄 Принудительное обновление...")
    except Exception as e:
        logging.exception("Ошибка обновления cmd сессии через callback")
        await callback.answer(f"⚠️ Ошибка: {e}", show_alert=True)


@router.message(Command("cmd_dump"))
async def handle_cmd_dump(message: Message) -> None:
    """Отправить полный вывод cmd сессии файлом"""
    chat_id = message.chat.id
    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]['active']:
        await message.answer("ℹ️ Нет активной cmd сессии для дампа")
        return

    # Получаем полный вывод из сессии (если доступен)
    # Поскольку full_output находится в локальной переменной функции _read_stream_and_update,
    # нам нужно сохранять его в сессии для доступа
    session = cmd_sessions[chat_id]
    if 'full_output' not in session:
        await message.answer("⚠️ Полный вывод недоступен. Попробуйте после выполнения команды.")
        return

    full_output = session['full_output']
    if not full_output.strip():
        await message.answer("ℹ️ Вывод пуст")
        return

    try:
        # Создаем временный файл
        import os
        import tempfile
        from datetime import datetime

        from aiogram.types import FSInputFile

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            f.write("Полный вывод cmd сессии\n")
            f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
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


@router.message(F.text & ~F.text.startswith('/'))
async def handle_session_text(message: Message) -> None:
    chat_id = message.chat.id
    if chat_id not in cmd_sessions or not cmd_sessions[chat_id]['active']:
        return
    try:
        proc: asyncio.subprocess.Process = cmd_sessions[chat_id]['process']
        proc.stdin.write((message.text + '\n').encode(get_encoding()))  # type: ignore[attr-defined]
        await proc.stdin.drain()  # type: ignore[attr-defined]
        await message.answer(f"⌨ Команда отправлена: {message.text}")
    except Exception as e:
        logging.exception("Ошибка отправки команды в handle_session_text")
        await message.answer(f"⚠️ Ошибка отправки команды: {e}")



