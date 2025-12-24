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

import os
from pathlib import Path
from dotenv import load_dotenv
from ..core.logging import warning


class Settings:
    """Конфигурация приложения TelegramControlBot."""

    def __init__(self) -> None:
        """Загружает настройки из переменных окружения."""
        # Загружаем .env файл если существует
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Обязательные параметры
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения или .env файле")

        # Опциональные параметры
        self.allowed_user_ids: str = os.getenv("ALLOWED_USER_IDS", "")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Валидация log_level
        valid_levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            warning(f"Неверный log_level '{self.log_level}', используется INFO", "config")
            self.log_level = "INFO"

        # Кодировка
        if os.name == "nt":
            self.encoding: str = "cp1251"
        else:
            self.encoding: str = os.getenv("ENCODING", "utf-8")

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
            return "cp1251"
        return os.device_encoding(1) or "utf-8"

    def get_project_root(self) -> Path:
        """Возвращает корневую директорию проекта (по наличию main.py)."""
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "main.py").exists():
                return current
            current = current.parent
        warning("main.py не найден ни в одном из родителей, fallback на parent.parent", "config")
        return Path(__file__).parent.parent


# Глобальный экземпляр настроек (инициализируется при первом обращении)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Возвращает текущие настройки приложения."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Перезагружает настройки из переменных окружения."""
    global _settings
    _settings = Settings()
    return _settings


# Экспорт
__all__ = ["Settings", "get_settings", "reload_settings"]
