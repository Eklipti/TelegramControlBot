import json
import os

DEFAULT_PATHS = {
    "EvilBot_ALT": r"C:\Users\TAKERO\Downloads\EvilBot_Dev3\EvilBot_ALT.py",
    "EvilBot": r"C:\Users\TAKERO\Downloads\EvilBot_Dev3\EvilBot.py",
    "Sad_EvilBot_ALT": r"C:\Users\TAKERO\Downloads\Sad_EvilBot_Dev3\Sad_EvilBot_ALT.py",
    "Sad_EvilBot": r"C:\Users\TAKERO\Downloads\Sad_EvilBot_Dev3\Sad_EvilBot.py",
    "ST": r"C:\SillyTavern\SillyTavern-release\Start.bat",
    "DP8k": r"C:\AI Models\DP8k.kcpps",
    "Edos": r"C:\Edos\Edos.py",
    "8k": [
        r"C:\Users\TAKERO\Downloads\Sad_EvilBot_Dev3\8k.kcpps",
        r"C:\Users\TAKERO\Downloads\EvilBot_Dev3\8k.kcpps"
    ]
}

CONFIG_FILE = "paths_config.json"

def load_paths():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return DEFAULT_PATHS
    return DEFAULT_PATHS

def save_paths(paths):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(paths, f, indent=4)

# Инициализация путей
PATHS = load_paths()