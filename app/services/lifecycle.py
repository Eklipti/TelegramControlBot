# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from aiogram import Bot
from aiogram.types import BotCommand

from ..config import Settings
from ..help_texts import COMMAND_HELP


class LifecycleManager:
    def __init__(self, bot: Bot, settings: Settings) -> None:
        self.bot = bot
        self.settings = settings

    async def on_startup(self) -> None:
        # Register bot commands menu
        try:
            commands = [
                BotCommand(command=cmd, description=(data.get('description') or '')[:256])
                for cmd, data in sorted(COMMAND_HELP.items(), key=lambda x: x[0])
            ]
            await self.bot.set_my_commands(commands)
        except Exception:
            pass

        for user_id in self.settings.allowed_user_ids:
            try:
                await self.bot.send_message(user_id, "🟢 <b>Бот запущен</b>")
            except Exception:
                pass

    async def on_shutdown(self) -> None:
        for user_id in self.settings.allowed_user_ids:
            try:
                await self.bot.send_message(user_id, "⛔ <b>Бот остановлен</b>")
            except Exception:
                pass



