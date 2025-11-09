# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio

from aiogram                        import Bot, Dispatcher
from aiogram.client.default         import DefaultBotProperties
from aiogram.enums                  import ParseMode
from aiogram.fsm.storage.memory     import MemoryStorage

from .handlers.registration         import register_all_handlers
from .config                        import get_settings  
from .core.security                 import PrivateChatFilter, init_security
from .handlers.auth                 import AllowedUserFilter
from .middleware.logging_middleware import BotInteractionLoggingMiddleware
from .router                        import router

from .services.lifecycle            import LifecycleManager
from .services.metrics              import init_metrics
from .services.centralized_logging  import init_centralized_logging
from .config.paths                  import init_paths_config


async def _run() -> None:
    settings = get_settings()

    from app.core.logging import info
    info("Запуск приложения ControlBot", "app")

    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(BotInteractionLoggingMiddleware())
    dp.callback_query.middleware(BotInteractionLoggingMiddleware())
    info("Bot, Dispatcher и middleware созданы", "app")

    init_security(bot)
    info("Система безопасности инициализирована", "app")

    init_metrics(str(settings.get_data_directory()))
    init_centralized_logging(str(settings.get_logs_directory()), str(settings.get_exports_directory()))
    info("Система мониторинга и метрик инициализирована", "app")
    
    paths_config = init_paths_config()
    info(f"Система путей инициализирована. Загружено {len(paths_config.default_paths)} системных путей", "app")

    allowed_filter = AllowedUserFilter(settings.get_allowed_user_ids())
    private_filter = PrivateChatFilter()
    router.message.filter(allowed_filter, private_filter)
    router.callback_query.filter(allowed_filter, private_filter)
    info("Фильтры безопасности применены", "app")

    register_all_handlers(dp)
    info("Все handlers зарегистрированы", "app")

    dp.include_router(router)
    info("Роутер подключен к Dispatcher", "app")

    lifecycle = LifecycleManager(bot=bot, settings=settings)
    await lifecycle.on_startup()
    info("LifecycleManager запущен", "app")

    try:
        info("Начинаем polling Telegram API", "app")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        info("Завершение работы приложения", "app")
        await lifecycle.on_shutdown()
        await bot.session.close()
        info("Приложение остановлено", "app")

def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
