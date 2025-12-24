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

import io

import pyautogui
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from PIL import ImageGrab

from ..router import router
from ..state import screen_find_requests


@router.message(Command("screen"))
async def handle_screen(message: Message) -> None:
    if len(message.text.split()) > 1:
        await message.answer("⚠️ Выбор конкретного окна не поддерживается. Делаю скриншот всего экрана.")

    try:
        screenshot = pyautogui.screenshot()
    except Exception:
        try:
            screenshot = ImageGrab.grab()
        except Exception as e:
            await message.answer(f"⚠️ Ошибка создания скриншота: {e}")
            return

    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format="PNG")
    await message.answer_photo(BufferedInputFile(img_byte_arr.getvalue(), filename="screen.png"), caption="Весь экран")


@router.message(Command("screen_find"))
async def handle_screen_find(message: Message) -> None:
    chat_id = message.chat.id
    screen_find_requests.add(chat_id)
    await message.answer("🖼 Отправьте фото-образец. Следующее изображение будет использовано для поиска на экране.")
