# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os

DEFAULT_PATHS_FILE = "jsons/DEFAULT_PATHS.json"
CONFIG_FILE = "jsons/paths_config.json"

def load_default_paths():
    """Загружает предустановленные пути из jsons/DEFAULT_PATHS.json"""
    if os.path.exists(DEFAULT_PATHS_FILE):
        try:
            with open(DEFAULT_PATHS_FILE, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки jsons/DEFAULT_PATHS.json: {e}")
            return {}
    return {}

def load_paths():
    """Загружает пользовательские пути из jsons/paths_config.json"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки jsons/paths_config.json: {e}")
            return {}
    return {}

def save_paths(paths):
    """Сохраняет пользовательские пути в jsons/paths_config.json"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(paths, f, indent=4, ensure_ascii=False)

def save_default_paths(paths):
    """Сохраняет предустановленные пути в jsons/DEFAULT_PATHS.json"""
    with open(DEFAULT_PATHS_FILE, 'w', encoding='utf-8') as f:
        json.dump(paths, f, indent=4, ensure_ascii=False)

def get_all_paths():
    """Возвращает объединенные пути: пользовательские + предустановленные"""
    user_paths = load_paths()
    default_paths = load_default_paths()

    # Объединяем, приоритет у пользовательских путей
    all_paths = default_paths.copy()
    all_paths.update(user_paths)
    return all_paths

# Инициализация путей
PATHS = get_all_paths()
