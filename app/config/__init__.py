# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация приложения ControlBot с использованием Pydantic Settings."""

    # Токены и аутентификация
    telegram_bot_token: str = Field(..., description="Токен Telegram бота")
    allowed_user_ids: str = Field(default="", description="Список разрешенных пользователей (через запятую)")

    # Режим отображения
    gui_enabled: bool = Field(default=True, description="Включить GUI режим (True = GUI, False = Headless)")

    # Уровень логирования
    log_level: str = Field(default="INFO", description="Уровень логирования")

    # Пути к файлам и директориям (относительно корня проекта)
    default_paths_file: str = Field(default="jsons/DEFAULT_PATHS.json", description="Файл с путями по умолчанию")
    logs_directory: str = Field(default="logs", description="Директория для логов")
    data_directory: str = Field(default="data", description="Директория для данных/метрик")
    exports_directory: str = Field(default="exports", description="Директория для экспортов/выгрузок")

    # Настройки системы
    encoding: str = Field(default="cp866" if os.name == "nt" else "utf-8", description="Кодировка для Windows")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level должен быть одним из: {valid_levels}")
        return v.upper()

    @field_validator("encoding")
    @classmethod
    def set_windows_encoding(cls, v):
        """Установка кодировки для Windows."""
        if os.name == "nt":
            return "cp866"
        return v


    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "",
        "extra": "ignore",
    }

    @classmethod
    def load_from_env(cls) -> "Settings":
        """Загружает настройки из переменных окружения."""
        # Загружаем .env файл если существует
        env_file = Path(".env")
        if env_file.exists():
            cls.model_config["env_file"] = str(env_file)

        return cls()

    def get_allowed_user_ids(self) -> list[int]:
        """Возвращает список разрешенных пользователей."""
        if not self.allowed_user_ids:
            return []

        allowed: list[int] = []
        for part in self.allowed_user_ids.replace(";", ",").split(","):
            part = part.strip()
            if not part:
                continue
            try:
                allowed.append(int(part))
            except ValueError:
                continue
        return allowed

    def is_user_allowed(self, user_id: int) -> bool:
        """Проверяет, разрешен ли пользователь."""
        return user_id in self.get_allowed_user_ids()

    def get_encoding(self) -> str:
        """Возвращает кодировку для текущей системы."""
        if os.name == "nt":
            return "cp866"
        return os.device_encoding(1) or "utf-8"

    @property
    def gui_mode(self) -> bool:
        """Обратная совместимость: возвращает gui_enabled."""
        return self.gui_enabled

    @property
    def headless_mode(self) -> bool:
        """Обратная совместимость: возвращает not gui_enabled."""
        return not self.gui_enabled

    def get_project_root(self) -> Path:
        """Возвращает корневую директорию проекта."""
        # Ищем корень проекта по наличию pyproject.toml
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        # Если не найден, возвращаем директорию с main.py
        return Path(__file__).parent.parent

    def get_default_paths_file(self) -> Path:
        """Возвращает абсолютный путь к файлу DEFAULT_PATHS.json."""
        return self.get_project_root() / self.default_paths_file


    def get_logs_directory(self) -> Path:
        """Возвращает абсолютный путь к директории логов."""
        return self.get_project_root() / self.logs_directory

    def get_data_directory(self) -> Path:
        """Возвращает абсолютный путь к директории данных/метрик."""
        return self.get_project_root() / self.data_directory

    def get_exports_directory(self) -> Path:
        """Возвращает абсолютный путь к директории экспортов/выгрузок."""
        return self.get_project_root() / self.exports_directory

    def ensure_directories(self) -> None:
        """Создает необходимые директории."""
        self.get_logs_directory().mkdir(parents=True, exist_ok=True)
        self.get_data_directory().mkdir(parents=True, exist_ok=True)
        self.get_exports_directory().mkdir(parents=True, exist_ok=True)
        (self.get_project_root() / "jsons").mkdir(parents=True, exist_ok=True)


# Глобальный экземпляр настроек (инициализируется при первом обращении)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Возвращает текущие настройки приложения."""
    global _settings
    if _settings is None:
        _settings = Settings.load_from_env()
    return _settings


def reload_settings() -> Settings:
    """Перезагружает настройки из переменных окружения."""
    global _settings
    _settings = Settings.load_from_env()
    return _settings


# Экспорт для обратной совместимости
__all__ = ["Settings", "get_settings", "reload_settings", "get_encoding", "is_user_allowed", "load_env"]


# Функции для обратной совместимости
def get_encoding() -> str:
    """DEPRECATED: Используйте settings.get_encoding()"""
    import warnings

    warnings.warn(
        "Функция get_encoding() устарела. Используйте settings.get_encoding()", DeprecationWarning, stacklevel=2
    )
    if os.name == "nt":
        return "cp866"
    return os.device_encoding(1) or "utf-8"


def is_user_allowed(user_id: int, allowed_users: list[int]) -> bool:
    """DEPRECATED: Используйте settings.is_user_allowed()"""
    import warnings

    warnings.warn(
        "Функция is_user_allowed() устарела. Используйте settings.is_user_allowed()", DeprecationWarning, stacklevel=2
    )
    return user_id in allowed_users


def load_env(path: str = ".env") -> None:
    """DEPRECATED: Используйте Settings.load_from_env()"""
    import warnings

    warnings.warn("Функция load_env() устарела. Используйте Settings.load_from_env()", DeprecationWarning, stacklevel=2)
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f.readlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass
