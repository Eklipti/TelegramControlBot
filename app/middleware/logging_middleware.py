# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Middleware для логирования всех взаимодействий с ботом.
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from ..core.logging import debug, info, trace, trace_function_entry, trace_function_exit


class BotInteractionLoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех взаимодействий с ботом."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обрабатывает входящие события и логирует их.
        
        Args:
            handler: Следующий обработчик в цепочке
            event: Входящее событие (Message, CallbackQuery, etc.)
            data: Данные для передачи в обработчик
        """
        trace_function_entry("BotInteractionLoggingMiddleware.__call__", 
                           args=(type(event).__name__,), 
                           kwargs={"data_keys": list(data.keys())},
                           logger_name="middleware")

        # Логируем входящее событие
        await self._log_incoming_event(event, data)
        
        try:
            # Вызываем следующий обработчик
            result = await handler(event, data)
            
            # Логируем успешную обработку
            await self._log_successful_processing(event, result)
            
            trace_function_exit("BotInteractionLoggingMiddleware.__call__", 
                              result="success",
                              logger_name="middleware")
            return result
            
        except Exception as e:
            # Логируем ошибку обработки
            await self._log_processing_error(event, e)
            trace_function_exit("BotInteractionLoggingMiddleware.__call__", 
                              result=f"error: {e}",
                              logger_name="middleware")
            raise

    async def _log_incoming_event(self, event: TelegramObject, data: Dict[str, Any]) -> None:
        """Логирует входящее событие."""
        if isinstance(event, Message):
            await self._log_message(event, data)
        elif isinstance(event, CallbackQuery):
            await self._log_callback_query(event, data)
        else:
            # Логируем другие типы событий
            info(f"Получено событие: {type(event).__name__}", "bot_interaction")
            trace(f"Детали события {type(event).__name__}: {event}", "bot_interaction")

    async def _log_message(self, message: Message, data: Dict[str, Any]) -> None:
        """Логирует входящее сообщение."""
        user = message.from_user
        chat = message.chat
        
        # Основная информация о сообщении
        message_info = {
            "message_id": message.message_id,
            "user_id": user.id if user else None,
            "username": user.username if user else None,
            "chat_id": chat.id if chat else None,
            "chat_type": chat.type if chat else None,
            "text": message.text[:100] + "..." if message.text and len(message.text) > 100 else message.text,
            "has_photo": bool(message.photo),
            "has_document": bool(message.document),
            "has_video": bool(message.video),
            "has_audio": bool(message.audio),
            "has_voice": bool(message.voice),
            "has_sticker": bool(message.sticker),
            "has_animation": bool(message.animation),
            "has_contact": bool(message.contact),
            "has_location": bool(message.location),
            "has_venue": bool(message.venue),
            "has_poll": bool(message.poll),
            "has_dice": bool(message.dice),
        }
        
        # Логируем основную информацию
        info(f"Получено сообщение от пользователя {user.id} ({user.username or 'без username'}) "
             f"в чат {chat.id} ({chat.type}): {message.text or 'без текста'}", 
             "bot_interaction")
        
        # Детальная информация для отладки
        debug(f"Детали сообщения: {message_info}", "bot_interaction")
        
        # TRACE информация о содержимом
        if message.text:
            trace(f"Текст сообщения: {message.text}", "bot_interaction")
        
        # Логируем медиа файлы
        if message.photo:
            trace(f"Фото: {len(message.photo)} вариантов размеров", "bot_interaction")
        if message.document:
            trace(f"Документ: {message.document.file_name} ({message.document.file_size} байт)", "bot_interaction")
        if message.video:
            trace(f"Видео: {message.video.file_name} ({message.video.file_size} байт)", "bot_interaction")

    async def _log_callback_query(self, callback: CallbackQuery, data: Dict[str, Any]) -> None:
        """Логирует callback запрос."""
        user = callback.from_user
        message = callback.message
        
        callback_info = {
            "callback_id": callback.id,
            "user_id": user.id if user else None,
            "username": user.username if user else None,
            "data": callback.data,
            "message_id": message.message_id if message else None,
            "chat_id": message.chat.id if message and message.chat else None,
        }
        
        # Логируем основную информацию
        info(f"Получен callback от пользователя {user.id} ({user.username or 'без username'}): {callback.data}", 
             "bot_interaction")
        
        # Детальная информация для отладки
        debug(f"Детали callback: {callback_info}", "bot_interaction")
        
        # TRACE информация
        trace(f"Callback data: {callback.data}", "bot_interaction")

    async def _log_successful_processing(self, event: TelegramObject, result: Any) -> None:
        """Логирует успешную обработку события."""
        if isinstance(event, Message):
            user = event.from_user
            info(f"Сообщение от пользователя {user.id} ({user.username or 'без username'}) успешно обработано", 
                 "bot_interaction")
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            info(f"Callback от пользователя {user.id} ({user.username or 'без username'}) успешно обработан", 
                 "bot_interaction")
        
        trace(f"Результат обработки: {type(result).__name__ if result is not None else 'None'}", 
              "bot_interaction")

    async def _log_processing_error(self, event: TelegramObject, error: Exception) -> None:
        """Логирует ошибку обработки события."""
        from ..core.logging import error as log_error
        
        if isinstance(event, Message):
            user = event.from_user
            log_error(f"Ошибка обработки сообщения от пользователя {user.id} ({user.username or 'без username'}): {error}", 
                     "bot_interaction")
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            log_error(f"Ошибка обработки callback от пользователя {user.id} ({user.username or 'без username'}): {error}", 
                     "bot_interaction")
        else:
            log_error(f"Ошибка обработки события {type(event).__name__}: {error}", "bot_interaction")
        
        trace(f"Детали ошибки: {error}", "bot_interaction")
