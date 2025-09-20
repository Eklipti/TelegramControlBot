# Headless-режим для GitHub Actions

## Проблема

GitHub Actions работает в headless-окружении без дисплея, что вызывает ошибки при импорте GUI модулей (`pyautogui`, `cv2`, `PIL`):

```
KeyError: 'DISPLAY'
```

## Решение

Код теперь поддерживает headless-режим через:

1. **Автоматическое определение** headless-окружения
2. **Ленивые импорты** GUI модулей
3. **Принудительный headless-режим** через переменную окружения

## Использование

### Автоматическое определение

Код автоматически определяет headless-окружение:
- **Linux/macOS**: проверяет наличие переменной `DISPLAY`
- **Windows**: проверяет доступность GUI через `pyautogui.size()`

### Принудительный headless-режим

Для принудительного включения headless-режима установите переменную окружения:

```bash
export GUI_ENABLED=0
# или
export GUI_ENABLED=false
# или
export GUI_ENABLED=no
```

**Обратная совместимость** (deprecated):
```bash
export HEADLESS_MODE=1
# или
export GUI_MODE=0
```

### В GitHub Actions

Добавьте в ваш workflow:

```yaml
env:
  GUI_ENABLED: 0
```

**Обратная совместимость** (deprecated):
```yaml
env:
  HEADLESS_MODE: 1
```

## Поведение

- **В headless-режиме**: GUI модули блокируются с понятным сообщением об ошибке
- **В обычном режиме**: GUI модули работают как обычно
- **Импорты**: все модули импортируются без ошибок в любом режиме

## Ленивые импорты (v2.2.1)

### Новые функции для ленивых импортов

```python
from app.gui_utils import (
    lazy_import_cv2,
    lazy_import_pyautogui, 
    lazy_import_pil,
    lazy_import_gui_modules
)

# Ленивый импорт OpenCV
try:
    cv2 = lazy_import_cv2()
    # Работа с OpenCV
except RuntimeError as e:
    print(f"OpenCV недоступен: {e}")

# Ленивый импорт PyAutoGUI
try:
    pyautogui = lazy_import_pyautogui()
    # Работа с PyAutoGUI
except RuntimeError as e:
    print(f"PyAutoGUI недоступен: {e}")

# Ленивый импорт PIL
try:
    ImageGrab = lazy_import_pil()
    # Работа с PIL
except RuntimeError as e:
    print(f"PIL недоступен: {e}")
```

### Улучшенные сообщения об ошибках

Ленивые импорты предоставляют подробные сообщения об ошибках:

```
OpenCV недоступен в headless-окружении. 
Для работы с изображениями требуется GUI-среда.

PyAutoGUI недоступен в headless-окружении. 
Для работы с мышью и клавиатурой требуется GUI-среда.

PIL недоступен в headless-окружении. 
Для работы с изображениями требуется GUI-среда.
```

## Примеры

### Старый способ (deprecated)
```python
from app.gui_utils import safe_import_pyautogui

try:
    pyautogui = safe_import_pyautogui()
    # Работа с pyautogui
except RuntimeError as e:
    print(f"GUI недоступен: {e}")
```

### Новый способ (рекомендуется)
```python
from app.gui_utils import lazy_import_pyautogui

try:
    pyautogui = lazy_import_pyautogui()
    # Работа с pyautogui
except RuntimeError as e:
    print(f"GUI недоступен: {e}")
```

## Файлы

- `app/gui_utils.py` - утилиты для безопасной работы с GUI
- `app/handlers/attachments.py` - обновлен для headless-режима
- `app/handlers/mouse_keyboard.py` - обновлен для headless-режима
- `app/handlers/screen.py` - обновлен для headless-режима
- `app/handlers/remote_desktop.py` - обновлен для headless-режима
