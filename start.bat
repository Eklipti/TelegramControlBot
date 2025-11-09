@echo off
REM SPDX-FileCopyrightText: 2025 ControlBot contributors
REM SPDX-License-Identifier: AGPL-3.0-or-later

chcp 65001 >nul
title ControlBot

REM Получение пути к директории скрипта
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Проверка наличия виртуального окружения
if not exist ".venv" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo.
    echo Пожалуйста, сначала запустите setup.bat для настройки.
    echo.
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist ".env" (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!
    echo.
    echo Пожалуйста, создайте .env файл с настройками бота.
    echo Используйте .env.example как шаблон.
    echo.
    pause
    exit /b 1
)

REM Активация виртуального окружения и запуск бота
echo ============================================
echo   Запуск ControlBot...
echo ============================================
echo.

call .venv\Scripts\activate.bat

REM Запуск бота
python main.py

REM Если бот завершился с ошибкой
if errorlevel 1 (
    echo.
    echo ============================================
    echo   Бот завершился с ошибкой!
    echo ============================================
    echo.
    pause
)

