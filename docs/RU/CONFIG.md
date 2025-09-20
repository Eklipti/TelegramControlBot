# Конфигурация ControlBot

ControlBot v2.2.1+ использует Pydantic Settings для управления конфигурацией приложения. Все настройки могут быть заданы через переменные окружения или .env файл.

## Основные настройки

### Токены и аутентификация
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота (обязательный)
- `ALLOWED_USER_IDS` - список разрешенных пользователей через запятую

### Режим отображения
- `GUI_ENABLED` - включить GUI режим (по умолчанию: true)
  - `true`/`1`/`yes` - режим с графическим интерфейсом
  - `false`/`0`/`no` - headless режим без GUI

### Логирование
- `LOG_LEVEL` - уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Пути к файлам
- `DEFAULT_PATHS_FILE` - файл с путями по умолчанию (по умолчанию: jsons/DEFAULT_PATHS.json)
- `LOGS_DIRECTORY` - директория для логов (по умолчанию: logs)

### Система
- `ENCODING` - кодировка (автоматически cp866 для Windows, utf-8 для Unix)

## Использование в коде

```python
from app.config import get_settings, Settings

# Получение настроек
settings = get_settings()

# Проверка пользователя
if settings.is_user_allowed(user_id):
    # пользователь разрешен

# Получение списка разрешенных пользователей
allowed_users = settings.get_allowed_user_ids()

# Создание необходимых директорий
settings.ensure_directories()

# Перезагрузка настроек
reload_settings()
```

## Валидация настроек

Система автоматически валидирует:
- Уровень логирования (только допустимые значения)
- Режимы работы (нельзя одновременно использовать GUI и headless)
- Кодировку (автоматическая установка для Windows)
- Формат списка пользователей

## Пример .env файла

```env
# Обязательные настройки
TELEGRAM_BOT_TOKEN=your_bot_token_here
ALLOWED_USER_IDS=123456789,987654321

# Режим отображения
GUI_ENABLED=true

# Логирование
LOG_LEVEL=INFO

# Пути к файлам
DEFAULT_PATHS_FILE=jsons/DEFAULT_PATHS.json
LOGS_DIRECTORY=logs
```
