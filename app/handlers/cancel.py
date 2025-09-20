# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from aiogram.filters import Command
from aiogram.types import Message

from ..core.logging import info
from ..router import router
from ..state import download_requests, upload_requests


@router.message(Command("cancel"))
async def handle_cancel(message: Message) -> None:
    chat_id = message.chat.id
    info(f"Отмена операций для пользователя {chat_id}", "cancel")
    
    had_upload = chat_id in upload_requests
    had_download = chat_id in download_requests
    
    upload_requests.pop(chat_id, None)
    download_requests.pop(chat_id, None)
    
    if had_upload or had_download:
        info(f"Операции отменены: upload={had_upload}, download={had_download}", "cancel")
    else:
        info("Нет активных операций для отмены", "cancel")
    
    await message.answer("❌ Операция отменена")
