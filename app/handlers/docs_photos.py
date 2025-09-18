# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
import os
import tempfile

import cv2
import pyautogui
from aiogram import F
from aiogram.types import BufferedInputFile, Message

from ..router import router
from ..state import download_requests, mouse_positions, screen_find_requests, upload_requests


@router.message(F.document | F.photo)
async def handle_file(message: Message) -> None:
    chat_id = message.chat.id

    if chat_id in upload_requests:
        target_path = upload_requests.pop(chat_id)
        try:
            if message.document:
                file_id = message.document.file_id
                original_name = message.document.file_name or "uploaded_file"
            else:
                file_id = message.photo[-1].file_id  # type: ignore[index]
                original_name = "uploaded_photo.jpg"

            if os.path.isdir(target_path):
                final_path = os.path.join(target_path, original_name)
            else:
                final_path = target_path

            dir_path = os.path.dirname(final_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            file = await message.bot.get_file(file_id)
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, destination=buf)  # type: ignore[arg-type]
            with open(final_path, 'wb') as new_file:
                new_file.write(buf.getvalue())

            await message.answer(f"✅ Файл сохранен как:\n{final_path}")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка при загрузке файла: {e}")
        return

    if chat_id in download_requests:
        file_path = download_requests.pop(chat_id)
        try:
            if not os.path.exists(file_path):
                await message.answer(f"⚠️ Файл не существует: {file_path}")
                return
            with open(file_path, 'rb') as f:
                await message.answer_document(BufferedInputFile(f.read(), filename=os.path.basename(file_path)), caption=f"📥 Файл: {file_path}")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка при отправке файла: {e}")
        return

    if message.photo and message.chat.id in screen_find_requests:
        chat_id = message.chat.id
        # Одноразовый флаг на поиск по фото
        screen_find_requests.discard(chat_id)
        template_path: str | None = None
        screen_path: str | None = None
        try:
            file = await message.bot.get_file(message.photo[-1].file_id)  # type: ignore[index]
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, destination=buf)  # type: ignore[arg-type]

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_t:
                tmp_t.write(buf.getvalue())
                template_path = tmp_t.name

            screenshot = pyautogui.screenshot()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_s:
                screenshot.save(tmp_s, format='PNG')
                screen_path = tmp_s.name

            img_rgb = cv2.imread(screen_path)
            template = cv2.imread(template_path)

            result = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > 0.8:
                x, y = max_loc
                w, h = template.shape[1], template.shape[0]
                mouse_positions["found"] = (x + w//2, y + h//2)
                await message.answer(f"🔍 Объект найден! Координаты: ({x + w//2}, {y + h//2})")
            else:
                await message.answer("❌ Объект не найден на экране")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка поиска: {e}")
        finally:
            try:
                if template_path and os.path.exists(template_path):
                    os.remove(template_path)
            except Exception:
                pass
            try:
                if screen_path and os.path.exists(screen_path):
                    os.remove(screen_path)
            except Exception:
                pass



