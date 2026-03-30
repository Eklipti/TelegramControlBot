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

import contextlib
import io
import tempfile
from pathlib import Path

import cv2
import pyautogui
from aiogram import F
from aiogram.types import Message

from ..core.logging import debug, error, info, warning
from ..router import router
from ..state import mouse_positions, screen_find_requests, upload_requests


@router.message(F.document | F.photo)
async def handle_file(message: Message) -> None:
    chat_id = message.chat.id
    debug(f"Получен файл от пользователя {chat_id}", "attachments")

    if chat_id in upload_requests:
        target_path = upload_requests.pop(chat_id)
        info(f"Начало загрузки файла в {target_path} для пользователя {chat_id}", "attachments")
        try:
            if message.document:
                file_id = message.document.file_id
                original_name = message.document.file_name or "uploaded_file"
                debug(f"Загружается документ: {original_name}", "attachments")
            else:
                file_id = message.photo[-1].file_id  # type: ignore[index]
                original_name = "uploaded_photo.jpg"
                debug(f"Загружается фото: {original_name}", "attachments")

            target_p = Path(target_path)

            final_path = target_p / original_name if target_p.is_dir() else target_p

            dir_path = final_path.parent
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                debug(f"Создана директория: {dir_path}", "attachments")

            file = await message.bot.get_file(file_id)
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, destination=buf)  # type: ignore[arg-type]

            with final_path.open("wb") as new_file:
                new_file.write(buf.getvalue())

            info(f"Файл успешно сохранен: {final_path}", "attachments")
            await message.answer(f"✅ Файл сохранен как:\n{final_path}")
        except Exception as e:
            error(f"Ошибка при загрузке файла для пользователя {chat_id}: {e}", "attachments")
            await message.answer(f"⚠️ Ошибка при загрузке файла: {e}")
        return

    if message.photo and message.chat.id in screen_find_requests:
        chat_id = message.chat.id
        screen_find_requests.discard(chat_id)
        info(f"Начало поиска по фото для пользователя {chat_id}", "attachments")
        template_path: str | None = None
        screen_path: str | None = None
        try:
            debug("GUI модули успешно импортированы", "attachments")

            file = await message.bot.get_file(message.photo[-1].file_id)  # type: ignore[index]
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, destination=buf)  # type: ignore[arg-type]

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_t:
                tmp_t.write(buf.getvalue())
                template_path = tmp_t.name

            screenshot = pyautogui.screenshot()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_s:
                screenshot.save(tmp_s, format="PNG")
                screen_path = tmp_s.name

            debug("Скриншот и шаблон сохранены во временные файлы", "attachments")

            img_rgb = cv2.imread(screen_path)
            template = cv2.imread(template_path)

            result = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > 0.8:
                x, y = max_loc
                w, h = template.shape[1], template.shape[0]
                mouse_positions["found"] = (x + w // 2, y + h // 2)
                info(
                    f"Объект найден на координатах ({x + w // 2}, {y + h // 2}) с точностью {max_val:.2f}",
                    "attachments",
                )
                await message.answer(f"🔍 Объект найден! Координаты: ({x + w // 2}, {y + h // 2})")
            else:
                warning(f"Объект не найден на экране (максимальная точность: {max_val:.2f})", "attachments")
                await message.answer("❌ Объект не найден на экране")
        except Exception as e:
            error(f"Ошибка поиска по фото для пользователя {chat_id}: {e}", "attachments")
            await message.answer(f"⚠️ Ошибка поиска: {e}")
        finally:
            with contextlib.suppress(Exception):
                if template_path:
                    Path(template_path).unlink(missing_ok=True)
            with contextlib.suppress(Exception):
                if screen_path:
                    Path(screen_path).unlink(missing_ok=True)
