import asyncio
import logging
import signal
from typing import List

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import Settings, load_env
from .router import router
from .services.lifecycle import LifecycleManager
from .handlers.auth import AllowedUserFilter
from . import handlers  # noqa: F401 - import registers handlers


async def _run() -> None:
    load_env()
    settings = Settings.load()
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # apply allowed user filter globally
    allowed_filter = AllowedUserFilter(settings.allowed_user_ids)
    router.message.filter(allowed_filter)
    router.callback_query.filter(allowed_filter)

    dp.include_router(router)

    lifecycle = LifecycleManager(bot=bot, settings=settings)
    await lifecycle.on_startup()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _stop(*_: List[int]) -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: _stop())

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await lifecycle.on_shutdown()
        await bot.session.close()


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()



