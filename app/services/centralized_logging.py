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
Централизованная система логирования с экспортом в разные форматы.
"""

import asyncio
import csv
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Удален импорт для избежания циклической зависимости


class CentralizedLogger:
    """Централизованная система логирования с возможностью экспорта."""
    
    def __init__(self, logs_dir: str = "./logs", export_dir: str = "./exports"):
        self.logs_dir = Path(logs_dir)
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
        # Централизованное хранилище логов
        self.centralized_logs: List[Dict[str, Any]] = []
        self.max_logs_in_memory = 10000  # Максимум логов в памяти
        
        # Статистика логирования
        self.log_stats = {
            "total_logs": 0,
            "logs_by_level": {},
            "logs_by_logger": {},
            "errors_count": 0,
            "warnings_count": 0
        }
        
        # Логирование инициализации через стандартный logging
        self._logger = logging.getLogger("centralized_logging")
        self._logger.info("Централизованная система логирования инициализирована")
    
    def add_log(
        self, 
        level: str, 
        message: str, 
        logger_name: str = "main",
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Добавляет лог в централизованное хранилище."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "logger_name": logger_name,
            "extra_data": extra_data or {}
        }
        
        # Добавляем в централизованное хранилище
        self.centralized_logs.append(log_entry)
        
        # Ограничиваем размер в памяти
        if len(self.centralized_logs) > self.max_logs_in_memory:
            self.centralized_logs = self.centralized_logs[-self.max_logs_in_memory:]
        
        # Обновляем статистику
        self.log_stats["total_logs"] += 1
        self.log_stats["logs_by_level"][level] = self.log_stats["logs_by_level"].get(level, 0) + 1
        self.log_stats["logs_by_logger"][logger_name] = self.log_stats["logs_by_logger"].get(logger_name, 0) + 1
        
        if level == "ERROR":
            self.log_stats["errors_count"] += 1
        elif level == "WARNING":
            self.log_stats["warnings_count"] += 1
    
    def get_logs(
        self, 
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Получает логи с фильтрацией."""
        filtered_logs = self.centralized_logs.copy()
        
        # Фильтрация по уровню
        if level:
            filtered_logs = [log for log in filtered_logs if log["level"] == level]
        
        # Фильтрация по логгеру
        if logger_name:
            filtered_logs = [log for log in filtered_logs if log["logger_name"] == logger_name]
        
        # Фильтрация по времени
        if start_time:
            filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log["timestamp"]) >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if datetime.fromisoformat(log["timestamp"]) <= end_time]
        
        # Ограничение количества
        result = filtered_logs[-limit:] if limit > 0 else filtered_logs
        
        return result
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику логирования."""
        stats = self.log_stats.copy()
        
        # Добавляем дополнительную информацию
        if self.centralized_logs:
            latest_log = self.centralized_logs[-1]
            oldest_log = self.centralized_logs[0]
            stats["latest_log_time"] = latest_log["timestamp"]
            stats["oldest_log_time"] = oldest_log["timestamp"]
        
        return stats
    
    async def export_to_json(self, filename: Optional[str] = None) -> str:
        """Экспортирует логи в JSON формат."""
        try:
            if not filename:
                filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_path = self.export_dir / filename
            
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_logs": len(self.centralized_logs),
                    "export_format": "json"
                },
                "statistics": self.get_log_statistics(),
                "logs": self.centralized_logs
            }
            
            # Выносим блокирующую операцию записи в отдельный поток
            def _write_json():
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            await asyncio.to_thread(_write_json)
            
            self._logger.info(f"Логи экспортированы в JSON: {export_path}")
            return str(export_path)
            
        except Exception as e:
            self._logger.error(f"Ошибка экспорта в JSON: {e}")
            raise
    
    async def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Экспортирует логи в CSV формат."""
        try:
            if not filename:
                filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            export_path = self.export_dir / filename
            
            # Выносим блокирующую операцию записи в отдельный поток
            def _write_csv():
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    if not self.centralized_logs:
                        return
                    
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'level', 'logger_name', 'message', 'extra_data'])
                    writer.writeheader()
                    
                    for log in self.centralized_logs:
                        csv_log = {
                            'timestamp': log['timestamp'],
                            'level': log['level'],
                            'logger_name': log['logger_name'],
                            'message': log['message'],
                            'extra_data': json.dumps(log['extra_data'], ensure_ascii=False)
                        }
                        writer.writerow(csv_log)
            
            await asyncio.to_thread(_write_csv)
            
            self._logger.info(f"Логи экспортированы в CSV: {export_path}")
            return str(export_path)
            
        except Exception as e:
            self._logger.error(f"Ошибка экспорта в CSV: {e}")
            raise
    
    async def export_to_xml(self, filename: Optional[str] = None) -> str:
        """Экспортирует логи в XML формат."""
        try:
            if not filename:
                filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            
            export_path = self.export_dir / filename
            
            # Создаем корневой элемент
            root = ET.Element("logs")
            root.set("export_timestamp", datetime.now().isoformat())
            root.set("total_logs", str(len(self.centralized_logs)))
            
            # Добавляем статистику
            stats_elem = ET.SubElement(root, "statistics")
            for key, value in self.get_log_statistics().items():
                stat_elem = ET.SubElement(stats_elem, key)
                stat_elem.text = str(value)
            
            # Добавляем логи
            logs_elem = ET.SubElement(root, "log_entries")
            for log in self.centralized_logs:
                log_elem = ET.SubElement(logs_elem, "log")
                log_elem.set("timestamp", log['timestamp'])
                log_elem.set("level", log['level'])
                log_elem.set("logger", log['logger_name'])
                
                message_elem = ET.SubElement(log_elem, "message")
                message_elem.text = log['message']
                
                if log['extra_data']:
                    extra_elem = ET.SubElement(log_elem, "extra_data")
                    extra_elem.text = json.dumps(log['extra_data'], ensure_ascii=False)
            
            # Выносим блокирующую операцию записи в отдельный поток
            def _write_xml():
                tree = ET.ElementTree(root)
                tree.write(export_path, encoding='utf-8', xml_declaration=True)
            
            await asyncio.to_thread(_write_xml)
            
            self._logger.info(f"Логи экспортированы в XML: {export_path}")
            return str(export_path)
            
        except Exception as e:
            self._logger.error(f"Ошибка экспорта в XML: {e}")
            raise
    
    async def export_to_text(self, filename: Optional[str] = None) -> str:
        """Экспортирует логи в текстовый формат."""
        try:
            if not filename:
                filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            export_path = self.export_dir / filename
            
            # Выносим блокирующую операцию записи в отдельный поток
            def _write_text():
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(f"TelegramControlBot Logs Export\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write(f"Total logs: {len(self.centralized_logs)}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for log in self.centralized_logs:
                        timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        f.write(f"[{timestamp}] {log['level']:8} | {log['logger_name']:15} | {log['message']}\n")
                        
                        if log['extra_data']:
                            f.write(f"  Extra data: {json.dumps(log['extra_data'], ensure_ascii=False)}\n")
                        
                        f.write("\n")
            
            await asyncio.to_thread(_write_text)
            
            self._logger.info(f"Логи экспортированы в TXT: {export_path}")
            return str(export_path)
            
        except Exception as e:
            self._logger.error(f"Ошибка экспорта в TXT: {e}")
            raise
    
    async def cleanup_old_exports(self, days_to_keep: int = 30) -> None:
        """Очищает старые файлы экспорта."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for file_path in self.export_dir.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
            
            self._logger.info(f"Удалено {deleted_count} старых файлов экспорта")
            
        except Exception as e:
            self._logger.error(f"Ошибка очистки старых экспортов: {e}")


# Глобальный экземпляр централизованного логгера
centralized_logger: Optional[CentralizedLogger] = None


def init_centralized_logging(logs_dir: str = "./logs", export_dir: str = "./exports") -> CentralizedLogger:
    """Инициализирует централизованную систему логирования."""
    global centralized_logger
    if centralized_logger is None:
        centralized_logger = CentralizedLogger(logs_dir, export_dir)
    return centralized_logger


def get_centralized_logger() -> CentralizedLogger:
    """Возвращает глобальный централизованный логгер."""
    global centralized_logger
    if centralized_logger is None:
        centralized_logger = CentralizedLogger()
    return centralized_logger
