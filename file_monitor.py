import os
import threading
import time

class FileMonitor:
    def __init__(self, bot, allowed_user_ids):
        self.bot = bot
        self.allowed_user_ids = allowed_user_ids
        self.monitor_paths = set()
        self.monitor_stop = threading.Event()
        self.monitor_thread = None
        self.last_state = {}
        self.running = False

    def start(self):
        if self.running:
            return

        self.last_state = {}
        self.monitor_stop.clear()
        self.running = True

        self.monitor_thread = threading.Thread(target=self.worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop(self):
        self.running = False
        self.monitor_stop.set()
        self.monitor_paths.clear()

    def add_path(self, path):
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return False
        
        self.monitor_paths.add(abs_path)
        self.start()
        return True

    def remove_path(self, path):
        abs_path = os.path.abspath(path)
        if abs_path in self.monitor_paths:
            self.monitor_paths.remove(abs_path)
            return True
        return False

    def list_paths(self):
        return list(self.monitor_paths)

    def worker(self):
        while not self.monitor_stop.is_set() and self.running:
            try:
                current_state = {}
                
                # Собираем текущее состояние только для активных путей
                for path in list(self.monitor_paths):
                    if not os.path.exists(path):
                        continue

                    if os.path.isfile(path):
                        try:
                            current_state[path] = {
                                'mtime': os.path.getmtime(path),
                                'size': os.path.getsize(path)
                            }
                        except Exception:
                            continue
                    else:
                        for root, _, files in os.walk(path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    current_state[file_path] = {
                                        'mtime': os.path.getmtime(file_path),
                                        'size': os.path.getsize(file_path)
                                    }
                                except Exception:
                                    continue

                # Первый запуск - просто сохраняем состояние
                if not self.last_state:
                    self.last_state = current_state
                    time.sleep(10)
                    continue

                # Поиск изменений
                changed = []
                created = []
                deleted = []

                # Проверяем изменения в существующих файлах
                for path, info in current_state.items():
                    if path in self.last_state:
                        old_info = self.last_state[path]
                        if info['mtime'] != old_info['mtime'] or info['size'] != old_info['size']:
                            changed.append(path)
                    else:
                        created.append(path)

                # Проверяем удаленные файлы
                for path in self.last_state:
                    if path not in current_state:
                        deleted.append(path)

                # Отправляем уведомления
                for path in created:
                    self.notify_file_change(f"➕ Создан: {path}")
                for path in changed:
                    self.notify_file_change(f"✏️ Изменен: {path}")
                for path in deleted:
                    self.notify_file_change(f"➖ Удален: {path}")

                # Обновляем последнее известное состояние
                self.last_state = current_state

                time.sleep(10)  # Проверка каждые 10 секунд

            except Exception as e:
                print(f"File monitor error: {str(e)}")
                time.sleep(30)
        
        self.running = False

    def notify_file_change(self, message):
        for user_id in self.allowed_user_ids:
            try:
                self.bot.send_message(user_id, f"📁 {message}")
            except Exception:
                pass