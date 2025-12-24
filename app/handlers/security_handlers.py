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

"""
Обработчики безопасности для подтверждений опасных действий
"""

import asyncio
import os

from aiogram import F
from aiogram.types import BufferedInputFile, CallbackQuery
from ..handlers.files import format_size

from ..core.security import get_confirmation_manager
from ..router import router


@router.callback_query(F.data.startswith(("confirm:", "cancel:")))
async def handle_confirmation_callback(callback: CallbackQuery) -> None:
    """Обрабатывает подтверждения/отмены опасных действий"""

    manager = get_confirmation_manager()
    result = await manager.handle_confirmation_callback(callback)

    if result is not None:
        # Действие подтверждено, выполняем соответствующую логику
        action_type = result.get("action_type")

        if action_type == "reload":
            await _execute_reload(callback, result)
        elif action_type == "file_delete":
            await _execute_file_delete(callback, result)
        elif action_type == "file_upload":
            await _execute_file_upload(callback, result)
        elif action_type == "file_cut":
            await _execute_file_cut(callback, result)
        elif action_type == "process_stop":
            await _execute_process_stop(callback, result)
        elif action_type == "process_stop_all":
            await _execute_process_stop_all(callback, result)
        elif action_type == "rdp_start":
            await _execute_rdp_start(callback, result)
        elif action_type == "folder_download":
            await _execute_folder_download(callback, result)


async def _execute_reload(callback: CallbackQuery, result: dict) -> None:
    """Выполняет перезагрузку системы"""
    try:
        import os

        if os.name == "nt":
            os.system("shutdown /r /t 0")
        else:
            os.system("sudo reboot")
        await callback.bot.send_message(
            callback.from_user.id, "🔄 <b>Перезагрузка инициирована</b>\n\nСистема будет перезагружена..."
        )
    except Exception as e:
        await callback.bot.send_message(callback.from_user.id, f"⚠️ Ошибка при перезагрузке: {e}")


async def _execute_file_delete(callback: CallbackQuery, result: dict) -> None:
    """Выполняет удаление файла"""
    file_path = result.get("file_path")
    if not file_path:
        await callback.bot.send_message(callback.from_user.id, "⚠️ Ошибка: путь к файлу не указан")
        return

    try:
        import os

        if os.path.exists(file_path):
            os.remove(file_path)
            await callback.bot.send_message(callback.from_user.id, f"✅ Файл успешно удален:\n{file_path}")
        else:
            await callback.bot.send_message(callback.from_user.id, f"⚠️ Файл не найден: {file_path}")
    except Exception as e:
        await callback.bot.send_message(callback.from_user.id, f"⚠️ Ошибка при удалении файла: {e}")


async def _execute_file_upload(callback: CallbackQuery, result: dict) -> None:
    """Инициирует загрузку файла"""
    from ..state import upload_requests

    target_path = result.get("target_path")
    if not target_path:
        await callback.bot.send_message(callback.from_user.id, "⚠️ Ошибка: путь назначения не указан")
        return

    upload_requests[callback.from_user.id] = target_path
    await callback.bot.send_message(
        callback.from_user.id,
        f"📤 <b>Загрузка разрешена</b>\n\nОтправьте файл для сохранения по пути:\n{target_path}\n\nИспользуйте /cancel для отмены.",  # noqa: E501
    )


async def _execute_process_stop(callback: CallbackQuery, result: dict) -> None:
    """Выполняет остановку процесса"""
    target = result.get("target")
    if not target:
        await callback.bot.send_message(callback.from_user.id, "⚠️ Ошибка: цель не указана")
        return

    try:
        import os
        import subprocess

        from ..handlers.processes import active_processes

        if target.isdigit():
            pid = int(target)
            for name, proc in active_processes.items():
                if proc.pid == pid:
                    if os.name == "nt":
                        subprocess.call(f"taskkill /F /T /PID {proc.pid}", shell=True)
                    else:
                        proc.terminate()
                    active_processes.pop(name, None)
                    await callback.bot.send_message(
                        callback.from_user.id, f"⛔ Процесс '{name}' (PID: {proc.pid}) остановлен"
                    )
                    return
        else:
            target_lower = target.lower()
            for name, proc in active_processes.items():
                if name.lower() == target_lower:
                    if os.name == "nt":
                        subprocess.call(f"taskkill /F /T /PID {proc.pid}", shell=True)
                    else:
                        proc.terminate()
                    active_processes.pop(name, None)
                    await callback.bot.send_message(
                        callback.from_user.id, f"⛔ Процесс '{name}' (PID: {proc.pid}) остановлен"
                    )
                    return

        await callback.bot.send_message(callback.from_user.id, f"❌ Процесс '{target}' не найден")
    except Exception as e:
        await callback.bot.send_message(callback.from_user.id, f"⚠️ Ошибка при остановке процесса: {e}")


async def _execute_process_stop_all(callback: CallbackQuery, result: dict) -> None:
    """Выполняет остановку всех процессов"""
    try:
        import os
        import subprocess

        from ..handlers.processes import active_processes

        stopped = []
        failed = []

        for name, proc in list(active_processes.items()):
            if proc.poll() is None:
                try:
                    if os.name == "nt":
                        subprocess.call(f"taskkill /F /T /PID {proc.pid}", shell=True)
                    else:
                        proc.terminate()
                    stopped.append(name)
                except Exception as e:
                    failed.append(f"{name}: {e}")
                finally:
                    active_processes.pop(name, None)

        response = "⛔ <b>Остановлены процессы:</b>\n" + (
            "\n".join(f"• {name}" for name in stopped) if stopped else "ℹ️ Нет процессов для остановки"
        )  # noqa: E501
        if failed:
            response += "\n\n❌ <b>Ошибки:</b>\n" + "\n".join(failed)

        await callback.bot.send_message(callback.from_user.id, response)
    except Exception as e:
        await callback.bot.send_message(callback.from_user.id, f"⚠️ Ошибка при остановке процессов: {e}")


async def _execute_rdp_start(callback: CallbackQuery, result: dict) -> None:
    """Выполняет запуск RDP сессии"""
    from ..core.logging import error, info, warning
    
    try:
        fps = result.get("fps", 1)
        chat_id = callback.from_user.id
        
        from ..handlers.remote_desktop import RDP_SESSIONS, _rdp_stream
        
        if chat_id in RDP_SESSIONS:
            session_info = RDP_SESSIONS[chat_id]
            await callback.bot.send_message(
                chat_id, f"ℹ️ Сессия уже запущена ({session_info['fps']} FPS). Используйте /rdp_stop"
            )
            return

        # Запускаем RDP сессию
        stop_event = asyncio.Event()
        task = asyncio.create_task(_rdp_stream(callback.bot, chat_id, stop_event, fps))
        RDP_SESSIONS[chat_id] = {"task": task, "stop_event": stop_event, "fps": fps}
        
        await callback.bot.send_message(
            chat_id, f"✅ RDP сессия запущена с FPS {fps}. Используйте /rdp_stop для остановки"
        )
        info(f"RDP сессия успешно запущена для пользователя {chat_id}")
            
    except Exception as e:
        error(f"Ошибка при запуске RDP сессии: {e}", "security")
        await callback.bot.send_message(
            callback.from_user.id, f"❌ Ошибка при запуске RDP сессии: {str(e)}"
        )


async def _execute_folder_download(callback: CallbackQuery, result: dict) -> None:
    """Выполняет скачивание папки после подтверждения"""
    from ..handlers.files import execute_folder_download

    # Добавляем необходимые данные для выполнения
    action_data = result.get("action_data", {})
    action_data.update({"bot": callback.bot, "chat_id": callback.from_user.id, "message": callback.message})

    await execute_folder_download(action_data)


async def _execute_file_cut(callback: CallbackQuery, result: dict) -> None:
    """Выполняет скачивание и удаление файла"""
    file_path = result.get("file_path")
    file_size = result.get("file_size", 0)

    if not file_path:
        await callback.bot.send_message(callback.from_user.id, "⚠️ Ошибка: путь к файлу не указан")
        return

    try:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            await callback.bot.send_message(callback.from_user.id, f"⚠️ Файл уже не существует: {file_path}")
            return
        
        with open(file_path, "rb") as f:
            await callback.bot.send_document(
                callback.from_user.id,
                BufferedInputFile(f.read(), filename=os.path.basename(file_path)),
                caption=f"✂️ Файл: {file_path}\n📊 Размер: {format_size(file_size)}"
            )

        os.remove(file_path)
        
        await callback.bot.send_message(callback.from_user.id, f"✅ Файл скачан и удален:\n{file_path}")

    except Exception as e:
        await callback.bot.send_message(callback.from_user.id, f"⚠️ Ошибка при операции 'Скачать и удалить': {e}")