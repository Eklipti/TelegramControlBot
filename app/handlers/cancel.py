from aiogram.filters import Command
from aiogram.types import Message

from ..router import router
from ..state import upload_requests, download_requests


@router.message(Command("cancel"))
async def handle_cancel(message: Message) -> None:
    chat_id = message.chat.id
    upload_requests.pop(chat_id, None)
    download_requests.pop(chat_id, None)
    await message.answer("❌ Операция отменена")



