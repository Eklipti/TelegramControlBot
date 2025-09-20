# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Утилиты для безопасной работы с GUI/скриншотами в headless-окружении."""
import importlib
import os
from typing import Any, Callable, Optional


def _bool_env(name: str, *, default: Optional[bool] = None) -> Optional[bool]:
    v = os.environ.get(name, "").strip().lower()
    if v in ("1", "true", "yes"):
        return True
    if v in ("0", "false", "no"):
        return False
    return default

def _is_display_available() -> bool:
    """Проверяет доступность дисплея для GUI операций."""
    try:
        # Новая логика + обратная совместимость
        gui_enabled = _bool_env("GUI_ENABLED")
        if gui_enabled is not None:
            return gui_enabled
        # back-compat
        if _bool_env("HEADLESS_MODE") is True:  # HEADLESS_MODE=true => GUI недоступен
            return False
        old = _bool_env("GUI_MODE")
        if old is not None:
            return old

        if os.name == "nt":  # Windows
            # Быстрая проверка наличия GUI через pyautogui.size()
            try:
                import pyautogui  # type: ignore
                pyautogui.size()
                return True
            except Exception:
                return False
        # Linux/macOS
        return os.environ.get("DISPLAY") is not None
    except Exception:
        return False


def _import_gui_module(mod: str, *, require_display: bool, postcheck: Optional[Callable[[], None]] = None) -> Any:
    """Общий безопасный импорт модулей GUI-семейства."""
    if require_display and not _is_display_available():
        raise RuntimeError(f"{mod} недоступен в headless-окружении")
    try:
        m = importlib.import_module(mod)
        if postcheck:
            postcheck()
        return m
    except ImportError as e:
        raise RuntimeError(f"Не удалось импортировать {mod}: {e}") from e


def safe_import_cv2():
    """Безопасный импорт OpenCV с требованием GUI."""
    return _import_gui_module("cv2", require_display=True)

def safe_import_pyautogui():
    """Безопасный импорт PyAutoGUI с требованием GUI."""
    return _import_gui_module("pyautogui", require_display=True)

def safe_import_pil():
    """Безопасный импорт PIL.ImageGrab с требованием GUI."""
    return _import_gui_module("PIL.ImageGrab", require_display=True)


def safe_import_gui_modules() -> tuple[Any, Any, Any]:
    """Безопасно импортирует все GUI модули."""
    if not _is_display_available():
        raise RuntimeError("GUI модули недоступны в headless-окружении. Установите GUI_ENABLED=1.")
    cv2 = _import_gui_module("cv2", require_display=True)
    pyautogui = _import_gui_module("pyautogui", require_display=True)
    ImageGrab = _import_gui_module("PIL.ImageGrab", require_display=True)
    return cv2, pyautogui, ImageGrab


def lazy_import_cv2():
    """Ленивый импорт OpenCV с внятной ошибкой."""
    return _import_gui_module("cv2", require_display=True)

def lazy_import_pyautogui():
    """Ленивый импорт PyAutoGUI с внятной ошибкой."""
    return _import_gui_module("pyautogui", require_display=True)

def lazy_import_pil():
    """Ленивый импорт PIL.ImageGrab с внятной ошибкой."""
    return _import_gui_module("PIL.ImageGrab", require_display=True)


def is_headless_environment() -> bool:
    """True, если дисплей недоступен (headless)."""
    return not _is_display_available()
