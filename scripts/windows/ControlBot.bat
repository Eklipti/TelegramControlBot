@echo off
REM ControlBot - Telegram bot for remote PC control
REM Loads .env and runs aiogram bot

echo Starting ControlBot...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Check if main.py exists (go up two directories from scripts/windows/)
if not exist "%~dp0..\..\main.py" (
    echo ERROR: main.py not found in project root
    echo Please run this script from the ControlBot directory
    pause
    exit /b 1
)

REM Change to project root directory
cd /d "%~dp0..\.."

REM Run the bot
python main.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Bot stopped with error code %errorlevel%
    pause
) else (
    echo.
    echo Bot stopped normally
    pause
)