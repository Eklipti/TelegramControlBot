# Windows Scripts

This directory contains Windows-specific scripts for ControlBot.

## ControlBot.bat

A Windows batch file for easy startup of ControlBot.

### Usage

```cmd
ControlBot.bat
```

### What it does

- Activates the Python virtual environment (if exists)
- Installs/updates dependencies from `requirements.txt`
- Runs the main ControlBot application
- Provides error handling and user feedback

### Requirements

- Python 3.8+ installed and in PATH
- `requirements.txt` in the project root
- `main.py` in the project root

### Notes

- Run this script from the ControlBot project root directory
- The script will automatically handle virtual environment activation
- All dependencies will be installed/updated before running the bot
