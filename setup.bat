@echo off
REM SPDX-FileCopyrightText: 2025 ControlBot contributors
REM SPDX-License-Identifier: AGPL-3.0-or-later

chcp 65001 >nul
echo ============================================
echo   ControlBot - Первоначальная настройка
echo ============================================
echo.

REM Получение пути к директории скрипта
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Проверка наличия Python
echo [1/6] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Пожалуйста, установите Python 3.11 или выше:
    echo https://www.python.org/downloads/
    echo.
    echo Убедитесь, что отметили "Add Python to PATH" при установке.
    pause
    exit /b 1
)
python --version
echo.

REM Проверка версии Python
echo [2/6] Проверка версии Python...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Требуется Python 3.11 или выше!
    echo Текущая версия может не поддерживаться.
    echo.
)

REM Создание виртуального окружения
echo [3/6] Создание виртуального окружения...
if exist ".venv" (
    echo Виртуальное окружение уже существует.
) else (
    echo Создание .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение!
        pause
        exit /b 1
    )
    echo Виртуальное окружение создано успешно.
)
echo.

REM Активация виртуального окружения
echo [4/6] Активация виртуального окружения...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ОШИБКА] Не удалось активировать виртуальное окружение!
    pause
    exit /b 1
)
echo Виртуальное окружение активировано.
echo.

REM Установка зависимостей
echo [5/6] Установка зависимостей...
echo Это может занять несколько минут...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости!
    pause
    exit /b 1
)
echo Зависимости установлены успешно.
echo.

REM Создание .env файла
echo [6/6] Настройка конфигурации...
if exist ".env" (
    echo Файл .env уже существует.
) else (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Создан файл .env из .env.example
        echo.
        echo [ВАЖНО] Отредактируйте файл .env и укажите:
        echo   - TELEGRAM_BOT_TOKEN (получите от @BotFather)
        echo   - ALLOWED_USER_IDS (получите от @userinfobot)
        echo.
    ) else (
        echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env.example не найден!
    )
)

REM Создание необходимых директорий
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "exports" mkdir exports

echo.
echo ============================================
echo   Настройка завершена успешно!
echo ============================================
echo.
echo Следующие шаги:
echo   1. Отредактируйте файл .env (укажите токен бота и ID пользователей)
echo   2. Запустите start.bat для запуска бота
echo   3. (Опционально) Запустите install_autostart.bat для добавления в автозагрузку
echo.
pause

