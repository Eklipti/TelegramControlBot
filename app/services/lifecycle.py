# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from aiogram import Bot
from aiogram.types import BotCommand

from ..config import Settings
from ..core.logging import error, info, warning, debug, trace, trace_function_entry, trace_function_exit
from ..help_texts import COMMAND_HELP


class LifecycleManager:
    def __init__(self, bot: Bot, settings: Settings) -> None:
        self.bot = bot
        self.settings = settings

    async def on_startup(self) -> None:
        trace_function_entry("LifecycleManager.on_startup", logger_name="lifecycle")
        info("Начало процедуры запуска бота", "lifecycle")
        
        # Register bot commands menu
        try:
            trace("Начало регистрации команд бота", "lifecycle")
            commands = [
                BotCommand(command=cmd, description=(data.get("description") or "")[:256])
                for cmd, data in sorted(COMMAND_HELP.items(), key=lambda x: x[0])
            ]
            debug(f"Подготовлено {len(commands)} команд для регистрации", "lifecycle")
            await self.bot.set_my_commands(commands)
            info(f"Зарегистрировано {len(commands)} команд бота", "lifecycle")
            trace("Команды бота успешно зарегистрированы", "lifecycle")
        except Exception as e:
            error(f"Ошибка при регистрации команд бота: {e}", "lifecycle")
            trace(f"Детали ошибки регистрации команд: {e}", "lifecycle")

        allowed_users = self.settings.get_allowed_user_ids()
        trace(f"Отправка уведомлений о запуске {len(allowed_users)} пользователям", "lifecycle")
        for user_id in allowed_users:
            try:
                trace(f"Отправка уведомления о запуске пользователю {user_id}", "lifecycle")
                await self.bot.send_message(user_id, "🟢 <b>Бот запущен</b>")
                info(f"Уведомление о запуске отправлено пользователю {user_id}", "lifecycle")
            except Exception as e:
                warning(f"Не удалось отправить уведомление о запуске пользователю {user_id}: {e}", "lifecycle")
                trace(f"Детали ошибки отправки уведомления пользователю {user_id}: {e}", "lifecycle")
        
        info("Процедура запуска бота завершена", "lifecycle")
        trace_function_exit("LifecycleManager.on_startup", result="success", logger_name="lifecycle")

    async def on_shutdown(self) -> None:
        trace_function_entry("LifecycleManager.on_shutdown", logger_name="lifecycle")
        info("Начало процедуры остановки бота", "lifecycle")
        
        allowed_users = self.settings.get_allowed_user_ids()
        trace(f"Отправка уведомлений об остановке {len(allowed_users)} пользователям", "lifecycle")
        for user_id in allowed_users:
            try:
                trace(f"Отправка уведомления об остановке пользователю {user_id}", "lifecycle")
                await self.bot.send_message(user_id, "⛔ <b>Бот остановлен</b>")
                info(f"Уведомление об остановке отправлено пользователю {user_id}", "lifecycle")
            except Exception as e:
                warning(f"Не удалось отправить уведомление об остановке пользователю {user_id}: {e}", "lifecycle")
                trace(f"Детали ошибки отправки уведомления об остановке пользователю {user_id}: {e}", "lifecycle")
        
        info("Процедура остановки бота завершена", "lifecycle")
        trace_function_exit("LifecycleManager.on_shutdown", result="success", logger_name="lifecycle")
