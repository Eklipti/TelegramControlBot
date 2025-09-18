# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class AllowedUserFilter(BaseFilter):
    def __init__(self, allowed_ids: list[int]) -> None:
        self.allowed = set(allowed_ids)

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        user = obj.from_user
        return bool(user and user.id in self.allowed)



