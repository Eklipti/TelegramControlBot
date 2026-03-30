# Руководство по установке TelegramControlBot

Подробное руководство по установке и настройке TelegramControlBot на Windows.

## Содержание

- [Предварительные требования](#предварительные-требования)
- [Автоматическая установка](#автоматическая-установка-рекомендуется)
- [Ручная установка](#ручная-установка)
- [Настройка автозапуска](#настройка-автозапуска)
- [Решение проблем](#решение-проблем)

## Предварительные требования

### Обязательные
- **Windows 10/11** _(разработка проводилась на windows 11)_
- **Python 3.13+** — [Скачать](https://www.python.org/downloads/)
- **Git** (для клонирования) — [Скачать](https://git-scm.com/downloads)
- **Токен Telegram-бота** — получите от [@BotFather](https://t.me/BotFather)
- **Telegram User ID** — получите от [@userinfobot](https://t.me/userinfobot)
- **API ID и API Hash** приложения — получите на [my.telegram.org](https://my.telegram.org) (опционально)

### Проверка Python

Откройте командную строку (Win+R → `cmd`) и выполните:

```bash
python --version
```

Должна отобразиться версия Python 3.13 или выше.

## Автоматическая установка

Самый простой способ установки и настройки бота.

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/Eklipti/TelegramControlBot.git
cd TelegramControlBot
```

### Шаг 2: Запуск setup.bat

Дважды кликните на `setup.bat` или запустите из командной строки:

```bash
setup.bat
```

**Что делает скрипт:**
1. Проверяет наличие и версию Python
2. Создает виртуальное окружение `.venv`
3. Активирует виртуальное окружение
4. Обновляет pip до последней версии
5. Устанавливает все зависимости из `requirements.txt`
6. Создает `.env` файл из `.env.example`
7. Создает необходимые директории

* **Примечание**: путь не должен содержать спец. символов, кириллицы и желательно пробелов. Если таковые имеются, рекомендуется запускать через PowerShell.

### Шаг 3: Настройка .env файла

Откройте файл `.env` в текстовом редакторе (Блокнот, Notepad++, VS Code):

```env
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Telegram API ID
TELEGRAM_API_ID=your_api_id_here

# Telegram API Hash
TELEGRAM_API_HASH=your_api_hash_here

# ID разрешенных пользователей через запятую (получите от @Getmyid_bot)
ALLOWED_USER_IDS=123456789,987654321

# Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

**Обязательные параметры:**
- `TELEGRAM_BOT_TOKEN` - токен вашего бота
- `ALLOWED_USER_IDS` - ваш Telegram ID

### Шаг 4: Запуск бота

Дважды кликните на `start.bat` или запустите:

```bash
start.bat
```

Бот запустится в отдельном окне консоли.

## Управление ботом

### Запуск

```bash
start.bat
```

### Остановка

Закройте окно консоли или нажмите `Ctrl+C`

### Просмотр логов

Логи находятся в директории `logs/`:
- `all.log` - все сообщения
- `error.log` - только ошибки
- `info.log` - информационные сообщения
- `debug.log` - отладочные сообщения

## Настройка автозапуска

### Установка в автозагрузку

Запустите `install_autostart.bat`:

```bash
install_autostart.bat
```

**Что делает скрипт:**
- Создает ярлык на `start.bat` в папке автозагрузки Windows
- Бот будет автоматически запускаться при входе в систему

**Расположение ярлыка:**
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TelegramControlBot.lnk
```

### Удаление из автозагрузки

Запустите `uninstall_autostart.bat`:

```bash
uninstall_autostart.bat
```

Или вручную:
1. Нажмите `Win+R`
2. Введите: `shell:startup`
3. Удалите ярлык `TelegramControlBot.lnk`

## Ручная установка

### Шаг 1: Клонирование

```bash
git clone https://github.com/Eklipti/TelegramControlBot.git
cd TelegramControlBot
```

### Шаг 2: Создание виртуального окружения

```bash
python -m venv .venv
```

### Шаг 3: Активация виртуального окружения

```bash
.venv\Scripts\activate
```

Вы должны увидеть `(.venv)` в начале строки командной строки.

### Шаг 4: Обновление pip

```bash
python -m pip install --upgrade pip
```

### Шаг 5: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Шаг 6: Создание .env файла

```bash
copy .env.example .env
```

Затем отредактируйте `.env` как описано выше.

### Шаг 7: Создание директорий

```bash
mkdir logs data exports
```

### Шаг 8: Запуск

```bash
python main.py
```

## Обновление бота

### Автоматический способ

```bash
# Остановите бота (закройте окно или Ctrl+C)

# Обновите код
git pull

# Запустите setup.bat для обновления зависимостей
setup.bat

# Запустите бота
start.bat
```

### Ручной способ

```bash
# Остановите бота
# Обновите код
git pull

# Активируйте окружение
.venv\Scripts\activate

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Запустите бота
python main.py
```

## Решение проблем

### Python не найден

**Проблема:** При запуске `setup.bat` выводится "Python не найден"

**Решение:**
1. Установите Python 3.11+ с официального сайта
2. При установке обязательно отметьте "Add Python to PATH"
3. Перезапустите командную строку
4. Проверьте: `python --version`

### Не удалось создать виртуальное окружение

**Проблема:** Ошибка при создании `.venv`

**Решение:**
```bash
# Установите venv модуль
python -m pip install virtualenv

# Или используйте virtualenv
virtualenv .venv
```

### Ошибки при установке зависимостей

**Проблема:** Ошибки при установке пакетов из `requirements.txt`

**Решение:**
```bash
# Обновите pip
python -m pip install --upgrade pip

# Установите wheel
pip install wheel

# Попробуйте снова
pip install -r requirements.txt
```

### Бот не запускается

**Проблема:** Окно консоли сразу закрывается или ошибка

**Решение:**
1. Проверьте файл `.env` - токен и ID должны быть корректными
2. Проверьте логи в директории `logs/error.log`
3. Запустите вручную для просмотра ошибок:
   ```bash
   .venv\Scripts\activate
   python main.py
   ```

## Дополнительные ресурсы

- **[README.md](../../README.md)** - основная документация
- **[CHANGELOG.md](CHANGELOG.md)** - история изменений
- **[CONFIG.md](CONFIG.md)** - подробное описание конфигурации
- **[COMMANDS.md](COMMANDS.md)** - справочник команд
- **[GitHub Issues](https://github.com/Eklipti/TelegramControlBot/issues)** - сообщения об ошибках и вопросы

---

## 📄 Лицензия

Проект распространяется по лицензии **GNU GPL v3.0**. Вы можете свободно использовать и модифицировать код.

Изначальная задумка: Nlan_Cat
Автор: Eklipti

См. [LICENSE](../LICENSE) для полного текста лицензии.