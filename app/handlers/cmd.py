import asyncio
import html
import os
import sys
import logging
from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message

from ..router import router
from ..config import get_encoding


cmd_sessions: dict[int, dict] = {}


async def _read_stream_and_update(chat_id: int, message_id: int, proc: asyncio.subprocess.Process, bot) -> None:
    encoding = get_encoding()
    full_output = ""
    start_time = asyncio.get_event_loop().time()
    last_update = start_time
    line_count = 0
    buffer = b""
    BATCH_SIZE = 512  # Читаем по 512 байт за раз
    UPDATE_INTERVAL = 0.25  # Обновляем не чаще 4 раз в секунду

    try:
        while True:
            # Читаем батч данных
            chunk = await proc.stdout.read(BATCH_SIZE)  # type: ignore[attr-defined]
            if not chunk:
                if proc.returncode is not None:
                    break
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
            
            # Обновляем сообщение не чаще UPDATE_INTERVAL секунд
            if current_time - last_update >= UPDATE_INTERVAL:
                # Небольшая задержка для накопления вывода
                await asyncio.sleep(0.1)
                
                elapsed = int(current_time - start_time)
                status_bar = f"⏱️ {elapsed}s | 📜 {line_count} lines"
                display_output = html.escape(full_output[-1000:])
                message_content = f"<code>{status_bar}\n{'-'*20}\n{display_output}</code>"
                try:
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_content)
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
            except Exception:
                logging.exception("Ошибка обновления сообщения в cmd")
                pass
        
        exit_code = proc.returncode
        if exit_code is None:
            exit_code = await proc.wait()
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        status = "✅ Успешно" if exit_code == 0 else f"❌ Ошибка (код: {exit_code})"
        result_message = (
            f"<code>{status} | ⏱️ {elapsed}s | 📜 {line_count} lines\n"
            f"{'-'*20}\n"
            f"{html.escape(full_output[-3000:])}</code>"
        )
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=result_message)
        except Exception:
            logging.exception("Ошибка финального обновления сообщения в cmd")
            await bot.send_message(chat_id, result_message)
        if chat_id in cmd_sessions and cmd_sessions[chat_id]['process'] == proc:
            del cmd_sessions[chat_id]


@router.message(Command("cmd"))
async def handle_cmd(message: Message) -> None:
    chat_id = message.chat.id
    command_text = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None

    if chat_id in cmd_sessions and cmd_sessions[chat_id]['active']:
        if command_text:
            try:
                proc: asyncio.subprocess.Process = cmd_sessions[chat_id]['process']
                proc.stdin.write((command_text + '\n').encode(get_encoding()))  # type: ignore[attr-defined]
                await proc.stdin.drain()  # type: ignore[attr-defined]
                await message.answer(f"⌨ Команда отправлена: {command_text}")
            except Exception as e:
                logging.exception("Ошибка отправки команды в cmd")
                await message.answer(f"⚠️ Ошибка отправки команды: {e}")
        else:
            await message.answer("ℹ️ Сессия активна. Отправьте команду текстом или используйте /newcmd")
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
        logging.exception("Ошибка запуска оболочки в cmd")
        await message.answer(f"⚠️ Ошибка запуска оболочки: {e}")
        return

    msg = await message.answer("⌛ Запуск командной сессии...")
    session = {"process": proc, "last_message_id": msg.message_id, "active": True}
    cmd_sessions[chat_id] = session

    asyncio.create_task(_read_stream_and_update(chat_id, msg.message_id, proc, message.bot))

    if command_text:
        try:
            proc.stdin.write((command_text + '\n').encode(get_encoding()))  # type: ignore[attr-defined]
            await proc.stdin.drain()  # type: ignore[attr-defined]
        except Exception as e:
            logging.exception("Ошибка отправки команды при запуске cmd")
            await message.answer(f"⚠️ Ошибка отправки команды: {e}")


@router.message(Command("newcmd"))
async def handle_newcmd(message: Message) -> None:
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
    await handle_cmd(message)


@router.message(Command("end_session"))
async def handle_end_session(message: Message) -> None:
    chat_id = message.chat.id
    if chat_id in cmd_sessions:
        session = cmd_sessions[chat_id]
        if session['active']:
            try:
                session['process'].terminate()
            except Exception:
                logging.exception("Ошибка при завершении процесса в end_session")
                try:
                    session['process'].kill()
                except Exception:
                    logging.exception("Ошибка при принудительном завершении процесса в end_session")
                    pass
            session['active'] = False
            await message.answer("⛔ Сессия завершена")
        else:
            await message.answer("ℹ️ Нет активной сессии")
    else:
        await message.answer("ℹ️ Нет активной сессии")


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



