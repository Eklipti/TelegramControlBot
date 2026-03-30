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

import ctypes
import logging
import os
import shlex
import subprocess
import uuid

from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..config.paths import get_paths_config
from ..core.logging import error, info
from ..help_texts import get_command_help_text
from ..router import router
from ..state import path_save_requests

active_processes: dict[str, subprocess.Popen] = {}


@router.message(Command("on"))
async def handle_on(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(get_command_help_text("on"))
        return

    input_arg = args[1].strip()
    hidden_mode = False
    admin_mode = False
    arguments: list[str] = []

    # Обработка префиксов
    if input_arg.startswith("hidden:"):
        hidden_mode = True
        input_arg = input_arg[7:]
    elif input_arg.startswith("admin:"):
        admin_mode = True
        input_arg = input_arg[6:]

    # Разделение на команду и аргументы
    if " " in input_arg:
        parts = input_arg.split(" ", 1)
        input_arg = parts[0]
        # shlex.split корректно обрабатывает кавычки
        arguments = shlex.split(parts[1]) if " " in parts[1] else [parts[1]]

    # Поиск файла 
    file_path: str | None = None
    custom_path = False
    process_key: str | None = None
    new_path_found = False

    config = get_paths_config()
    user_id = message.from_user.id
    all_paths = config.get_all_paths(user_id)

    # Ищем в сохраненных путях
    if input_arg in all_paths:
        # берем первый существующий
        val = all_paths.get(input_arg)
        if isinstance(val, list):
            for v in val:
                if os.path.exists(str(v)):
                    file_path = str(v)
                    break
        else:
            file_path = str(val)
        process_key = input_arg
    else:
        # Ищем как прямой путь или системную команду
        found = False
        
        # Проверка стандартных путей Windows (System32 и т.д.)
        if not os.path.isabs(input_arg):
            system_dirs = [
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SysWOW64"),
                os.getcwd() # Текущая папка бота
            ]
            # Список расширений, которые пробуем подставить
            extensions = ["", ".exe", ".bat", ".cmd", ".com", ".lnk"]
            
            for sys_dir in system_dirs:
                for ext in extensions:
                    # Если расширение уже есть, не дублируем его
                    if ext and input_arg.lower().endswith(ext):
                        candidate = os.path.join(sys_dir, input_arg)
                    else:
                        candidate = os.path.join(sys_dir, input_arg + ext)
                    
                    if os.path.exists(candidate):
                        file_path = candidate
                        custom_path = True
                        process_key = os.path.abspath(file_path)
                        new_path_found = True
                        found = True
                        break
                if found:
                    break
        
        # Если всё ещё не нашли, пробуем как абсолютный путь
        if not found:
            abs_candidate = os.path.abspath(input_arg)
            if os.path.exists(abs_candidate):
                file_path = abs_candidate
                custom_path = True
                process_key = file_path
                new_path_found = True
                found = True

        if not found:
            await message.answer(f"❌ Файл не найден: {input_arg}")
            return

    # Проверка на повторный запуск
    assert file_path is not None and process_key is not None

    if process_key in active_processes:
        proc = active_processes[process_key]
        if proc.poll() is None:
            await message.answer(f"ℹ️ Процесс уже запущен: {process_key}")
            return
        del active_processes[process_key]

    # Запуск
    working_dir = os.path.dirname(file_path)
    
    # Подготовка сообщения об успехе
    reply_msg_base = f"✅ Успешно запущен: {os.path.basename(file_path)}"
    if custom_path:
        reply_msg_base += f"\n📁 Путь: {file_path}"
    if arguments:
        reply_msg_base += f"\n⚙️ Аргументы: {' '.join(arguments)}"
    if hidden_mode:
        reply_msg_base += "\n👻 Режим: скрытый"

    # Кнопка сохранения
    markup = None
    if new_path_found and input_arg not in all_paths:
        request_id = str(uuid.uuid4())[:8]
        alias_name = os.path.basename(input_arg)
        path_save_requests[request_id] = (alias_name, file_path)
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"💾 Сохранить как '{alias_name}'", callback_data=f"save_path:{request_id}")]
            ]
        )

    try:
        if admin_mode:
            await message.answer("⚠️ Запрос прав администратора (подтвердите UAC на экране)...")
            
            # Собираем параметры в одну строку для ShellExecute
            params_str = ""
            if arguments:
                # Оборачиваем в кавычки аргументы с пробелами
                params_str = " ".join(f'"{a}"' if " " in a else a for a in arguments)

            # 0 = SW_HIDE, 1 = SW_SHOWNORMAL
            show_cmd = 0 if hidden_mode else 1
            
            # ShellExecute сам разберется с типами файлов
            result = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",      # Verb: запуск от админа
                file_path,    # File: путь к файлу (exe, bat, py, txt...)
                params_str,   # Params
                working_dir,  # Directory
                show_cmd      # ShowCmd
            )
            
            # Если результат > 32, значит успех
            if result <= 32:
                raise OSError(f"ShellExecute error code: {result}")
            
            info(f"Процесс запущен (Admin): {file_path}", "processes")
            reply_msg_base += "\n🛡️ Режим: администратор"
            await message.answer(reply_msg_base, reply_markup=markup)
            
        else:
            # Обычный запуск
            # subprocess.Popen c shell=True на Windows работает аналогично win+r
            
            # Формируем команду. Если есть пробелы в пути к файлу, subprocess их обработает,
            # но для shell=True лучше передавать список или корректно экранированную строку.
            # На Windows список аргументов при shell=True работает так: первый элемент - команда, остальные - аргументы.
            
            cmd_args = [file_path] + arguments
            
            creationflags = 0
            if hidden_mode:
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                # отвязывает процесс от консоли бота
                creationflags = subprocess.CREATE_NEW_CONSOLE

            proc = subprocess.Popen(
                cmd_args, 
                cwd=working_dir, 
                creationflags=creationflags,
                shell=True # Позволяет запускать не только .exe
            )
            
            active_processes[process_key] = proc
            await message.answer(reply_msg_base, reply_markup=markup)

    except Exception as e:
        logging.exception("Ошибка запуска процесса")
        err_msg = str(e)
        # Если ошибка "не является приложением Win32", пробуем os.startfile как fallback
        if "Win32" in err_msg or "OSError" in err_msg:
            try:
                os.startfile(file_path)
                await message.answer(f"✅ Запущено через os.startfile: {file_path}\n(PID не отслеживается)")
                return
            except Exception:
                pass
        
        await message.answer(f"⚠️ Ошибка запуска: {err_msg}")

@router.callback_query(F.data.startswith("save_path"))
async def handle_save_path_callback(call: CallbackQuery) -> None:
    try:
        parts = call.data.split(":", 1)
        if len(parts) < 2:
            await call.answer("⚠️ Ошибка данных", show_alert=True)
            return
            
        request_id = parts[1]
        if request_id not in path_save_requests:
            await call.answer("⚠️ Ссылка устарела", show_alert=True)
            return
            
        name, path = path_save_requests.pop(request_id)
        config = get_paths_config()
        
        if config.add_user_path(call.from_user.id, name, path):
            await call.message.edit_text(
                f"✅ Путь сохранен!\n\nИмя: <code>{name}</code>\nПуть: {path}"
            )
        else:
            await call.answer("❌ Путь не существует", show_alert=True)
            
    except Exception as e:
        logging.exception("Ошибка callback")
        await call.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.message(Command("off"))
async def handle_off(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(get_command_help_text("off"))
        return

    target = args[1].strip()

    # Остановка всех
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

    # Поиск процесса
    matched_proc: subprocess.Popen | None = None
    matched_name: str | None = None
    
    # Поиск по PID
    if target.isdigit():
        pid = int(target)
        for name, proc in active_processes.items():
            if proc.pid == pid:
                matched_proc = proc
                matched_name = name
                break
    
    # Поиск по имени
    if not matched_proc:
        target_lower = target.lower()
        for name, proc in active_processes.items():
            if os.path.basename(name).lower().startswith(target_lower):
                matched_proc = proc
                matched_name = name
                break

    # Результат поиска
    if not matched_proc or not matched_name:
        await message.answer(f"❌ Процесс '{target}' не найден в списке запущенных ботом.")
        return

    if matched_proc.poll() is not None:
        active_processes.pop(matched_name, None)
        await message.answer(f"ℹ️ Процесс '{os.path.basename(matched_name)}' уже завершен")
        return

    # Запрос подтверждения
    from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager
    manager = get_confirmation_manager()
    action_config = DANGEROUS_ACTIONS["process_stop"]

    await manager.create_confirmation(
        chat_id=message.chat.id,
        action_type="process_stop",
        action_data={"action_type": "process_stop", "action_data": {"target": target}, "target": target},
        warning_message=action_config["warning"].format(
            action_data=f"Остановка процесса: {os.path.basename(matched_name)} (PID: {matched_proc.pid})"
        ),
        timeout=action_config["timeout"],
    )


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
        ),
        timeout=action_config["timeout"],
    )
