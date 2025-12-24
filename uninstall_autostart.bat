@echo off
REM SPDX-FileCopyrightText: 2025 TelegramControlBot contributors
REM SPDX-License-Identifier: AGPL-3.0-or-later

chcp 65001 >nul
echo ============================================
echo   TelegramControlBot - Удаление автозапуска
echo ============================================
echo.

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\TelegramControlBot.lnk"

if not exist "%SHORTCUT_PATH%" (
    echo [INFO] Ярлык в автозагрузке не найден.
    echo Бот не установлен в автозагрузку.
    echo.
    pause
    exit /b 0
)

echo Удаление ярлыка из автозагрузки...
del "%SHORTCUT_PATH%"

if errorlevel 1 (
    echo [ERROR] Не удалось удалить ярлык!
    echo Попробуйте удалить его вручную:
    echo %SHORTCUT_PATH%
    echo.
    pause
    exit /b 1
)

echo ============================================
echo   Автозапуск удален успешно!
echo ============================================
pause

