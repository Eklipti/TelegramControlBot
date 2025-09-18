# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from aiogram.filters import Command
from aiogram.types import Message

from ..router import router
from ..state import download_requests, upload_requests


@router.message(Command("cancel"))
async def handle_cancel(message: Message) -> None:
    chat_id = message.chat.id
    upload_requests.pop(chat_id, None)
    download_requests.pop(chat_id, None)
    await message.answer("❌ Операция отменена")



