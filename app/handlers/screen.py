# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import io

from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from ..gui_utils import lazy_import_pil, lazy_import_pyautogui
from ..router import router
from ..state import screen_find_requests


@router.message(Command("screen"))
async def handle_screen(message: Message) -> None:
    if len(message.text.split()) > 1:
        await message.answer("⚠️ Выбор конкретного окна не поддерживается. Делаю скриншот всего экрана.")

    try:
        pyautogui = lazy_import_pyautogui()
        screenshot = pyautogui.screenshot()
    except RuntimeError as e:
        await message.answer(f"⚠️ {e}")
        return
    except Exception:
        try:
            ImageGrab = lazy_import_pil()
            screenshot = ImageGrab.grab()
        except RuntimeError as e:
            await message.answer(f"⚠️ {e}")
            return
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
