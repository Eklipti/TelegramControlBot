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

import os
import shutil
import tempfile
import time
from pathlib import Path

from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager
from ..help_texts import get_command_help_text
from ..router import router

SYSTEM_DIRECTORIES_BLACKLIST = {
    "C:\\Windows",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "C:\\System Volume Information",
    "C:\\$Recycle.Bin",
    "C:\\Recovery",
    "C:\\Boot",
    "C:\\EFI",
    "C:\\PerfLogs",
    "C:\\hiberfil.sys",
    "C:\\pagefile.sys",
    "C:\\swapfile.sys",
    "AppData\\Local\\Temp",
    "AppData\\Local\\Microsoft\\Windows\\INetCache",
    "AppData\\Local\\Microsoft\\Windows\\WebCache",
    "AppData\\Roaming\\Microsoft\\Windows\\Recent",
    "C:\\Users\\Default",
    "C:\\Users\\Public",
    "C:\\Documents and Settings",
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB для файлов
MAX_FOLDER_SIZE = 500 * 1024 * 1024  # 500 MB для папок
MAX_FOLDER_ITEMS = 10000  # Максимум файлов в папке


def is_path_blacklisted(path: str) -> bool:
    """Проверяет, находится ли путь в черном списке"""
    abs_path = str(Path(path).resolve()).lower()

    for blacklisted in SYSTEM_DIRECTORIES_BLACKLIST:
        blacklisted_lower = blacklisted.lower()
        if abs_path.startswith(blacklisted_lower):
            return True
        if (
            blacklisted_lower.startswith("appdata")
            and "appdata" in abs_path
            and blacklisted_lower.replace("appdata", "").replace("\\", "") in abs_path
        ):
            return True
    return False


def get_folder_size_and_count(path: str) -> tuple[int, int]:
    """Возвращает размер папки в байтах и количество элементов"""
    total_size = 0
    item_count = 0

    try:
        for dirpath, dirnames, filenames in os.walk(path):
            item_count += len(filenames) + len(dirnames)
            if item_count > MAX_FOLDER_ITEMS:
                break

            for filename in filenames:
                filepath = Path(dirpath) / filename
                try:
                    total_size += filepath.stat().st_size
                except OSError:
                    continue

                if total_size > MAX_FOLDER_SIZE:
                    break

            if total_size > MAX_FOLDER_SIZE or item_count > MAX_FOLDER_ITEMS:
                break

    except OSError:
        pass

    return total_size, item_count


def format_size(size_bytes: int) -> str:
    """Форматирует размер в читаемый вид"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


@router.message(Command("upload"))
async def handle_upload_command(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(get_command_help_text("upload"))
        return

    target_path = str(Path(args[1]).resolve())

    from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager

    manager = get_confirmation_manager()
    action_config = DANGEROUS_ACTIONS["file_upload"]

    await manager.create_confirmation(
        chat_id=message.chat.id,
        action_type="file_upload",
        action_data={
            "action_type": "file_upload",
            "action_data": {"target_path": target_path},
            "target_path": target_path,
        },
        warning_message=action_config["warning"].format(action_data=f"Загрузка файла по пути: {target_path}"),
        timeout=action_config["timeout"],
    )


@router.message(Command("download"))
async def handle_download_command(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(get_command_help_text("download"))
        return

    path = str(Path(args[1]).resolve())

    try:
        if not Path(path).exists():
            await message.answer(f"⚠️ Путь не существует: {path}")
            return

        if is_path_blacklisted(path):
            await message.answer(
                f"🚫 <b>Доступ запрещен!</b>\n\n"
                f"Путь находится в системной директории и недоступен для скачивания:\n"
                f"<code>{path}</code>\n\n"
                f"Используйте безопасные директории, например:\n"
                f"• <code>C:\\Users\\{os.getenv('USERNAME', 'User')}\\Desktop</code>\n"
                f"• <code>C:\\Users\\{os.getenv('USERNAME', 'User')}\\Documents</code>\n"
                f"• <code>C:\\Users\\{os.getenv('USERNAME', 'User')}\\Downloads</code>"
            )
            return

        if Path(path).is_file:
            file_size = Path(path).stat().st_size
            if file_size > MAX_FILE_SIZE:
                await message.answer(
                    f"⚠️ <b>Файл слишком большой!</b>\n\n"
                    f"Размер: {format_size(file_size)}\n"
                    f"Максимум: {format_size(MAX_FILE_SIZE)}\n\n"
                    f"Используйте архиватор для сжатия файла."
                )
                return

            with Path(path).open("rb") as f:
                await message.answer_document(
                    BufferedInputFile(f.read(), filename=Path(path).name),
                    caption=f"📥 Файл: {path}\n📊 Размер: {format_size(file_size)}",
                )
        else:
            folder_size, item_count = get_folder_size_and_count(path)

            if item_count > MAX_FOLDER_ITEMS:
                await message.answer(
                    f"⚠️ <b>Папка содержит слишком много элементов!</b>\n\n"
                    f"Элементов: {item_count:,}\n"
                    f"Максимум: {MAX_FOLDER_ITEMS:,}\n\n"
                    f"Попробуйте скачать отдельные подпапки."
                )
                return

            if folder_size > MAX_FOLDER_SIZE:
                await message.answer(
                    f"⚠️ <b>Папка слишком большая!</b>\n\n"
                    f"Размер: {format_size(folder_size)}\n"
                    f"Максимум: {format_size(MAX_FOLDER_SIZE)}\n\n"
                    f"Попробуйте скачать отдельные подпапки."
                )
                return

            from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager

            manager = get_confirmation_manager()
            action_config = DANGEROUS_ACTIONS["folder_download"]

            await manager.create_confirmation(
                chat_id=message.chat.id,
                action_type="folder_download",
                action_data={
                    "action_type": "folder_download",
                    "action_data": {"path": path, "size": folder_size, "items": item_count},
                    "path": path,
                    "size": folder_size,
                    "items": item_count,
                },
                warning_message=action_config["warning"].format(
                    path=path, size=format_size(folder_size), items=item_count
                ),
                timeout=action_config["timeout"],
            )

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("cut"))
async def handle_cut_command(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(get_command_help_text("cut"))
        return

    file_path = str(Path(args[1]).resolve())

    if not Path(file_path).exists():
        await message.answer(f"⚠️ Файл не существует: {file_path}")
        return
    if not Path(file_path).is_file():
        await message.answer(f"⚠️ Указанный путь не является файлом: {file_path}")
        return

    if is_path_blacklisted(file_path):
        await message.answer(
            "🚫 <b>Доступ запрещен!</b>\n\nПуть находится в системной директории и недоступен для скачивания/удаления."
        )
        return

    file_size = Path(file_path).stat().st_size
    if file_size > MAX_FILE_SIZE:
        await message.answer(
            f"⚠️ <b>Файл слишком большой!</b>\n\n"
            f"Размер: {format_size(file_size)}\n"
            f"Максимум: {format_size(MAX_FILE_SIZE)}\n\n"
            f"Эта операция не может быть выполнена."
        )
        return

    manager = get_confirmation_manager()

    action_config = DANGEROUS_ACTIONS["file_cut"]

    await manager.create_confirmation(
        chat_id=message.chat.id,
        action_type="file_cut",
        action_data={
            "action_type": "file_cut",
            "action_data": {"file_path": file_path, "file_size": file_size},
            "file_path": file_path,
            "file_size": file_size,
        },
        warning_message=action_config["warning"].format(action_data=f"Файл: {file_path} ({format_size(file_size)})"),
        timeout=action_config["timeout"],
    )


async def execute_folder_download(action_data: dict) -> None:
    """Выполняет скачивание папки после подтверждения"""
    path = action_data["path"]
    size = action_data["size"]
    items = action_data["items"]

    try:
        msg = await action_data.get("message")
        if msg:
            await msg.edit_text("📦 Архивация папки...")

        zip_path = shutil.make_archive(
            base_name=str(Path(tempfile.gettempdir()) / f"folder_{time.time()}"), format="zip", root_dir=path
        )

        with Path(zip_path).open("rb") as zip_file:
            await action_data["bot"].send_document(
                chat_id=action_data["chat_id"],
                document=BufferedInputFile(zip_file.read(), filename=f"{Path(path).name}.zip"),
                caption=f"📁 Папка: {path}\n📊 Размер: {format_size(size)}\n📄 Элементов: {items:,}",
            )

        Path(zip_path).unlink()

        if msg:
            await msg.delete()

    except Exception as e:
        if msg:
            await msg.edit_text(f"⚠️ Ошибка при архивации: {e}")
