@echo off

chcp 65001 >nul
echo ============================================
echo   TelegramControlBot - Установка автозапуска
echo ============================================
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Скрипт не запущен от имени администратора.
    echo Будет использована папка автозагрузки пользователя.
    echo.
)

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist "start.bat" (
    echo [ERROR] Файл start.bat не найден!
    echo Убедитесь, что вы запускаете скрипт из директории проекта.
    pause
    exit /b 1
)

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo Создание ярлыка в автозагрузке...
echo.

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
pause

