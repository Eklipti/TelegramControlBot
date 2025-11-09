# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import ctypes
import logging
import os
import shlex
import subprocess
import sys

from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..config.paths import get_paths_config
from ..core.logging import error, info, warning
from ..router import router

active_processes: dict[str, subprocess.Popen] = {}


@router.message(Command("on"))
async def handle_on(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        examples = (
            "Примеры использования:\n"
            "/on EvilBot\n"
            "/on cmd /K\n"
            "/on powershell -NoExit\n"
            '/on "C:/my bot.py" --debug\n'
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

    if " " in input_arg:
        parts = input_arg.split(" ", 1)
        input_arg = parts[0]
        arguments = shlex.split(parts[1]) if " " in parts[1] else [parts[1]]

    file_path: str | None = None
    custom_path = False
    process_key: str | None = None
    new_path_found = False

    config = get_paths_config()
    user_id = message.from_user.id
    all_paths = config.get_all_paths(user_id)

    if input_arg in all_paths:
        if input_arg == "8k":
            for path in all_paths["8k"]:
                if os.path.exists(path):
                    file_path = path
                    break
        else:
            file_path = all_paths.get(input_arg)
        process_key = input_arg
    else:
        # DEFAULT_PATHS.json уже содержит весь системный PATH,
        # но на всякий случай проверяем системные директории для базовых команд
        found = False
        
        # Для Windows проверяем стандартные системные команды
        if os.name == "nt" and not os.path.isabs(input_arg):
            system_dirs = [
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SysWOW64"),
            ]
            for sys_dir in system_dirs:
                for ext in [".exe", ".cmd", ".bat"]:
                    candidate = os.path.join(sys_dir, input_arg if input_arg.lower().endswith(ext) else input_arg + ext)
                    if os.path.exists(candidate):
                        file_path = candidate
                        custom_path = True
                        process_key = os.path.abspath(file_path)
                        new_path_found = True
                        found = True
                        info(f"Найдена системная команда: {file_path}", "processes")
                        break
                if found:
                    break
        
        # Проверяем как прямой путь к файлу
        if not found and not os.path.isabs(input_arg):
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
            await message.answer(f"❌ Файл не найден: {input_arg}\n\nℹ️ Используйте имя из сохраненных путей (/paths) или полный путь к файлу")
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
        if os.name == "nt":
            if hidden_mode:
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = subprocess.CREATE_NEW_CONSOLE
            if admin_mode:
                await message.answer("⚠️ Режим admin требует локального подтверждения UAC.")
                # Используем ShellExecute с "runas" для вызова UAC диалога
                try:
                    # Формируем команду и параметры
                    if file_path.lower().endswith(".py"):
                        executable = sys.executable
                        params = f'"{file_path}"'
                        if arguments:
                            params += " " + " ".join(f'"{arg}"' if " " in arg else arg for arg in arguments)
                    else:
                        executable = file_path
                        params = " ".join(f'"{arg}"' if " " in arg else arg for arg in arguments) if arguments else ""
                    
                    # ShellExecute для UAC
                    # SW_SHOWNORMAL = 1 (нормальное окно), SW_HIDE = 0 (скрытое)
                    show_cmd = 0 if hidden_mode else 1
                    
                    result = ctypes.windll.shell32.ShellExecuteW(
                        None,           # hwnd
                        "runas",        # lpVerb - запуск от имени администратора
                        executable,     # lpFile
                        params,         # lpParameters
                        working_dir,    # lpDirectory
                        show_cmd        # nShowCmd
                    )
                    
                    # ShellExecute возвращает значение > 32 при успехе
                    if result <= 32:
                        await message.answer(f"❌ Ошибка запуска с правами администратора. Код: {result}")
                        return
                    
                    info(f"Процесс запущен с правами администратора: {file_path}", "processes")
                    
                    # Формируем ответное сообщение
                    reply_msg = f"✅ Успешно запущен: {os.path.basename(file_path)}"
                    if custom_path:
                        reply_msg += f"\n📁 Путь: {file_path}"
                    if arguments:
                        reply_msg += f"\n⚙️ Аргументы: {' '.join(arguments)}"
                    if hidden_mode:
                        reply_msg += "\n👻 Режим: скрытый"
                    reply_msg += "\n🛡️ Режим: администратор (UAC требует подтверждения)"
                    
                    if new_path_found and input_arg not in all_paths:
                        markup = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="💾 Сохранить путь", callback_data=f"save_path:{input_arg}:{file_path}")]
                            ]
                        )
                        await message.answer(reply_msg, reply_markup=markup)
                    else:
                        await message.answer(reply_msg)
                    return
                    
                except Exception as e:
                    error(f"Ошибка при вызове ShellExecute: {e}", "processes")
                    await message.answer(f"❌ Ошибка запуска с правами администратора: {e}")
                    return
            else:
                if file_path.lower().endswith(".py"):
                    cmd = [sys.executable, file_path]
                    cmd.extend(arguments)
                else:
                    cmd = [file_path]
                    cmd.extend(arguments)
        else:
            if file_path.lower().endswith(".py"):
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
            reply_msg += "\n🛡️ Режим: администратор (UAC требует подтверждения)"

        if new_path_found and input_arg not in all_paths:
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="💾 Сохранить путь", callback_data=f"save_path:{input_arg}:{file_path}")]
                ]
            )
            await message.answer(reply_msg, reply_markup=markup)
        else:
            await message.answer(reply_msg)
    except Exception as e:
        logging.exception("Ошибка запуска процесса")
        err = str(e)
        error_msg = (
            f"⚠️ Ошибка запуска: len={len(err)}, first='{err[0] if err else ''}', last='{err[-1] if err else ''}'"  # noqa: E501
        )
        if os.name == "nt":
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
        response += f"🔹 <b>{os.path.basename(name)}</b>\n• Статус: {status}\n• {pid_line}\n• Путь: {name}\n\n"
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
        response += "\n\nℹ️ Используйте /off &lt;название&gt; или /off all"
        try:
            await message.answer(response)
        except Exception as e:
            error(f"Ошибка отправки сообщения в handle_off: {e}", "error")
            # Отправляем упрощенное сообщение без HTML-тегов
            simple_response = "📋 Активные процессы:\n" + ("\n".join(active_list) if active_list else "ℹ️ Нет активных процессов")
            simple_response += "\n\nℹ️ Используйте /off &lt;название&gt; или /off all"
            await message.answer(simple_response)
        return

    target = args[1].strip()
    if target.lower() == "all":
        from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager

        manager = get_confirmation_manager()
        action_config = DANGEROUS_ACTIONS["process_stop_all"]

        await manager.create_confirmation(
            chat_id=message.chat.id,
            action_type="process_stop_all",
            action_data={"action_type": "process_stop_all", "action_data": {"target": "all"}},
            warning_message=action_config["warning"],
            timeout=action_config["timeout"],
        )
        return

    # Проверяем, существует ли процесс
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

    from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager

    manager = get_confirmation_manager()
    action_config = DANGEROUS_ACTIONS["process_stop"]

    await manager.create_confirmation(
        chat_id=message.chat.id,
        action_type="process_stop",
        action_data={"action_type": "process_stop", "action_data": {"target": target}, "target": target},
        warning_message=action_config["warning"].format(
            action_data=f"Остановка процесса: {matched_name} (PID: {matched_proc.pid})"
        ),  # noqa: E501
        timeout=action_config["timeout"],
    )


@router.callback_query(F.data.startswith("save_path"))
async def handle_save_path_callback(call: CallbackQuery) -> None:
    try:
        _, name, path = call.data.split(":", 2)
        config = get_paths_config()
        user_id = call.from_user.id
        if config.add_user_path(user_id, name, path):
            await call.message.edit_text(f"✅ Путь сохранен: {name} → {path}")
        else:
            await call.answer("Ошибка: путь не существует", show_alert=True)
    except Exception:
        logging.exception("Ошибка сохранения пути")
        await call.answer("Ошибка сохранения", show_alert=True)
