# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import os

from aiogram import Bot


class FileMonitor:
    def __init__(self) -> None:
        self._paths: set[str] = set()
        self._last_state: dict[str, tuple[float, int]] = {}
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._subscribers: set[int] = set()

    async def start(self, bot: Bot, chat_id: int) -> None:
        self._subscribers.add(chat_id)
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._worker(bot))

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
            self._task = None
        async with self._lock:
            self._paths.clear()
            self._last_state.clear()
            self._subscribers.clear()

    async def add_path(self, path: str, bot: Bot, chat_id: int) -> None:
        async with self._lock:
            self._paths.add(os.path.abspath(path))
        await self.start(bot, chat_id)

    async def remove_path(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        async with self._lock:
            if abs_path in self._paths:
                self._paths.remove(abs_path)
                return True
        return False

    async def get_paths(self) -> list[str]:
        async with self._lock:
            return list(self._paths)

    async def _worker(self, bot: Bot) -> None:
        try:
            while True:
                await asyncio.sleep(5)  # Уменьшено с 10 до 5 секунд
                async with self._lock:
                    paths = list(self._paths)
                current_state: dict[str, tuple[float, int]] = {}

                for path in paths:
                    if not os.path.exists(path):
                        continue
                    if os.path.isfile(path):
                        try:
                            current_state[path] = (
                                os.path.getmtime(path),
                                os.path.getsize(path),
                            )
                        except Exception:
                            continue
                    else:
                        for root, _, files in os.walk(path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    current_state[file_path] = (
                                        os.path.getmtime(file_path),
                                        os.path.getsize(file_path),
                                    )
                                except Exception:
                                    continue

                if not self._last_state:
                    self._last_state = current_state
                    continue

                changed: list[str] = []
                created: list[str] = []
                deleted: list[str] = []

                for path, info in current_state.items():
                    if path in self._last_state:
                        old_mtime, old_size = self._last_state[path]
                        if info[0] != old_mtime or info[1] != old_size:
                            changed.append(path)
                    else:
                        created.append(path)

                for path in self._last_state:
                    if path not in current_state:
                        deleted.append(path)

                # Группируем изменения по пользователям для уменьшения количества сообщений
                if created or changed or deleted:
                    for user_id in list(self._subscribers):
                        try:
                            message_parts = []
                            if created:
                                message_parts.append("📁 ➕ <b>Созданы:</b>\n" + "\n".join(f"• {p}" for p in created[:10]))
                                if len(created) > 10:
                                    message_parts.append(f"... и еще {len(created) - 10} файлов")
                            if changed:
                                message_parts.append("📁 ✏️ <b>Изменены:</b>\n" + "\n".join(f"• {p}" for p in changed[:10]))
                                if len(changed) > 10:
                                    message_parts.append(f"... и еще {len(changed) - 10} файлов")
                            if deleted:
                                message_parts.append("📁 ➖ <b>Удалены:</b>\n" + "\n".join(f"• {p}" for p in deleted[:10]))
                                if len(deleted) > 10:
                                    message_parts.append(f"... и еще {len(deleted) - 10} файлов")

                            if message_parts:
                                message = "\n\n".join(message_parts)
                                await bot.send_message(user_id, message)
                        except Exception:
                            pass

                self._last_state = current_state
        except asyncio.CancelledError:
            return



