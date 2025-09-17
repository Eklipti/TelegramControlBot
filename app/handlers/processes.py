import os
import shlex
import subprocess
import sys
import time
import logging
from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from ..router import router
from ..paths_config import PATHS, save_paths


active_processes: dict[str, subprocess.Popen] = {}


@router.message(Command("on"))
async def handle_on(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        examples = (
            "Примеры использования:\n"
            "/on EvilBot\n"
            "/on \"C:/my bot.py\" --debug\n"
            "/on notepad.exe C:/file.txt\n"
            "/on hidden:EvilBot_ALT\n"
            "/on admin:cmd.exe\n"
            "/on explorer.exe C:/Windows"
        )
        await message.answer(f"❌ Укажите имя бота или путь к файлу\n\n{examples}")
        return

    input_arg = args[1].strip()
    hidden_mode = False
    admin_mode = False
    arguments: list[str] = []

    if input_arg.startswith("hidden:"):
        hidden_mode = True
        input_arg = input_arg[7:]
    elif input_arg.startswith("admin:"):
        admin_mode = True
        input_arg = input_arg[6:]

    if ' ' in input_arg:
        parts = input_arg.split(' ', 1)
        input_arg = parts[0]
        arguments = shlex.split(parts[1]) if ' ' in parts[1] else [parts[1]]

    file_path: str | None = None
    custom_path = False
    process_key: str | None = None
    new_path_found = False

    if input_arg in PATHS:
        if input_arg == "8k":
            for path in PATHS["8k"]:
                if os.path.exists(path):
                    file_path = path
                    break
        else:
            file_path = PATHS.get(input_arg)
        process_key = input_arg
    else:
        # Сначала проверяем, есть ли файл в PATH (исполняемые файлы)
        found = False
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            candidate = os.path.join(path_dir.strip('"'), input_arg)
            if os.path.exists(candidate):
                file_path = candidate
                custom_path = True
                process_key = os.path.abspath(file_path)
                found = True
                new_path_found = True
                break
        
        # Если не найден в PATH, проверяем как путь к файлу
        if not found:
            if not os.path.isabs(input_arg):
                # Для относительных путей сначала проверяем в текущей директории
                if os.path.exists(input_arg):
                    file_path = os.path.abspath(input_arg)
                    custom_path = True
                    process_key = file_path
                    new_path_found = True
                    found = True
                else:
                    # Если не найден, делаем абсолютным относительно рабочей директории
                    input_arg = os.path.abspath(input_arg)
            
            if not found and os.path.exists(input_arg):
                file_path = input_arg
                custom_path = True
                process_key = os.path.abspath(file_path)
                new_path_found = True
                found = True
        
        if not found:
            await message.answer(f"❌ Файл не найден: {input_arg}")
            return

    assert file_path is not None and process_key is not None

    if process_key in active_processes:
        proc = active_processes[process_key]
        if proc.poll() is None:
            await message.answer(f"ℹ️ Процесс уже запущен: {process_key}")
            return
        del active_processes[process_key]

    working_dir = os.path.dirname(file_path)
    cmd: list[str] = []
    creationflags = 0

    try:
        if os.name == 'nt':
            if hidden_mode:
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = subprocess.CREATE_NEW_CONSOLE
            if admin_mode:
                await message.answer("⚠️ Режим admin требует локального подтверждения UAC и может не сработать из Telegram.")
                if file_path.lower().endswith('.py'):
                    cmd = ["runas", "/user:Administrator", sys.executable, file_path]
                else:
                    cmd = ["runas", "/user:Administrator", file_path]
                cmd.extend(arguments)
            else:
                if file_path.lower().endswith('.py'):
                    cmd = [sys.executable, file_path]
                    cmd.extend(arguments)
                else:
                    cmd = [file_path]
                    cmd.extend(arguments)
        else:
            if file_path.lower().endswith('.py'):
                cmd = [sys.executable, file_path]
            else:
                cmd = [file_path]
            cmd.extend(arguments)
            if admin_mode:
                await message.answer("⚠️ sudo без TTY/пароля может подвиснуть; запуск не гарантируется.")
                cmd = ["sudo"] + cmd

        proc = subprocess.Popen(cmd, cwd=working_dir, creationflags=creationflags)
        active_processes[process_key] = proc
        reply_msg = f"✅ Успешно запущен: {os.path.basename(file_path)}"
        if custom_path:
            reply_msg += f"\n📁 Путь: {file_path}"
        if arguments:
            reply_msg += f"\n⚙️ Аргументы: {' '.join(arguments)}"
        if hidden_mode:
            reply_msg += "\n👻 Режим: скрытый"
        if admin_mode:
            reply_msg += "\n🛡️ Режим: администратор"

        if new_path_found and input_arg not in PATHS:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💾 Сохранить путь", callback_data=f"save_path:{input_arg}:{file_path}")]
            ])
            await message.answer(reply_msg, reply_markup=markup)
        else:
            await message.answer(reply_msg)
    except Exception as e:
        logging.exception("Ошибка запуска процесса")
        err = str(e)
        error_msg = f"⚠️ Ошибка запуска: len={len(err)}, first='{err[0] if err else ''}', last='{err[-1] if err else ''}'"
        if os.name == 'nt':
            if "не является приложением Win32" in str(e):
                try:
                    os.startfile(file_path)  # type: ignore[attr-defined]
                    await message.answer(f"✅ Запущено через ассоциированную программу: {file_path}")
                    return
                except Exception as startfile_error:
                    logging.exception("Ошибка при запуске через ассоциацию")
                    error_msg += f"\nℹ️ Ошибка при запуске через ассоциацию: {startfile_error}"
        await message.answer(error_msg)


@router.message(Command("processes"))
async def handle_processes(message: Message) -> None:
    if not active_processes:
        await message.answer("ℹ️ Нет активных процессов")
        return
    response = "🖥️ Активные процессы:\n\n"
    for name, proc in active_processes.items():
        status = "🟢 Активен" if proc.poll() is None else "⚪ Завершен"
        pid_line = f"PID: {proc.pid}" if proc.pid else "PID: N/A"
        response += (
            f"🔹 <b>{os.path.basename(name)}</b>\n"
            f"• Статус: {status}\n"
            f"• {pid_line}\n"
            f"• Путь: {name}\n\n"
        )
    await message.answer(response)


@router.message(Command("off"))
async def handle_off(message: Message) -> None:
    args = message.text.split()
    if len(args) < 2:
        active_list = []
        for name, proc in active_processes.items():
            status = "🟢 Активен" if proc.poll() is None else "⚪ Завершен"
            active_list.append(f"- {name} ({status})")
        response = "📋 Активные процессы:\n" + ("\n".join(active_list) if active_list else "ℹ️ Нет активных процессов")
        response += "\n\nℹ️ Используйте /off <имя> или /off all"
        await message.answer(response)
        return

    target = args[1].strip()
    if target.lower() == "all":
        stopped: list[str] = []
        failed: list[str] = []
        for name, proc in list(active_processes.items()):
            if proc.poll() is None:
                try:
                    if os.name == 'nt':
                        subprocess.call(f'taskkill /F /T /PID {proc.pid}', shell=True)
                    else:
                        proc.terminate()
                    stopped.append(name)
                except Exception as e:
                    logging.exception(f"Ошибка остановки процесса {name}")
                    failed.append(f"{name}: {e}")
                finally:
                    active_processes.pop(name, None)
        response = "⛔ Остановлены:\n" + ("\n".join(stopped) if stopped else "ℹ️ Нет процессов для остановки")
        if failed:
            response += "\n\n❌ Ошибки:\n" + "\n".join(failed)
        await message.answer(response)
        return

    matched_proc: subprocess.Popen | None = None
    matched_name: str | None = None
    if target.isdigit():
        pid = int(target)
        for name, proc in active_processes.items():
            if proc.pid == pid:
                matched_proc = proc
                matched_name = name
                break
    if not matched_proc:
        target_lower = target.lower()
        for name, proc in active_processes.items():
            if name.lower() == target_lower:
                matched_proc = proc
                matched_name = name
                break
    if not matched_proc or not matched_name:
        await message.answer(f"❌ Процесс '{target}' не найден")
        return
    if matched_proc.poll() is not None:
        active_processes.pop(matched_name, None)
        await message.answer(f"ℹ️ Процесс '{matched_name}' уже завершен")
        return
    try:
        if os.name == 'nt':
            subprocess.call(f'taskkill /F /T /PID {matched_proc.pid}', shell=True)
            time.sleep(1)
            if matched_proc.poll() is None:
                matched_proc.kill()
        else:
            matched_proc.terminate()
        active_processes.pop(matched_name, None)
        await message.answer(f"⛔ Процесс '{matched_name}' (PID: {matched_proc.pid}) остановлен")
    except Exception as e:
        logging.exception(f"Ошибка остановки процесса {matched_name}")
        await message.answer(f"⚠️ Ошибка остановки: {e}")


@router.callback_query(F.data.startswith('save_path'))
async def handle_save_path_callback(call: CallbackQuery) -> None:
    try:
        _, name, path = call.data.split(':', 2)
        PATHS[name] = path
        save_paths(PATHS)
        await call.message.edit_text(f"✅ Путь сохранен: {name} → {path}")
    except Exception:
        logging.exception("Ошибка сохранения пути")
        await call.answer("Ошибка сохранения", show_alert=True)



