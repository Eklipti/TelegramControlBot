import os
import sys


def _load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f.readlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


def main() -> None:
    _load_env()
    mode = os.environ.get("SWITCH", "new").lower()
    if mode == "old":
        # run legacy telebot script
        exec(compile(open("ControlBot.py", "rb").read(), "ControlBot.py", "exec"), {
            "__name__": "__main__"
        })
    else:
        # run aiogram app
        from app.app import main as run_aiogram
        run_aiogram()


if __name__ == "__main__":
    main()



