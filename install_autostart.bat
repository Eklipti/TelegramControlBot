@echo off
REM SPDX-FileCopyrightText: 2025 TelegramControlBot contributors
REM SPDX-License-Identifier: AGPL-3.0-or-later

chcp 65001 >nul
echo ============================================
echo   TelegramControlBot - Установка автозапуска
echo ============================================
echo.

REM Проверка прав администратора
net session >nul 2>&1
if errorlevel 1 (
    echo [INFO] Скрипт не запущен от имени администратора.
    echo Будет использована папка автозагрузки пользователя.
    echo.
)

REM Получение пути к директории скрипта
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Проверка наличия start.bat
if not exist "start.bat" (
    echo [ERROR] Файл start.bat не найден!
    echo Убедитесь, что вы запускаете скрипт из директории проекта.
    pause
    exit /b 1
)

REM Путь к папке автозагрузки
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Создание ярлыка в автозагрузке
echo Создание ярлыка в автозагрузке...
echo.

REM Использование PowerShell для создания ярлыка
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\TelegramControlBot.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%start.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'Telegram TelegramControlBot'; $Shortcut.Save()"

if errorlevel 1 (
    echo [ERROR] Не удалось создать ярлык!
    pause
    exit /b 1
)

echo ============================================
echo   Автозапуск установлен успешно!
echo ============================================
echo.
echo Ярлык создан: %STARTUP_FOLDER%\TelegramControlBot.lnk
echo.
echo Бот будет автоматически запускаться при входе в Windows.
echo.
echo Для удаления из автозагрузки:
echo   1. Нажмите Win+R
echo   2. Введите: shell:startup
echo   3. Удалите ярлык TelegramControlBot.lnk
echo.
pause

