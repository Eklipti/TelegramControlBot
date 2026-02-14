@echo off

chcp 65001 >nul
echo ============================================
echo TelegramControlBot - Первоначальная настройка
echo ============================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [1/6] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден!
    echo.
    echo Пожалуйста, установите Python 3.13 или выше:
    echo https://www.python.org/downloads/release/python-31312/
    echo.
    echo Убедитесь, что отметили "Add Python to PATH" при установке.
    pause
    exit /b 1
)
python --version
echo.

echo [2/6] Проверка версии Python...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Требуется Python 3.13 или выше!
    echo Текущая версия может не поддерживаться.
    echo.
)

echo [3/6] Создание виртуального окружения...
if exist ".venv" (
    echo Виртуальное окружение уже существует.
) else (
    echo Создание .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Не удалось создать виртуальное окружение!
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано успешно.
)
echo.

echo [4/6] Активация виртуального окружения...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Не удалось активировать виртуальное окружение!
    pause
    exit /b 1
)
echo [OK] Виртуальное окружение активировано.
echo.

echo [5/6] Установка зависимостей...
echo Это может занять несколько минут...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Не удалось установить зависимости!
    pause
    exit /b 1
)
echo [OK] Зависимости установлены успешно.
echo.

echo [6/6] Настройка конфигурации...
if exist ".env" (
    echo Файл .env уже существует.
) else (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] Создан файл .env из .env.example
        echo.
        echo [ВАЖНО] Отредактируйте файл .env и укажите:
        echo   - TELEGRAM_BOT_TOKEN (получите от @BotFather)
        echo   - ALLOWED_USER_IDS (получите от @Getmyid_bot)
        echo.
    ) else (
        echo [WARNING] Файл .env.example не найден!
    )
)


echo.
echo ============================================
echo   Настройка завершена успешно!
echo ============================================
echo.
pause

