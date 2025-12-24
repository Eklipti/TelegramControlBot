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
Конфигурация путей для TelegramControlBot
Единый источник правды для всех путей в приложении
"""

import json
import os
from pathlib import Path
from typing import Any


class PathsConfig:
    """Конфигурация путей"""

    def __init__(
        self,
        default_paths_file: str | Path = "jsons/DEFAULT_PATHS.json",
        jsons_dir: str | Path = "jsons",
    ) -> None:
        """Инициализирует конфигурацию путей"""
        self.default_paths_file = Path(default_paths_file) if isinstance(default_paths_file, str) else default_paths_file
        self.jsons_dir = Path(jsons_dir) if isinstance(jsons_dir, str) else jsons_dir
        
        self.default_paths: dict[str, Any] = {}
        self.user_paths: dict[int, dict[str, Any]] = {}  # telegram_id -> paths
        
        self.load_default_paths()
        self.load_all_user_paths()

    def load_default_paths(self) -> None:
        """Загружает системные пути из DEFAULT_PATHS.json и системного PATH"""
        # Всегда генерируем пути из PATH заново для актуальности
        self.default_paths = {}
        
        # Загружаем системные пути из PATH
        self._load_system_paths()

    def _load_system_paths(self) -> None:
        """Загружает системные пути из переменной PATH"""
        system_path = os.environ.get("PATH", "")
        if not system_path:
            return

        # Разрешенные расширения исполняемых файлов для Windows
        executable_extensions = {".exe", ".bat", ".cmd", ".com", ".vbs", ".ps1", ".msc"}
        
        # Парсим PATH и находим исполняемые файлы
        path_dirs = [p.strip() for p in system_path.split(os.pathsep) if p.strip()]
        
        for path_dir in path_dirs:
            if not os.path.exists(path_dir):
                continue
                
            try:
                for item in os.listdir(path_dir):
                    item_path = os.path.join(path_dir, item)
                    if not os.path.isfile(item_path):
                        continue
                    
                    # Получаем расширение файла
                    _, ext = os.path.splitext(item)
                    
                    # Фильтруем только исполняемые файлы
                    if os.name == "nt":  # Windows
                        if ext.lower() not in executable_extensions:
                            continue
                    else:  # Linux/Mac
                        if not os.access(item_path, os.X_OK):
                            continue
                    
                    # Получаем имя файла без расширения
                    name = os.path.splitext(item)[0]
                    if name and name not in self.default_paths:
                        self.default_paths[name] = os.path.abspath(item_path)
            except (OSError, PermissionError):
                continue

        # Сохраняем обновленные системные пути
        self.save_default_paths()

    def load_all_user_paths(self) -> None:
        """Загружает все пользовательские пути из папок пользователей"""
        jsons_path = Path(self.jsons_dir) if isinstance(self.jsons_dir, str) else self.jsons_dir
        
        if not jsons_path.exists():
            return

        self.user_paths = {}
        
        # Ищем папки пользователей (числовые имена)
        for item in jsons_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                user_id = int(item.name)
                user_paths_file = item / f"{user_id}_paths.json"
                
                if user_paths_file.exists():
                    try:
                        with open(user_paths_file, encoding="utf-8") as f:
                            self.user_paths[user_id] = json.load(f)
                    except Exception as e:
                        print(f"Ошибка загрузки {user_paths_file}: {e}")
                        self.user_paths[user_id] = {}

    def load_user_paths(self, user_id: int) -> dict[str, Any]:
        """Загружает пути конкретного пользователя"""
        if user_id in self.user_paths:
            return self.user_paths[user_id]
        
        # Загружаем из файла
        user_paths_file = self._get_user_paths_file(user_id)
        if user_paths_file.exists():
            try:
                with open(user_paths_file, encoding="utf-8") as f:
                    self.user_paths[user_id] = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки {user_paths_file}: {e}")
                self.user_paths[user_id] = {}
        else:
            self.user_paths[user_id] = {}
        
        return self.user_paths[user_id]

    def _get_user_paths_file(self, user_id: int) -> Path:
        """Возвращает путь к файлу пользовательских путей"""
        jsons_path = Path(self.jsons_dir) if isinstance(self.jsons_dir, str) else self.jsons_dir
        user_dir = jsons_path / str(user_id)
        return user_dir / f"{user_id}_paths.json"

    def save_user_paths(self, user_id: int) -> None:
        """Сохраняет пользовательские пути конкретного пользователя"""
        if user_id not in self.user_paths:
            return

        user_paths_file = self._get_user_paths_file(user_id)
        # Создаем директорию если не существует
        user_paths_file.parent.mkdir(parents=True, exist_ok=True)

        with open(user_paths_file, "w", encoding="utf-8") as f:
            json.dump(self.user_paths[user_id], f, indent=4, ensure_ascii=False)

    def save_default_paths(self) -> None:
        """Сохраняет системные пути в DEFAULT_PATHS.json"""
        path = Path(self.default_paths_file) if isinstance(self.default_paths_file, str) else self.default_paths_file
        # Создаем директорию если не существует
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.default_paths, f, indent=4, ensure_ascii=False)

    def get_all_paths(self, user_id: int) -> dict[str, Any]:
        """Возвращает объединенные пути для конкретного пользователя: пользовательские + системные"""
        user_paths = self.load_user_paths(user_id)
        all_paths = self.default_paths.copy()
        all_paths.update(user_paths)
        return all_paths

    def add_user_path(self, user_id: int, name: str, path: str) -> bool:
        """Добавляет пользовательский путь"""
        if not os.path.exists(path):
            return False

        # Загружаем пути пользователя
        user_paths = self.load_user_paths(user_id)
        user_paths[name] = os.path.abspath(path)
        self.user_paths[user_id] = user_paths
        self.save_user_paths(user_id)
        return True

    def remove_user_path(self, user_id: int, name: str) -> bool:
        """Удаляет пользовательский путь"""
        user_paths = self.load_user_paths(user_id)
        if name in user_paths:
            del user_paths[name]
            self.user_paths[user_id] = user_paths
            self.save_user_paths(user_id)
            return True
        return False

    def get_path(self, user_id: int, name: str) -> str | None:
        """Получает путь по имени для конкретного пользователя (приоритет у пользовательских)"""
        user_paths = self.load_user_paths(user_id)
        return user_paths.get(name) or self.default_paths.get(name)

    def reload_paths(self) -> None:
        """Перезагружает все пути из файлов"""
        self.load_default_paths()
        self.load_all_user_paths()

    def get_stats(self, user_id: int = None) -> dict[str, int]:
        """Возвращает статистику путей"""
        if user_id is not None:
            user_paths = self.load_user_paths(user_id)
            return {
                "user_paths": len(user_paths),
                "default_paths": len(self.default_paths),
                "total_paths": len(self.get_all_paths(user_id)),
            }
        else:
            return {
                "default_paths": len(self.default_paths),
                "total_users": len(self.user_paths),
            }


# Глобальный экземпляр конфигурации путей
_paths_config: PathsConfig | None = None


def get_paths_config() -> PathsConfig:
    """Получить глобальный экземпляр конфигурации путей"""
    global _paths_config
    if _paths_config is None:
        _paths_config = PathsConfig()
    return _paths_config


def init_paths_config() -> PathsConfig:
    """Инициализирует конфигурацию путей"""
    global _paths_config
    _paths_config = PathsConfig()
    return _paths_config