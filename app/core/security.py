# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Модуль безопасности для ControlBot
Содержит общую логику прав/ролей и подтверждений опасных действий
"""

import asyncio
from typing import Any

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .logging import debug, error, info, warning, trace, trace_function_entry, trace_function_exit

# Хранилище ожидающих подтверждений
pending_confirmations: dict[str, dict[str, Any]] = {}


class PrivateChatFilter(BaseFilter):
    """Фильтр для разрешения только private чатов"""

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        trace_function_entry("PrivateChatFilter.__call__", 
                           args=(type(obj).__name__,), 
                           kwargs={"user_id": obj.from_user.id if obj.from_user else None},
                           logger_name="security")
        
        # Для сообщений
        if isinstance(obj, Message):
            is_private = obj.chat.type == ChatType.PRIVATE
            user_id = obj.from_user.id if obj.from_user else None
            username = obj.from_user.username if obj.from_user else None
            
            if not is_private:
                warning(f"Попытка доступа из не-private чата {obj.chat.type} от пользователя {user_id} ({username})", "security")
                trace(f"Детали не-private чата: chat_id={obj.chat.id}, chat_type={obj.chat.type}, user_id={user_id}", "security")
                trace_function_exit("PrivateChatFilter.__call__", result="not_private_chat", logger_name="security")
            else:
                trace(f"Доступ из private чата от пользователя {user_id} ({username})", "security")
                trace_function_exit("PrivateChatFilter.__call__", result="private_chat_allowed", logger_name="security")
            return is_private
        # Для callback-запросов
        elif isinstance(obj, CallbackQuery):
            is_private = obj.message and obj.message.chat.type == ChatType.PRIVATE
            user_id = obj.from_user.id if obj.from_user else None
            username = obj.from_user.username if obj.from_user else None
            
            if not is_private:
                warning(f"Попытка callback из не-private чата {obj.message.chat.type if obj.message else 'no message'} от пользователя {user_id} ({username})", "security")
                trace(f"Детали не-private callback: chat_id={obj.message.chat.id if obj.message else None}, chat_type={obj.message.chat.type if obj.message else None}, user_id={user_id}", "security")
                trace_function_exit("PrivateChatFilter.__call__", result="not_private_callback", logger_name="security")
            else:
                trace(f"Callback из private чата от пользователя {user_id} ({username})", "security")
                trace_function_exit("PrivateChatFilter.__call__", result="private_callback_allowed", logger_name="security")
            return is_private
        # Для других типов возвращаем False
        warning(f"Неизвестный тип объекта для фильтра: {type(obj)}", "security")
        trace_function_exit("PrivateChatFilter.__call__", result="unknown_object_type", logger_name="security")
        return False


class ConfirmationManager:
    """Менеджер подтверждений для опасных действий"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def create_confirmation(
        self,
        chat_id: int,
        action_type: str,
        action_data: dict[str, Any],
        warning_message: str,
        timeout: int = 300,  # 5 минут по умолчанию
    ) -> str:
        """Создает подтверждение и возвращает его ID"""
        trace_function_entry("ConfirmationManager.create_confirmation", 
                           args=(chat_id, action_type), 
                           kwargs={"timeout": timeout},
                           logger_name="security")

        import uuid

        confirmation_id = f"{action_type}_{uuid.uuid4().hex[:8]}"
        info(f"Создание подтверждения {action_type} для чата {chat_id}, ID: {confirmation_id}", "security")
        debug(f"Данные подтверждения: {action_data}", "security")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{confirmation_id}"),
                    InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel:{confirmation_id}"),
                ]
            ]
        )

        message_text = (
            f"⚠️ <b>ВНИМАНИЕ! Опасное действие</b>\n\n{warning_message}\n\n"
            f"⏰ Подтверждение истечет через {timeout // 60} минут"
        )

        # Отправляем сообщение с подтверждением
        try:
            msg = await self.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=keyboard)
            info(f"Сообщение с подтверждением отправлено в чат {chat_id}, message_id: {msg.message_id}", "security")
        except Exception as e:
            error(f"Ошибка отправки сообщения с подтверждением в чат {chat_id}: {e}", "security")
            trace_function_exit("ConfirmationManager.create_confirmation", result=f"error: {e}", logger_name="security")
            raise

        # Сохраняем данные подтверждения
        pending_confirmations[confirmation_id] = {
            "action_type": action_type,
            "action_data": action_data,
            "chat_id": chat_id,
            "message_id": msg.message_id,
            "created_at": asyncio.get_event_loop().time(),
            "timeout": timeout,
            "warning_message": warning_message,
        }
        debug(f"Подтверждение {confirmation_id} сохранено в pending_confirmations", "security")

        # Автоматическая отмена через timeout
        asyncio.create_task(self._auto_cancel(confirmation_id, timeout))
        trace(f"Задача автоматической отмены создана для подтверждения {confirmation_id}", "security")

        trace_function_exit("ConfirmationManager.create_confirmation", result=confirmation_id, logger_name="security")
        return confirmation_id

    async def _auto_cancel(self, confirmation_id: str, timeout: int) -> None:
        """Автоматическая отмена подтверждения по таймауту"""
        await asyncio.sleep(timeout)

        if confirmation_id in pending_confirmations:
            confirmation = pending_confirmations[confirmation_id]
            try:
                await self.bot.edit_message_text(
                    chat_id=confirmation["chat_id"],
                    message_id=confirmation["message_id"],
                    text="⏰ <b>Подтверждение истекло</b>\n\nДействие отменено по таймауту",
                )
            except Exception:
                pass
            finally:
                pending_confirmations.pop(confirmation_id, None)

    async def handle_confirmation_callback(self, callback: CallbackQuery) -> dict[str, Any] | None:
        """Обрабатывает callback от кнопок подтверждения"""

        action, confirmation_id = callback.data.split(":", 1)

        if confirmation_id not in pending_confirmations:
            await callback.answer("Подтверждение уже обработано или истекло", show_alert=True)
            return None

        confirmation = pending_confirmations[confirmation_id]

        # Проверяем, что callback от правильного пользователя
        if callback.from_user.id != confirmation["chat_id"]:
            await callback.answer("Это не ваше подтверждение", show_alert=True)
            return None

        # Удаляем подтверждение
        action_data = confirmation["action_data"].copy()
        pending_confirmations.pop(confirmation_id, None)

        if action == "confirm":
            await callback.answer("✅ Действие подтверждено")
            try:
                await self.bot.edit_message_text(
                    chat_id=confirmation["chat_id"],
                    message_id=confirmation["message_id"],
                    text=f"✅ <b>Действие подтверждено</b>\n\n{confirmation['warning_message']}",
                )
            except Exception:
                pass
            return action_data
        else:  # cancel
            await callback.answer("❌ Действие отменено")
            try:
                await self.bot.edit_message_text(
                    chat_id=confirmation["chat_id"],
                    message_id=confirmation["message_id"],
                    text="❌ <b>Действие отменено</b>",
                )
            except Exception:
                pass
            return None


# Определения опасных действий
DANGEROUS_ACTIONS = {
    "reload": {
        "warning": "🔄 <b>ПЕРЕЗАГРУЗКА СИСТЕМЫ</b>\n\n"
        "Это действие приведет к немедленной перезагрузке компьютера!\n"
        "• Все несохраненные данные будут потеряны\n"
        "• Все запущенные программы закроются\n"
        "• RDP-сессии будут прерваны\n\n"
        "Убедитесь, что все важные данные сохранены!",
        "timeout": 120,  # 2 минуты для перезагрузки
    },
    "file_delete": {
        "warning": "🗑️ <b>УДАЛЕНИЕ ФАЙЛА</b>\n\n"
        "Файл будет безвозвратно удален!\n"
        "• Восстановление может быть невозможно\n"
        "• Проверьте путь к файлу\n\n"
        "Действие: {action_data}",
        "timeout": 60,
    },
    "file_upload": {
        "warning": "📤 <b>ЗАГРУЗКА ФАЙЛА</b>\n\n"
        "Файл будет загружен и может перезаписать существующий!\n"
        "• Проверьте путь назначения\n"
        "• Убедитесь в безопасности файла\n\n"
        "Действие: {action_data}",
        "timeout": 60,
    },
    "process_stop": {
        "warning": "⛔ <b>ОСТАНОВКА ПРОЦЕССА</b>\n\n"
        "Процесс будет принудительно завершен!\n"
        "• Несохраненные данные могут быть потеряны\n"
        "• Зависимые процессы также могут закрыться\n\n"
        "Действие: {action_data}",
        "timeout": 30,
    },
    "process_stop_all": {
        "warning": "⛔ <b>ОСТАНОВКА ВСЕХ ПРОЦЕССОВ</b>\n\n"
        "ВСЕ активные процессы будут принудительно завершены!\n"
        "• Система может стать нестабильной\n"
        "• Все несохраненные данные будут потеряны\n"
        "• RDP и другие сервисы остановятся\n\n"
        "Это действие крайне опасно!",
        "timeout": 60,
    },
    "rdp_start": {
        "warning": "🖥️ <b>ЗАПУСК RDP-ТРАНСЛЯЦИИ</b>\n\n"
        "Будет запущена трансляция экрана в реальном времени!\n"
        "• Экран будет виден в Telegram\n"
        "• Потребляет дополнительные ресурсы\n"
        "• Может снизить производительность\n\n"
        "Действие: {action_data}",
        "timeout": 30,
    },
    "folder_download": {
        "warning": "📁 <b>СКАЧИВАНИЕ ПАПКИ</b>\n\n"
        "Будет создан архив и отправлена папка:\n"
        "• Путь: {path}\n"
        "• Размер: {size}\n"
        "• Элементов: {items:,}\n\n"
        "⚠️ Убедитесь, что папка не содержит конфиденциальных данных!",
        "timeout": 120,
    },
}


# Глобальный менеджер подтверждений
confirmation_manager: ConfirmationManager | None = None


def init_security(bot: Bot) -> None:
    """Инициализация системы безопасности"""
    global confirmation_manager
    confirmation_manager = ConfirmationManager(bot)


def get_confirmation_manager() -> ConfirmationManager:
    """Получить менеджер подтверждений"""
    if confirmation_manager is None:
        raise RuntimeError("Security system not initialized")
    return confirmation_manager
