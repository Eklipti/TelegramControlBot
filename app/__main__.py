#!/usr/bin/env python3
"""
Точка входа для запуска ControlBot через python -m app
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Импортируем и запускаем main функцию
from app.app import main

if __name__ == "__main__":
    main()
