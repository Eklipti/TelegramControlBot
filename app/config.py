# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from dataclasses import dataclass


def load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f.readlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


@dataclass
class Settings:
    token: str
    allowed_user_ids: list[int]

    @staticmethod
    def load() -> "Settings":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        ids_raw = os.environ.get("ALLOWED_USER_IDS", "")
        allowed: list[int] = []
        for part in ids_raw.replace(";", ",").split(","):
            part = part.strip()
            if not part:
                continue
            try:
                allowed.append(int(part))
            except ValueError:
                continue
        return Settings(token=token, allowed_user_ids=allowed)


def is_user_allowed(user_id: int, allowed_users: list[int]) -> bool:
    return user_id in allowed_users


def get_encoding() -> str:
    if os.name == "nt":
        return "cp866"
    return os.device_encoding(1) or "utf-8"



