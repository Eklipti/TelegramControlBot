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
            level_name = logging.getLevelName(record.levelno)
            
            extra_data = {}
            if hasattr(record, 'extra_data'):
                extra_data = record.extra_data
            elif hasattr(record, 'args') and record.args:
                extra_data = {'args': record.args}
            
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
                message = record.getMessage()
                if message.startswith("ENTER: "):
                    extra_data['type'] = 'function_entry'
                    function_name = message[7:].split('(')[0]
                    extra_data['function_name'] = function_name
                elif message.startswith("EXIT: "):
                    extra_data['type'] = 'function_exit'
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
