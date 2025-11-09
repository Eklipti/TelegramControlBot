# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Декораторы для автоматического сбора метрик.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional

from ..core.logging import error, trace_function_entry, trace_function_exit
from ..services.metrics import get_metrics_collector


def _extract_user_id(args: tuple) -> Optional[int]:
    """Извлекает user_id из аргументов (обычно первый аргумент - это Message)."""
    if args and hasattr(args[0], 'from_user') and args[0].from_user:
        return args[0].from_user.id
    return None


def _track_command_execution(cmd_name: str, user_id: Optional[int], args: tuple):
    """Общая логика отслеживания выполнения команды."""
    if user_id:
        get_metrics_collector().record_user_session(user_id, "start")
    
    start_time = time.time()
    success = True
    error_msg = None
    
    class ExecutionContext:
        def __enter__(self):
            trace_function_entry(f"tracked_command_{cmd_name}", 
                               args=(user_id,), 
                               logger_name="metrics_decorator")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            nonlocal success, error_msg
            
            if exc_type is not None:
                success = False
                error_msg = str(exc_val)
                error(f"Ошибка в команде {cmd_name}: {exc_val}", "metrics_decorator")
                
                # Записываем ошибку в метрики
                get_metrics_collector().record_error(
                    error_type=exc_type.__name__,
                    user_id=user_id or 0,
                    error_msg=error_msg,
                    context={"command": cmd_name, "args": str(args)[:200]}
                )
                
                trace_function_exit(f"tracked_command_{cmd_name}", 
                                  result=f"error: {exc_val}", 
                                  logger_name="metrics_decorator")
            else:
                trace_function_exit(f"tracked_command_{cmd_name}", 
                                  result="success", 
                                  logger_name="metrics_decorator")
            
            # Записываем метрики выполнения
            execution_time = time.time() - start_time
            get_metrics_collector().record_command_execution(
                command=cmd_name,
                user_id=user_id or 0,
                execution_time=execution_time,
                success=success,
                error_msg=error_msg
            )
            
            # Записываем конец сессии пользователя
            if user_id:
                get_metrics_collector().record_user_session(user_id, "end")
    
    return ExecutionContext()


def track_command_metrics(command_name: str = None):
    """
    Декоратор для автоматического сбора метрик выполнения команд.
    
    Args:
        command_name: Имя команды для метрик. Если не указано, используется имя функции.
    """
    def decorator(func: Callable) -> Callable:
        cmd_name = command_name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                user_id = _extract_user_id(args)
                with _track_command_execution(cmd_name, user_id, args):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                user_id = _extract_user_id(args)
                with _track_command_execution(cmd_name, user_id, args):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


def track_performance(func: Callable) -> Callable:
    """
    Декоратор для отслеживания производительности функций.
    """
    def _record_metrics(execution_time: float, success: bool):
        """Записывает метрики производительности."""
        metrics = get_metrics_collector().performance_metrics
        metrics["response_times"].append(execution_time)
        metrics["error_rate"].append(0 if success else 1)
    
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = True
            try:
                return await func(*args, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                _record_metrics(time.time() - start_time, success)
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = True
            try:
                return func(*args, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                _record_metrics(time.time() - start_time, success)
        return sync_wrapper
