# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Система сбора метрик и статистики для ControlBot.
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logging import debug, error, info, log_call


class MetricsCollector:
    """Сборщик метрик для мониторинга производительности и использования."""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Метрики команд
        self.command_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "errors": 0,
            "last_used": None,
            "users": set()
        })
        
        # Метрики пользователей
        self.user_stats: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            "commands_used": 0,
            "total_time": 0.0,
            "last_activity": None,
            "favorite_commands": defaultdict(int),
            "sessions": 0,
            "current_session_start": None
        })
        
        # Метрики производительности
        self.performance_metrics = {
            "memory_usage": deque(maxlen=1000),
            "response_times": deque(maxlen=1000),
            "error_rate": deque(maxlen=100),
            "active_sessions": 0,
            "uptime_start": time.time()
        }
        
        # Паттерны использования
        self.usage_patterns = {
            "hourly_usage": defaultdict(int),
            "daily_usage": defaultdict(int),
            "command_sequences": defaultdict(int),
            "peak_hours": [],
            "user_activity_waves": []
        }
        
        # Аудит-трейлы
        self.audit_trails: List[Dict[str, Any]] = []
        
        info("Система метрик инициализирована", "metrics")
    
    @log_call("metrics")
    def record_command_execution(
        self, 
        command: str, 
        user_id: int, 
        execution_time: float, 
        success: bool = True,
        error_msg: Optional[str] = None
    ) -> None:
        """Записывает выполнение команды."""
        
        current_time = datetime.now()
        
        # Обновляем статистику команды
        cmd_stats = self.command_stats[command]
        cmd_stats["count"] += 1
        cmd_stats["total_time"] += execution_time
        cmd_stats["avg_time"] = cmd_stats["total_time"] / cmd_stats["count"]
        cmd_stats["min_time"] = min(cmd_stats["min_time"], execution_time)
        cmd_stats["max_time"] = max(cmd_stats["max_time"], execution_time)
        cmd_stats["last_used"] = current_time
        cmd_stats["users"].add(user_id)
        
        if not success:
            cmd_stats["errors"] += 1
        
        # Обновляем статистику пользователя
        user_stats = self.user_stats[user_id]
        user_stats["commands_used"] += 1
        user_stats["total_time"] += execution_time
        user_stats["last_activity"] = current_time
        user_stats["favorite_commands"][command] += 1
        
        # Записываем в аудит-трейл
        self._add_audit_trail({
            "timestamp": current_time.isoformat(),
            "event_type": "command_execution",
            "command": command,
            "user_id": user_id,
            "execution_time": execution_time,
            "success": success,
            "error_msg": error_msg
        })
        
        # Обновляем паттерны использования
        self._update_usage_patterns(command, user_id, current_time)
        
        # Обновляем метрики производительности
        self.performance_metrics["response_times"].append(execution_time)
        
        debug(f"Записано выполнение команды {command} пользователем {user_id} за {execution_time:.3f}s", "metrics")
    
    @log_call("metrics")
    def record_user_session(self, user_id: int, session_type: str = "start") -> None:
        """Записывает сессию пользователя."""
        
        current_time = datetime.now()
        user_stats = self.user_stats[user_id]
        
        if session_type == "start":
            user_stats["sessions"] += 1
            user_stats["current_session_start"] = current_time
            self.performance_metrics["active_sessions"] += 1
        elif session_type == "end" and user_stats["current_session_start"]:
            session_duration = (current_time - user_stats["current_session_start"]).total_seconds()
            user_stats["current_session_start"] = None
            self.performance_metrics["active_sessions"] = max(0, self.performance_metrics["active_sessions"] - 1)
            
            # Записываем в аудит-трейл
            self._add_audit_trail({
                "timestamp": current_time.isoformat(),
                "event_type": "session_end",
                "user_id": user_id,
                "session_duration": session_duration
            })
        
    
    @log_call("metrics")
    def record_error(self, error_type: str, user_id: int, error_msg: str, context: Dict[str, Any] = None) -> None:
        """Записывает ошибку."""
        
        current_time = datetime.now()
        
        # Обновляем метрики производительности
        self.performance_metrics["error_rate"].append(1)
        
        # Записываем в аудит-трейл
        self._add_audit_trail({
            "timestamp": current_time.isoformat(),
            "event_type": "error",
            "error_type": error_type,
            "user_id": user_id,
            "error_msg": error_msg,
            "context": context or {}
        })
        
        debug(f"Записана ошибка {error_type} для пользователя {user_id}: {error_msg}", "metrics")
    
    def _add_audit_trail(self, event: Dict[str, Any]) -> None:
        """Добавляет событие в аудит-трейл."""
        self.audit_trails.append(event)
        
        # Ограничиваем размер аудит-трейла (последние 10000 событий)
        if len(self.audit_trails) > 10000:
            self.audit_trails = self.audit_trails[-10000:]
    
    def _update_usage_patterns(self, command: str, user_id: int, timestamp: datetime) -> None:
        """Обновляет паттерны использования."""
        # Почасовое использование
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")
        self.usage_patterns["hourly_usage"][hour_key] += 1
        
        # Дневное использование
        day_key = timestamp.strftime("%Y-%m-%d")
        self.usage_patterns["daily_usage"][day_key] += 1
        
        # Обновляем пиковые часы
        self._update_peak_hours()
    
    def _update_peak_hours(self) -> None:
        """Обновляет список пиковых часов."""
        hourly_data = dict(self.usage_patterns["hourly_usage"])
        if not hourly_data:
            return
        
        # Сортируем по количеству использований
        sorted_hours = sorted(hourly_data.items(), key=lambda x: x[1], reverse=True)
        self.usage_patterns["peak_hours"] = sorted_hours[:10]  # Топ-10 пиковых часов
    
    @log_call("metrics")
    def get_command_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику команд."""
        
        stats = {}
        for command, data in self.command_stats.items():
            stats[command] = {
                "count": data["count"],
                "avg_time": round(data["avg_time"], 3),
                "min_time": round(data["min_time"], 3) if data["min_time"] != float('inf') else 0,
                "max_time": round(data["max_time"], 3),
                "error_rate": round(data["errors"] / data["count"] * 100, 2) if data["count"] > 0 else 0,
                "unique_users": len(data["users"]),
                "last_used": data["last_used"].isoformat() if data["last_used"] else None
            }
        
        return stats
    
    @log_call("metrics")
    def get_user_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику пользователей."""
        
        stats = {}
        for user_id, data in self.user_stats.items():
            favorite_command = max(data["favorite_commands"].items(), key=lambda x: x[1])[0] if data["favorite_commands"] else None
            
            stats[str(user_id)] = {
                "commands_used": data["commands_used"],
                "avg_time_per_command": round(data["total_time"] / data["commands_used"], 3) if data["commands_used"] > 0 else 0,
                "sessions": data["sessions"],
                "favorite_command": favorite_command,
                "last_activity": data["last_activity"].isoformat() if data["last_activity"] else None,
                "is_active": data["current_session_start"] is not None
            }
        
        return stats
    
    @log_call("metrics")
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Возвращает метрики производительности."""
        
        response_times = list(self.performance_metrics["response_times"])
        error_rates = list(self.performance_metrics["error_rate"])
        
        uptime = time.time() - self.performance_metrics["uptime_start"]
        
        metrics = {
            "uptime_seconds": round(uptime, 2),
            "uptime_human": str(timedelta(seconds=int(uptime))),
            "active_sessions": self.performance_metrics["active_sessions"],
            "avg_response_time": round(sum(response_times) / len(response_times), 3) if response_times else 0,
            "min_response_time": round(min(response_times), 3) if response_times else 0,
            "max_response_time": round(max(response_times), 3) if response_times else 0,
            "error_rate_percent": round(sum(error_rates) / len(error_rates) * 100, 2) if error_rates else 0,
            "total_commands": sum(cmd["count"] for cmd in self.command_stats.values()),
            "total_users": len(self.user_stats)
        }
        
        return metrics
    
    @log_call("metrics")
    def get_usage_patterns(self) -> Dict[str, Any]:
        """Возвращает паттерны использования."""
        
        patterns = {
            "peak_hours": self.usage_patterns["peak_hours"],
            "hourly_usage": dict(self.usage_patterns["hourly_usage"]),
            "daily_usage": dict(self.usage_patterns["daily_usage"]),
            "most_used_commands": sorted(
                [(cmd, data["count"]) for cmd, data in self.command_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        return patterns
    
    @log_call("metrics")
    def get_audit_trails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Возвращает аудит-трейлы."""
        
        trails = self.audit_trails[-limit:] if limit > 0 else self.audit_trails
        return trails
    
    @log_call("metrics")
    async def save_metrics(self) -> None:
        """Сохраняет метрики в файл."""
        try:
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "command_stats": {cmd: {**data, "users": list(data["users"])} for cmd, data in self.command_stats.items()},
                "user_stats": {str(uid): {**data, "favorite_commands": dict(data["favorite_commands"])} for uid, data in self.user_stats.items()},
                "performance_metrics": {
                    **self.performance_metrics,
                    "memory_usage": list(self.performance_metrics["memory_usage"]),
                    "response_times": list(self.performance_metrics["response_times"]),
                    "error_rate": list(self.performance_metrics["error_rate"])
                },
                "usage_patterns": self.usage_patterns,
                "audit_trails": self.audit_trails[-1000:]  # Сохраняем последние 1000 событий
            }
            
            # Daily rotate: один файл на дату
            date_str = datetime.now().strftime("%Y-%m-%d")
            metrics_file = self.data_dir / f"metrics_{date_str}.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
            info(f"Метрики сохранены в {metrics_file}", "metrics")
            
        except Exception as e:
            error(f"Ошибка сохранения метрик: {e}", "metrics")
    
    @log_call("metrics")
    async def load_metrics(self) -> None:
        """Загружает метрики из файла."""
        try:
            # Ищем последний файл метрик
            metrics_files = list(self.data_dir.glob("metrics_*.json"))
            if not metrics_files:
                info("Файлы метрик не найдены, начинаем с чистого состояния", "metrics")
                return
            
            latest_file = max(metrics_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                metrics_data = json.load(f)
            
            # Восстанавливаем данные
            self.command_stats = defaultdict(lambda: {
                "count": 0, "total_time": 0.0, "avg_time": 0.0,
                "min_time": float('inf'), "max_time": 0.0, "errors": 0,
                "last_used": None, "users": set()
            })
            
            for cmd, data in metrics_data.get("command_stats", {}).items():
                self.command_stats[cmd].update(data)
                self.command_stats[cmd]["users"] = set(data.get("users", []))
                if data.get("last_used"):
                    self.command_stats[cmd]["last_used"] = datetime.fromisoformat(data["last_used"])
            
            # Восстанавливаем статистику пользователей
            self.user_stats = defaultdict(lambda: {
                "commands_used": 0, "total_time": 0.0, "last_activity": None,
                "favorite_commands": defaultdict(int), "sessions": 0, "current_session_start": None
            })
            
            for user_id_str, data in metrics_data.get("user_stats", {}).items():
                user_id = int(user_id_str)
                self.user_stats[user_id].update(data)
                self.user_stats[user_id]["favorite_commands"] = defaultdict(int, data.get("favorite_commands", {}))
                if data.get("last_activity"):
                    self.user_stats[user_id]["last_activity"] = datetime.fromisoformat(data["last_activity"])
            
            # Восстанавливаем паттерны использования
            self.usage_patterns = metrics_data.get("usage_patterns", {
                "hourly_usage": defaultdict(int),
                "daily_usage": defaultdict(int),
                "command_sequences": defaultdict(int),
                "peak_hours": [],
                "user_activity_waves": []
            })
            
            # Восстанавливаем аудит-трейлы
            self.audit_trails = metrics_data.get("audit_trails", [])
            
            info(f"Метрики загружены из {latest_file}", "metrics")
            
        except Exception as e:
            error(f"Ошибка загрузки метрик: {e}", "metrics")


# Глобальный экземпляр сборщика метрик
metrics_collector: Optional[MetricsCollector] = None


def init_metrics(data_dir: str = "./data") -> MetricsCollector:
    """Инициализирует глобальный сборщик метрик."""
    global metrics_collector
    if metrics_collector is None:
        metrics_collector = MetricsCollector(data_dir)
    return metrics_collector


def get_metrics_collector() -> MetricsCollector:
    """Возвращает глобальный сборщик метрик."""
    global metrics_collector
    if metrics_collector is None:
        metrics_collector = MetricsCollector()
    return metrics_collector
