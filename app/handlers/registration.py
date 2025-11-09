# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Единое место регистрации всех handlers для избежания циклических импортов.
Все handlers регистрируются через декораторы @router.message/@router.callback_query
в своих модулях, поэтому импорта модулей достаточно для их активации.
"""

from aiogram import Dispatcher

# Импортируем все handlers для активации декораторов
from . import (
    attachments,
    auth,
    cancel,
    cmd,
    command_search,
    files,
    help,
    logs_export,
    menu,
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
    """
    Регистрирует все handlers в Dispatcher.
    
    Фактически, все handlers уже зарегистрированы через декораторы при импорте модулей выше.
    Эта функция существует для явного вызова из app.py и обеспечения
    правильного порядка инициализации.
    """
    # Handlers уже зарегистрированы через декораторы при импорте
    pass
