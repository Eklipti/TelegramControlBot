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
