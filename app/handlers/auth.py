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

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from ..core.logging import debug, warning, info, trace, trace_function_entry, trace_function_exit


class AllowedUserFilter(BaseFilter):
    def __init__(self, allowed_ids: list[int]) -> None:
        self.allowed = set(allowed_ids)
        info(f"Инициализирован фильтр авторизации для {len(allowed_ids)} пользователей", "auth")
        debug(f"Разрешенные пользователи: {sorted(allowed_ids)}", "auth")

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        trace_function_entry("AllowedUserFilter.__call__", 
                           args=(type(obj).__name__,), 
                           kwargs={"user_id": obj.from_user.id if obj.from_user else None},
                           logger_name="auth")
        
        user = obj.from_user
        if not user:
            warning("Получен объект без пользователя", "auth")
            trace_function_exit("AllowedUserFilter.__call__", result="no_user", logger_name="auth")
            return False
        
        is_allowed = user.id in self.allowed
        username = user.username or "без username"
        
        if not is_allowed:
            warning(f"Попытка доступа от неавторизованного пользователя {user.id} ({username})", "auth")
            trace(f"Детали неавторизованного доступа: user_id={user.id}, username={username}, first_name={user.first_name}, last_name={user.last_name}", "auth")
            trace_function_exit("AllowedUserFilter.__call__", result="access_denied", logger_name="auth")
        else:
            info(f"Авторизованный доступ от пользователя {user.id} ({username})", "auth")
            trace(f"Детали авторизованного доступа: user_id={user.id}, username={username}, first_name={user.first_name}, last_name={user.last_name}", "auth")
            trace_function_exit("AllowedUserFilter.__call__", result="access_granted", logger_name="auth")
        
        return is_allowed
