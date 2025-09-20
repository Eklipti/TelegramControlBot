# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Единое место регистрации всех handlers для избежания циклических импортов
"""

from aiogram import Dispatcher

from . import (
    attachments,
    auth,
    cancel,
    cmd,
    command_search,
    files,
    help,
    logs_export,
    monitor,
    mouse_keyboard,
    paths_handlers,
    processes,
    remote_desktop,
    screen,
    security_handlers,
    stats,
    system,
)


def register_all_handlers(dp: Dispatcher) -> None:
    """Регистрирует все handlers в Dispatcher."""
    # Импортируем handlers в правильном порядке для избежания циклических зависимостей
    
    # Базовые handlers (без зависимостей)
    from . import auth, cancel, help, security_handlers
    
    # Системные handlers
    from . import system, files, processes, monitor
    
    # GUI handlers (с ленивой загрузкой)
    from . import attachments, mouse_keyboard, screen, remote_desktop
    
    # Специализированные handlers
    from . import cmd, command_search, paths_handlers
    
    # Мониторинг и статистика
    from . import stats, logs_export
    
    # Все handlers уже зарегистрированы через декораторы @router.message/@router.callback_query
    # в своих модулях, поэтому дополнительная регистрация не требуется
    pass
