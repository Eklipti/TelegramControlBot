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

from aiogram import Bot
from aiogram.types import BotCommand

from ..config import Settings
from ..core.logging import debug, error, info, warning
from ..help_texts import COMMAND_HELP


class LifecycleManager:
    def __init__(self, bot: Bot, settings: Settings) -> None:
        self.bot = bot
        self.settings = settings

    async def on_startup(self) -> None:
        info("Начало процедуры запуска бота", "lifecycle")
        
        # Register bot commands menu
        try:
            commands = [
                BotCommand(command=cmd, description=(data.get("description") or "")[:256])
                for cmd, data in sorted(COMMAND_HELP.items(), key=lambda x: x[0])
            ]
            debug(f"Подготовлено {len(commands)} команд для регистрации", "lifecycle")
            await self.bot.set_my_commands(commands)
            info(f"Зарегистрировано {len(commands)} команд бота", "lifecycle")
        except Exception as e:
            error(f"Ошибка при регистрации команд бота: {e}", "lifecycle")

        # Отправка уведомлений разрешенным пользователям
        allowed_users = self.settings.get_allowed_user_ids()
        debug(f"Отправка уведомлений о запуске {len(allowed_users)} пользователям", "lifecycle")
        for user_id in allowed_users:
            try:
                await self.bot.send_message(user_id, "🟢 <b>Бот запущен</b>")
            except Exception as e:
                warning(f"Не удалось отправить уведомление о запуске пользователю {user_id}: {e}", "lifecycle")
        
        info("Процедура запуска бота завершена", "lifecycle")

    async def on_shutdown(self) -> None:
        info("Начало процедуры остановки бота", "lifecycle")
        
        # Отправка уведомлений разрешенным пользователям
        allowed_users = self.settings.get_allowed_user_ids()
        debug(f"Отправка уведомлений об остановке {len(allowed_users)} пользователям", "lifecycle")
        for user_id in allowed_users:
            try:
                await self.bot.send_message(user_id, "⛔ <b>Бот остановлен</b>")
            except Exception as e:
                warning(f"Не удалось отправить уведомление об остановке пользователю {user_id}: {e}", "lifecycle")
        
        info("Процедура остановки бота завершена", "lifecycle")
