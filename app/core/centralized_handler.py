# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Централизованный обработчик логирования как logging.Handler.
"""

import logging
from typing import Any, Dict, Optional

from ..services.centralized_logging import get_centralized_logger


class CentralizedLoggingHandler(logging.Handler):
    """Обработчик логирования, который форвардит записи в централизованную систему."""
    
    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self.centralized_logger = get_centralized_logger()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Обрабатывает запись лога и отправляет в централизованную систему."""
        try:
            # Преобразуем уровень логирования в строку
            level_name = logging.getLevelName(record.levelno)
            
            # Извлекаем дополнительную информацию из record
            extra_data = {}
            if hasattr(record, 'extra_data'):
                extra_data = record.extra_data
            elif hasattr(record, 'args') and record.args:
                # Если есть аргументы, добавляем их как extra_data
                extra_data = {'args': record.args}
            
            # Добавляем информацию о функции и модуле
            extra_data.update({
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno,
                'pathname': record.pathname,
                'process': record.process,
                'thread': record.thread,
                'threadName': record.threadName
            })
            
            # Специальная обработка для TRACE уровня
            if record.levelno == 5:  # TRACE level
                # Проверяем, является ли это специальным TRACE сообщением
                message = record.getMessage()
                if message.startswith("ENTER: "):
                    extra_data['type'] = 'function_entry'
                    # Извлекаем имя функции из сообщения
                    function_name = message[7:].split('(')[0]
                    extra_data['function_name'] = function_name
                elif message.startswith("EXIT: "):
                    extra_data['type'] = 'function_exit'
                    # Извлекаем имя функции из сообщения
                    function_name = message[6:].split(' ')[0]
                    extra_data['function_name'] = function_name
                elif message.startswith("STEP: "):
                    extra_data['type'] = 'step'
                    extra_data['step'] = message[6:]
            
            # Отправляем в централизованную систему
            self.centralized_logger.add_log(
                level=level_name,
                message=record.getMessage(),
                logger_name=record.name,
                extra_data=extra_data
            )
            
        except Exception:
            # В случае ошибки в обработчике, не поднимаем исключение
            # чтобы не нарушить работу основного логирования
            self.handleError(record)
