# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Декораторы для автоматического сбора метрик.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional

from ..core.logging import error, trace, trace_function_entry, trace_function_exit
from ..services.metrics import get_metrics_collector


def track_command_metrics(command_name: str = None):
    """
    Декоратор для автоматического сбора метрик выполнения команд.
    
    Args:
        command_name: Имя команды для метрик. Если не указано, используется имя функции.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Определяем имя команды
            cmd_name = command_name or func.__name__
            
            # Извлекаем user_id из аргументов (обычно первый аргумент - это Message)
            user_id = None
            if args and hasattr(args[0], 'from_user') and args[0].from_user:
                user_id = args[0].from_user.id
            
            # Записываем начало сессии пользователя
            if user_id:
                get_metrics_collector().record_user_session(user_id, "start")
            
            start_time = time.time()
            success = True
            error_msg = None
            
            try:
                trace_function_entry(f"tracked_command_{cmd_name}", 
                                   args=(user_id,), 
                                   logger_name="metrics_decorator")
                
                result = await func(*args, **kwargs)
                
                trace_function_exit(f"tracked_command_{cmd_name}", 
                                  result="success", 
                                  logger_name="metrics_decorator")
                return result
                
            except Exception as e:
                success = False
                error_msg = str(e)
                error(f"Ошибка в команде {cmd_name}: {e}", "metrics_decorator")
                
                # Записываем ошибку в метрики
                get_metrics_collector().record_error(
                    error_type=type(e).__name__,
                    user_id=user_id or 0,
                    error_msg=error_msg,
                    context={"command": cmd_name, "args": str(args)[:200]}
                )
                
                trace_function_exit(f"tracked_command_{cmd_name}", 
                                  result=f"error: {e}", 
                                  logger_name="metrics_decorator")
                raise
                
            finally:
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
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Для синхронных функций
            cmd_name = command_name or func.__name__
            
            user_id = None
            if args and hasattr(args[0], 'from_user') and args[0].from_user:
                user_id = args[0].from_user.id
            
            if user_id:
                get_metrics_collector().record_user_session(user_id, "start")
            
            start_time = time.time()
            success = True
            error_msg = None
            
            try:
                trace_function_entry(f"tracked_command_{cmd_name}", 
                                   args=(user_id,), 
                                   logger_name="metrics_decorator")
                
                result = func(*args, **kwargs)
                
                trace_function_exit(f"tracked_command_{cmd_name}", 
                                  result="success", 
                                  logger_name="metrics_decorator")
                return result
                
            except Exception as e:
                success = False
                error_msg = str(e)
                error(f"Ошибка в команде {cmd_name}: {e}", "metrics_decorator")
                
                get_metrics_collector().record_error(
                    error_type=type(e).__name__,
                    user_id=user_id or 0,
                    error_msg=error_msg,
                    context={"command": cmd_name, "args": str(args)[:200]}
                )
                
                trace_function_exit(f"tracked_command_{cmd_name}", 
                                  result=f"error: {e}", 
                                  logger_name="metrics_decorator")
                raise
                
            finally:
                execution_time = time.time() - start_time
                get_metrics_collector().record_command_execution(
                    command=cmd_name,
                    user_id=user_id or 0,
                    execution_time=execution_time,
                    success=success,
                    error_msg=error_msg
                )
                
                if user_id:
                    get_metrics_collector().record_user_session(user_id, "end")
        
        # Возвращаем соответствующую обертку
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_performance(func: Callable) -> Callable:
    """
    Декоратор для отслеживания производительности функций.
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        success = True
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            
            # Записываем метрики производительности
            metrics = get_metrics_collector().performance_metrics
            metrics["response_times"].append(execution_time)
            
            if not success:
                metrics["error_rate"].append(1)
            else:
                metrics["error_rate"].append(0)
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            
            metrics = get_metrics_collector().performance_metrics
            metrics["response_times"].append(execution_time)
            
            if not success:
                metrics["error_rate"].append(1)
            else:
                metrics["error_rate"].append(0)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
