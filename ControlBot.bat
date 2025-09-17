@echo on
REM Loads .env and dispatches to legacy (telebot) or new (aiogram)
python "%~dp0main.py"
exit