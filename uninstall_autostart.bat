@echo off
REM SPDX-FileCopyrightText: 2025 ControlBot contributors
REM SPDX-License-Identifier: AGPL-3.0-or-later

chcp 65001 >nul
echo ============================================
echo   ControlBot - Удаление автозапуска
echo ============================================
echo.

REM Путь к папке автозагрузки
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\ControlBot.lnk"

REM Проверка наличия ярлыка
if not exist "%SHORTCUT_PATH%" (
    echo [ИНФОРМАЦИЯ] Ярлык в автозагрузке не найден.
    echo Бот не установлен в автозагрузку.
    echo.
    pause
    exit /b 0
)

REM Удаление ярлыка
echo Удаление ярлыка из автозагрузки...
del "%SHORTCUT_PATH%"

if errorlevel 1 (
    echo [ОШИБКА] Не удалось удалить ярлык!
    echo Попробуйте удалить его вручную:
    echo %SHORTCUT_PATH%
    echo.
    pause
    exit /b 1
)

echo ============================================
echo   Автозапуск удален успешно!
echo ============================================
echo.
echo Бот больше не будет автоматически запускаться при входе в Windows.
echo.
pause

