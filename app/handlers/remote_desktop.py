# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import io
import logging
import time

import pyautogui
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InputMediaPhoto, Message

from ..router import router

RDP_SESSIONS: dict[int, dict] = {}


async def _rdp_stream(bot, chat_id: int, stop_event: asyncio.Event, fps: int) -> None:
    interval = 1.0 / fps
    message_id: int | None = None
    last_edit_time = 0.0
    MIN_EDIT_INTERVAL = 0.4  # Минимум 400мс между edit_message_media

    try:
        while not stop_event.is_set():
            try:
                start_time = time.time()
                screenshot = await asyncio.to_thread(pyautogui.screenshot)
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format="JPEG", quality=85)
                img_bytes = img_byte_arr.getvalue()
                caption = f"🖥️ {time.strftime('%H:%M:%S')} | {fps} FPS"

                if message_id is None:
                    try:
                        msg = await bot.send_photo(
                            chat_id,
                            BufferedInputFile(img_bytes, filename="rdp.jpg"),
                            caption=caption,
                            disable_notification=True,
                        )
                    except TelegramRetryAfter as e:
                        await asyncio.sleep(getattr(e, "retry_after", 1.5))
                        continue
                    message_id = msg.message_id
                    last_edit_time = time.time()
                else:
                    # Жесткий rate-limit для edit_message_media
                    current_time = time.time()
                    time_since_last_edit = current_time - last_edit_time
                    if time_since_last_edit < MIN_EDIT_INTERVAL:
                        await asyncio.sleep(MIN_EDIT_INTERVAL - time_since_last_edit)

                    try:
                        media = InputMediaPhoto(media=BufferedInputFile(img_bytes, filename="rdp.jpg"), caption=caption)
                        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media)
                        last_edit_time = time.time()
                    except TelegramRetryAfter as e:
                        await asyncio.sleep(getattr(e, "retry_after", 1.5))
                        continue
                    except Exception as e:
                        if "message to edit not found" in str(e).lower():
                            message_id = None
                            continue
                        logging.exception("Ошибка при обновлении RDP сообщения")
                        raise

                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                await asyncio.sleep(sleep_time)
            except Exception:
                logging.exception("Ошибка в RDP стриме")
                await asyncio.sleep(1)
    finally:
        if message_id:
            try:
                # Проверяем rate-limit для финального обновления
                current_time = time.time()
                time_since_last_edit = current_time - last_edit_time
                if time_since_last_edit < MIN_EDIT_INTERVAL:
                    await asyncio.sleep(MIN_EDIT_INTERVAL - time_since_last_edit)

                try:
                    screenshot = await asyncio.to_thread(pyautogui.screenshot)
                except Exception:
                    # GUI недоступен, пропускаем финальное обновление
                    return
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format="JPEG", quality=85)
                media = InputMediaPhoto(
                    media=BufferedInputFile(img_byte_arr.getvalue(), filename="rdp.jpg"),
                    caption=f"⛔ СТРИМИНГ ОСТАНОВЛЕН | {time.strftime('%H:%M:%S')}",
                )
                try:
                    await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media)
                except TelegramRetryAfter as e:
                    await asyncio.sleep(getattr(e, "retry_after", 1.5))
                    try:
                        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media)
                    except Exception:
                        logging.exception("Ошибка при финальном обновлении RDP сообщения")
                        pass
            except Exception:
                logging.exception("Ошибка при создании финального RDP скриншота")
                pass


@router.message(Command("rdp_start"))
async def handle_rdp_start(message: Message) -> None:
    chat_id = message.chat.id
    args = message.text.split()
    fps = 1
    if len(args) > 1:
        try:
            fps = max(1, min(int(args[1]), 10))
        except Exception:
            pass

    if chat_id in RDP_SESSIONS:
        await message.answer(f"ℹ️ Сессия уже запущена ({RDP_SESSIONS[chat_id]['fps']} FPS). Используйте /rdp_stop")
        return

    from ..core.security import DANGEROUS_ACTIONS, get_confirmation_manager

    manager = get_confirmation_manager()
    action_config = DANGEROUS_ACTIONS["rdp_start"]

    await manager.create_confirmation(
        chat_id=chat_id,
        action_type="rdp_start",
        action_data={"action_type": "rdp_start", "action_data": {"fps": fps}, "fps": fps},
        warning_message=action_config["warning"].format(action_data=f"Запуск RDP-трансляции с {fps} FPS"),
        timeout=action_config["timeout"],
    )


@router.message(Command("rdp_stop"))
async def handle_rdp_stop(message: Message) -> None:
    chat_id = message.chat.id
    if chat_id in RDP_SESSIONS:
        RDP_SESSIONS[chat_id]["stop_event"].set()
        await asyncio.sleep(0.1)
        del RDP_SESSIONS[chat_id]
        await message.answer("⛔ Сессия остановлена")
    else:
        await message.answer("ℹ️ Нет активной сессии")
