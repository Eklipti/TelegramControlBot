@echo off

chcp 65001 >nul
title TelegramControlBot

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist ".venv" (
    echo [INFO] Виртуальное окружение не найдено.
    echo.
    echo Запуск setup.bat для создания окружения...
    call setup.bat
    if not exist ".venv" (
        echo [ERROR] Виртуальное окружение не было создано!
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [WARNING] Файл .env не найден!
    echo.
    echo Пожалуйста, создайте .env файл с настройками бота.
    echo Используйте .env.example как шаблон.
    echo.
    pause
    exit /b 1
)

echo ============================================
echo   Запуск TelegramControlBot...
echo ============================================
echo.

call .venv\Scripts\activate.bat

python main.py

if errorlevel 1 (
    echo.
    echo ============================================
    echo   Бот завершился с ошибкой!
    echo ============================================
    echo.
    pause
)

