import os

# Load .env if present for SWITCH compatibility
def _load_env(path: str = ".env"):
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

_load_env()

import telebot
from telebot.types import BotCommand
import subprocess
import os
import threading
import time
import sys
import html
import locale
import io
from PIL import Image, ImageGrab
from telebot import types
import pyautogui
import numpy as np
import cv2
from telebot import apihelper
import shlex
import shutil
import tempfile
from app.help_texts import COMMAND_HELP
from app.paths_config import PATHS, load_paths, save_paths
from file_monitor import FileMonitor

# таймауты
apihelper.SESSION_TIME_TO_LIVE = 5 * 60
apihelper.READ_TIMEOUT = 50
apihelper.CONNECT_TIMEOUT = 15

# Конфигурация
TOKEN = ""
ALLOWED_USER_IDS = [] 

# Функция проверки пользователя должна быть определена ДО её использования
def is_user_allowed(user_id):
    return user_id in ALLOWED_USER_IDS

# Загрузка путей при старте
PATHS = load_paths()

bot = telebot.TeleBot(TOKEN)

# Set bot commands for legacy telebot mode
try:
    from app.help_texts import COMMAND_HELP
    commands = [
        BotCommand(cmd, (data.get('description') or '')[:256])
        for cmd, data in sorted(COMMAND_HELP.items(), key=lambda x: x[0])
    ]
    bot.set_my_commands(commands)
except Exception:
    pass
active_processes = {}
cmd_sessions = {}  # Сессии командной строки: {chat_id: session_dict}
upload_requests = {}  # Для отслеживания запросов на загрузку: {chat_id: target_path}
download_requests = {}  # Для отслеживания запросов на скачивание
mouse_positions = {}  # Словарь для сохранения позиций мыши

# Инициализация мониторинга файлов
file_monitor = FileMonitor(bot, ALLOWED_USER_IDS)

@bot.message_handler(commands=['monitor_add'])
def handle_monitor_add(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите путь для мониторинга")
        return

    path = os.path.abspath(args[1])
    if not os.path.exists(path):
        bot.reply_to(message, f"⚠️ Путь не существует: {path}")
        return

    file_monitor.add_path(path)
    bot.reply_to(message, f"👁️ Мониторинг добавлен для: {path}")

@bot.message_handler(commands=['monitor_remove'])
def handle_monitor_remove(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите путь для удаления")
        return

    path = os.path.abspath(args[1])
    if file_monitor.remove_path(path):
        bot.reply_to(message, f"⛔ Мониторинг удален для: {path}")
    else:
        bot.reply_to(message, f"ℹ️ Путь не в списке мониторинга: {path}")

@bot.message_handler(commands=['monitor_list'])
def handle_monitor_list(message):
    if not is_user_allowed(message.from_user.id):
        return

    paths = file_monitor.get_paths()
    if not paths:
        bot.reply_to(message, "ℹ️ Нет активных мониторингов")
        return

    response = "👁️ Отслеживаемые пути:\n" + "\n".join(paths)
    bot.reply_to(message, response)

@bot.message_handler(commands=['monitor_stop'])
def handle_monitor_stop(message):
    if not is_user_allowed(message.from_user.id):
        return

    file_monitor.stop()
    bot.reply_to(message, "⛔ Мониторинг полностью остановлен и очищен")

@bot.message_handler(commands=['add_path'])
def handle_add_path(message):
    """Добавить новый путь в конфиг"""
    if not is_user_allowed(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        bot.reply_to(message, "❌ Используйте: /add_path <имя> <путь>")
        return
    
    name = args[1]
    path = args[2]
    
    # Проверка существования пути
    if not os.path.exists(path):
        bot.reply_to(message, f"⚠️ Путь не существует: {path}")
        return
    
    # Обновляем конфиг
    PATHS[name] = os.path.abspath(path)
    save_paths(PATHS)
    
    bot.reply_to(message, f"✅ Путь сохранен:\n{name} → {PATHS[name]}")

@bot.message_handler(commands=['list_paths'])
def handle_list_paths(message):
    """Показать все зарегистрированные пути"""
    if not is_user_allowed(message.from_user.id):
        return
    
    if not PATHS:
        bot.reply_to(message, "ℹ️ Нет зарегистрированных путей")
        return
    
    response = "📁 Зарегистрированные пути:\n\n"
    for name, path in PATHS.items():
        response += f"• <b>{name}</b>: {path}\n"
    
    bot.reply_to(message, response, parse_mode='HTML')

@bot.message_handler(commands=['del_path'])
def handle_del_path(message):
    """Удалить путь из конфига"""
    if not is_user_allowed(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите имя пути для удаления")
        return
    
    name = args[1]
    if name in PATHS:
        del PATHS[name]
        save_paths(PATHS)
        bot.reply_to(message, f"✅ Путь удален: {name}")
    else:
        bot.reply_to(message, f"⚠️ Путь не найден: {name}")

def is_user_allowed(user_id):
    return user_id in ALLOWED_USER_IDS

@bot.message_handler(commands=['rdp_start'])
def handle_rdp_start(message):
    if not is_user_allowed(message.from_user.id):
        return

    chat_id = message.chat.id
    args = message.text.split()
    fps = 1  # По умолчанию 1 FPS

    if len(args) > 1:
        try:
            fps = min(max(int(args[1]), 1, 10))  # Ограничим 1-10 FPS
        except:
            pass

    # Если сессия уже запущена
    if chat_id in RDP_SESSIONS:
        bot.reply_to(message, f"ℹ️ Сессия уже запущена ({RDP_SESSIONS[chat_id]['fps']} FPS). Используйте /rdp_stop")
        return

    stop_event = threading.Event()
    thread = threading.Thread(target=rdp_stream, args=(chat_id, stop_event, fps))
    thread.daemon = True
    thread.start()

    RDP_SESSIONS[chat_id] = {
        'thread': thread,
        'stop_event': stop_event,
        'fps': fps
    }

    bot.reply_to(message, f"🖥️ Удаленный рабочий стол запущен ({fps} FPS)")

@bot.message_handler(commands=['rdp_stop'])
def handle_rdp_stop(message):
    if not is_user_allowed(message.from_user.id):
        return

    chat_id = message.chat.id
    if chat_id in RDP_SESSIONS:
        RDP_SESSIONS[chat_id]['stop_event'].set()
        session_info = RDP_SESSIONS[chat_id]
        del RDP_SESSIONS[chat_id]
        bot.reply_to(message, "⛔ Сессия остановлена")
    else:
        bot.reply_to(message, "ℹ️ Нет активной сессии")

def rdp_stream(chat_id, stop_event, fps):
    interval = 1.0 / fps
    message_id = None  # Сохраняем ID сообщения для редактирования

    while not stop_event.is_set():
        try:
            start_time = time.time()

            # Делаем скриншот
            screenshot = pyautogui.screenshot()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr.seek(0)

            caption = f"🖥️ {time.strftime('%H:%M:%S')} | {fps} FPS"

            if message_id is None:
                # Первое сообщение - отправляем новое
                msg = bot.send_photo(
                    chat_id,
                    img_byte_arr,
                    caption=caption,
                    disable_notification=True
                )
                message_id = msg.message_id
            else:
                # Редактируем существующее сообщение
                try:
                    media = telebot.types.InputMediaPhoto(
                        media=img_byte_arr,
                        caption=caption
                    )
                    bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=message_id,
                        media=media
                    )
                except telebot.apihelper.ApiTelegramException as e:
                    if "message to edit not found" in str(e):
                        # Если сообщение было удалено - создаем новое
                        message_id = None
                        continue
                    raise

            # Выдерживаем интервал
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)

        except Exception as e:
            print(f"RDP error: {str(e)}")
            time.sleep(1)

    # Финальное обновление после остановки
    if message_id:
        try:
            screenshot = pyautogui.screenshot()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr.seek(0)

            media = telebot.types.InputMediaPhoto(
                media=img_byte_arr,
                caption=f"⛔ СТРИМИНГ ОСТАНОВЛЕН | {time.strftime('%H:%M:%S')}"
            )
            bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=media
            )
        except Exception:
            pass

@bot.message_handler(commands=['help'])
def handle_help(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)

    # Если запрошена помощь по конкретной команде
    if len(args) > 1:
        cmd = args[1].lstrip('/').lower()

        # Находим наиболее подходящую команду
        matched_cmd = None
        for command in COMMAND_HELP:
            if command.startswith(cmd):
                matched_cmd = command
                break

        if matched_cmd and matched_cmd in COMMAND_HELP:
            help_data = COMMAND_HELP[matched_cmd]
            response = (
                f"🔹 <b>Команда: /{matched_cmd}</b>\n\n"
                f"ℹ️ {help_data['detailed']}"
            )
            bot.reply_to(message, response, parse_mode='HTML')
        else:
            bot.reply_to(
                message,
                f"❌ Команда '{cmd}' не найдена. Используйте /help для списка команд"
            )
        return

    # Общая справка по всем командам
    response = "📚 <b>Доступные команды:</b>\n\n"

    # Группируем команды по категориям
    categories = {
        "Процессы": ["on", "off", "reload", "processes"],
        "Система": ["tasklist"],
        "Файлы": ["upload", "download", "cut", "find"],
        "Мониторинг": ["monitor_add", "monitor_remove", "monitor_list", "monitor_stop"],
        "Удаленное управление": ["cmd", "newcmd", "end_session", "rdp_start", "rdp_stop"],
        "Мышь": ["mouse_move", "mouse_move_rel", "mouse_save", "mouse_goto",
                "mouse_speed", "mouse_click", "mouse_scroll", "screen_mark"],
        "Клавиатура": ["key", "type"],
        "Экран": ["screen"],
        "Прочее": ["help", "cancel"]
    }

    # Формируем ответ с категориями
    for category, commands in categories.items():
        response += f"<b>🔹 {category}:</b>\n"
        for cmd in commands:
            if cmd in COMMAND_HELP:
                response += f"• /{cmd} - {COMMAND_HELP[cmd]['description']}\n"
        response += "\n"

    response += (
        "\nℹ️ Для детальной справки по команде используйте:\n"
        "<code>/help &lt;команда&gt;</code>\n\n"
        "Пример: <code>/help on</code>"
    )

    bot.reply_to(message, response, parse_mode='HTML')

@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    if not is_user_allowed(message.from_user.id):
        return

    chat_id = message.chat.id
    if chat_id in upload_requests:
        del upload_requests[chat_id]
    if chat_id in download_requests:
        del download_requests[chat_id]
    bot.reply_to(message, "❌ Операция отменена")

@bot.message_handler(commands=['upload'])
def handle_upload_command(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите путь для сохранения после /upload")
        return

    target_path = args[1]
    upload_requests[message.chat.id] = target_path
    bot.reply_to(message, f"📤 Отправьте файл для сохранения по пути:\n{target_path}\n\nИспользуйте /cancel для отмены.")

@bot.message_handler(commands=['find'])
def handle_find(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите параметры поиска после /find")
        return

    search_params = args[1]
    msg = bot.reply_to(message, "🔍 Поиск файлов...")

    # Запускаем в отдельном потоке
    threading.Thread(
        target=find_files,
        args=(message.chat.id, msg.message_id, search_params)
    ).start()

def find_files(chat_id, msg_id, search_params):
    try:
        # Парсим параметры поиска
        name_filter = None
        size_filter = None
        ext_filter = None

        params = search_params.split()
        for param in params:
            if param.startswith("name:"):
                name_filter = param[5:]
            elif param.startswith("size:"):
                size_filter = param[5:]
            elif param.startswith("ext:"):
                ext_filter = param[4:].split(',')

        # Формируем команду find
        cmd = ["find", "/"]
        if name_filter:
            cmd += ["-name", name_filter]
        if size_filter:
            cmd += ["-size", size_filter]

        # Выполняем поиск
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding=get_encoding()
        )

        # Фильтруем по расширению
        files = result.stdout.split('\n')
        if ext_filter:
            files = [f for f in files if any(f.lower().endswith(e.lower()) for e in ext_filter)]

        # Формируем результат
        response = f"🔍 Найдено файлов: {len(files)}\n"
        response += "\n".join(files[:50])  # Первые 50 результатов

        if len(files) > 50:
            response += f"\n...и еще {len(files) - 50} файлов"

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=response
        )

        # Отправляем полный список файлом
        if files:
            file_content = "\n".join(files)
            file_io = io.BytesIO(file_content.encode('utf-8'))
            file_io.name = 'search_results.txt'
            bot.send_document(chat_id, file_io)

    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"⚠️ Ошибка поиска: {str(e)}"
        )

@bot.message_handler(commands=['download'])
def handle_download_command(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите путь к файлу/папке после /download")
        return

    path = args[1]

    try:
        # Проверяем существование
        if not os.path.exists(path):
            bot.reply_to(message, f"⚠️ Путь не существует: {path}")
            return

        # Если это файл
        if os.path.isfile(path):
            with open(path, 'rb') as file:
                bot.send_document(
                    chat_id=message.chat.id,
                    document=file,
                    caption=f"📥 Файл: {path}"
                )

        # Если это папка
        elif os.path.isdir(path):
            msg = bot.reply_to(message, "📦 Архивация папки...")

            # Создаем временный zip-архив
            zip_path = shutil.make_archive(
                base_name=os.path.join(tempfile.gettempdir(), f"folder_{time.time()}"),
                format='zip',
                root_dir=path
            )

            # Отправляем архив
            with open(zip_path, 'rb') as zip_file:
                bot.send_document(
                    chat_id=message.chat.id,
                    document=zip_file,
                    caption=f"📁 Папка: {path}"
                )

            # Удаляем временный файл
            os.remove(zip_path)
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['cut'])
def handle_cut_command(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Укажите путь к файлу после /cut")
        return

    file_path = args[1]

    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            bot.reply_to(message, f"⚠️ Файл не существует: {file_path}")
            return

        # Проверяем, является ли путь файлом
        if not os.path.isfile(file_path):
            bot.reply_to(message, f"⚠️ Указанный путь не является файлом: {file_path}")
            return

        # Отправляем файл
        with open(file_path, 'rb') as file:
            bot.send_document(
                chat_id=message.chat.id,
                document=file,
                caption=f"✂️ Файл отправлен и УДАЛЁН: {file_path}"
            )

        # Удаляем файл после успешной отправки
        os.remove(file_path)
        bot.reply_to(message, f"✅ Файл успешно удалён: {file_path}")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка при отправке или удалении файла: {str(e)}")

@bot.message_handler(content_types=['document', 'photo'])
def handle_file(message):
    if not is_user_allowed(message.from_user.id):
        return

    chat_id = message.chat.id

    if chat_id in upload_requests:
        target_path = upload_requests[chat_id]
        del upload_requests[chat_id]

        try:
            # Определяем имя файла и тип контента
            if message.content_type == 'document':
                file_info = bot.get_file(message.document.file_id)
                original_name = message.document.file_name
            else:  # photo
                file_info = bot.get_file(message.photo[-1].file_id)
                original_name = "uploaded_photo.jpg"

            # Исправление 1: Проверяем, является ли target_path директорией
            if os.path.isdir(target_path):
                # Если это директория - добавляем оригинальное имя файла
                final_path = os.path.join(target_path, original_name)
            else:
                final_path = target_path

            # Исправление 2: Создаем директории для конечного пути
            dir_path = os.path.dirname(final_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            # Скачиваем и сохраняем файл
            downloaded_file = bot.download_file(file_info.file_path)
            with open(final_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            bot.reply_to(message, f"✅ Файл сохранен как:\n{final_path}")

        except Exception as e:
            bot.reply_to(message, f"⚠️ Ошибка при загрузке файла: {str(e)}")
        return

    # Обработка скачивания файла (download)
    if chat_id in download_requests:
        file_path = download_requests[chat_id]
        del download_requests[chat_id]  # Удаляем запрос

        try:
            if not os.path.exists(file_path):
                bot.reply_to(message, f"⚠️ Файл не существует: {file_path}")
                return

            with open(file_path, 'rb') as file:
                bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    caption=f"📥 Файл: {file_path}"
                )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Ошибка при отправке файла: {str(e)}")
        return

    # Обработка фото как шаблона поиска
    if message.content_type == 'photo':
        try:
            # Скачиваем фото
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # Сохраняем шаблон для поиска
            with open("search_template.png", 'wb') as new_file:
                new_file.write(downloaded_file)

            # Ищем на экране
            screenshot = pyautogui.screenshot()
            screenshot.save("current_screen.png")

            img_rgb = cv2.imread("current_screen.png")
            template = cv2.imread("search_template.png")

            result = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > 0.8:  # Порог совпадения
                x, y = max_loc
                w, h = template.shape[1], template.shape[0]

                # Сохраняем позицию
                mouse_positions["found"] = (x + w//2, y + h//2)
                bot.reply_to(message, f"🔍 Объект найден! Координаты: ({x + w//2}, {y + h//2})")
            else:
                bot.reply_to(message, "❌ Объект не найден на экране")

        except Exception as e:
            bot.reply_to(message, f"⚠️ Ошибка поиска: {str(e)}")

@bot.message_handler(commands=['mouse_move_rel'])
def handle_mouse_move_rel(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        _, dx, dy = message.text.split()
        pyautogui.moveRel(int(dx), int(dy))
        bot.reply_to(message, f"🖱 Мышь перемещена на ({dx}, {dy})")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nИспользуйте: /mouse_move_rel dx dy")

@bot.message_handler(commands=['screen_mark'])
def handle_screen_mark(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        # Делаем скриншот
        screenshot = pyautogui.screenshot()
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Получаем размеры экрана
        width, height = screenshot.size

        # Добавляем сетку (каждые 100 пикселей)
        for x in range(0, width, 100):
            cv2.line(img, (x, 0), (x, height), (0, 0, 255), 1)
            cv2.putText(img, str(x), (x+5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)

        for y in range(0, height, 100):
            cv2.line(img, (0, y), (width, y), (0, 0, 255), 1)
            cv2.putText(img, str(y), (5, y+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)

        # Добавляем текущую позицию мыши
        mx, my = pyautogui.position()
        cv2.circle(img, (mx, my), 10, (0, 255, 0), 2)
        cv2.putText(img, f"Mouse: ({mx},{my})", (mx+15, my-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        # Сохраняем в буфер
        _, buffer = cv2.imencode('.png', img)
        img_byte_arr = io.BytesIO(buffer)
        img_byte_arr.name = 'screen_marked.png'

        bot.send_photo(
            message.chat.id,
            img_byte_arr,
            caption=f"📐 Экран с разметкой\nТекущая позиция: ({mx}, {my})"
        )

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['mouse_save'])
def handle_mouse_save(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        name = message.text.split()[1]
        x, y = pyautogui.position()
        mouse_positions[name] = (x, y)
        bot.reply_to(message, f"📍 Позиция сохранена как '{name}' ({x}, {y})")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nИспользуйте: /mouse_save имя_позиции")

@bot.message_handler(commands=['mouse_goto'])
def handle_mouse_goto(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        name = message.text.split()[1]
        x, y = mouse_positions[name]
        pyautogui.moveTo(x, y)
        bot.reply_to(message, f"🖱 Мышь перемещена в позицию '{name}' ({x}, {y})")
    except Exception as e:
        available = "\n".join([f"- {k}" for k in mouse_positions.keys()])
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nДоступные позиции:\n{available}")

@bot.message_handler(commands=['mouse_speed'])
def handle_mouse_speed(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        speed = float(message.text.split()[1])
        pyautogui.MINIMUM_DURATION = speed
        pyautogui.MINIMUM_SLEEP = speed
        bot.reply_to(message, f"⚡ Скорость мыши установлена: {speed} сек")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nИспользуйте: /mouse_speed 0.1 (быстро) или 1.0 (медленно)")

@bot.message_handler(commands=['mouse_move'])
def handle_mouse_move(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        _, x, y = message.text.split()
        pyautogui.moveTo(int(x), int(y))
        bot.reply_to(message, f"🖱 Мышь перемещена в ({x}, {y})")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nИспользуйте: /mouse_move x y")

@bot.message_handler(commands=['mouse_click'])
def handle_mouse_click(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        button = 'left'
        if len(message.text.split()) > 1:
            button = message.text.split()[1]

        pyautogui.click(button=button)
        bot.reply_to(message, f"🖱 Клик {button} кнопкой")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nДоступные кнопки: left, right, middle")

@bot.message_handler(commands=['mouse_scroll'])
def handle_mouse_scroll(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        _, steps = message.text.split()
        pyautogui.scroll(int(steps))
        bot.reply_to(message, f"🖱 Скролл на {steps} шагов")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nИспользуйте: /mouse_scroll steps")

@bot.message_handler(commands=['key'])
def handle_key_press(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        # Получаем все аргументы после команды
        args = message.text.split()[1:]
        if not args:
            bot.reply_to(message, "⚠️ Укажите клавиши для нажатия")
            return

        # Объединяем все аргументы в одну строку и разбиваем по +
        keys_str = ' '.join(args)
        keys = keys_str.split('+')
        
        # Удаляем пустые строки и лишние пробелы
        keys = [k.strip() for k in keys if k.strip()]
        
        if not keys:
            bot.reply_to(message, "⚠️ Не указаны клавиши")
            return

        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
            
        bot.reply_to(message, f"⌨ Нажаты клавиши: {'+'.join(keys)}")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nПример: /key enter или /key ctrl+alt+delete")

@bot.message_handler(commands=['type'])
def handle_type_text(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        text = message.text.split(' ', 1)[1]
        pyautogui.typewrite(text)
        bot.reply_to(message, f"⌨ Введен текст: {text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}\nИспользуйте: /type ваш_текст")

@bot.message_handler(func=lambda message: not is_user_allowed(message.from_user.id))
def handle_unauthorized(message):
    pass  # Игнорируем

def get_encoding():
    """Определяем правильную кодировку для Windows"""
    if os.name == 'nt':
        return 'cp866'  # Кодировка консоли Windows для русского
    return locale.getpreferredencoding()

def session_output_reader(chat_id, message_id, proc):
    encoding = get_encoding()
    full_output = ""
    start_time = time.time()
    last_update = start_time
    line_count = 0

    while True:
        char = proc.stdout.read(1)
        if not char:
            if proc.poll() is not None:
                break
            continue

        full_output += char
        current_time = time.time()

        if char == '\n' or current_time - last_update > 0.2:
            line_count += 1
            elapsed = int(current_time - start_time)
            status_bar = f"⏱️ {elapsed}s | 📜 {line_count} lines"
            display_output = html.escape(full_output[-1000:])

            message_content = (
                f"<code>{status_bar}\n"
                f"{'-'*20}\n"
                f"{display_output}</code>"
            )

            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_content,
                    parse_mode='HTML'
                )
            except Exception:
                pass

            last_update = current_time

    exit_code = proc.poll()
    elapsed = int(time.time() - start_time)
    status = "✅ Успешно" if exit_code == 0 else f"❌ Ошибка (код: {exit_code})"
    result_message = (
        f"<code>{status} | ⏱️ {elapsed}s | 📜 {line_count} lines\n"
        f"{'-'*20}\n"
        f"{html.escape(full_output[-3000:])}</code>"
    )

    if len(full_output) > 3000:
        result_message += "\n\n📄 Полный вывод отправлен файлом"
        file_io = io.BytesIO(full_output.encode(encoding))
        file_io.name = 'session_output.txt'
        bot.send_document(chat_id, file_io)

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=result_message,
            parse_mode='HTML'
        )
    except Exception:
        bot.send_message(chat_id, result_message, parse_mode='HTML')

    if chat_id in cmd_sessions and cmd_sessions[chat_id]['process'] == proc:
        del cmd_sessions[chat_id]

@bot.message_handler(commands=['cmd'])
def handle_cmd(message):
    if not is_user_allowed(message.from_user.id):
        return

    chat_id = message.chat.id
    command_text = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None

    # Если сессия уже активна
    if chat_id in cmd_sessions and cmd_sessions[chat_id]['active']:
        if command_text:
            try:
                cmd_sessions[chat_id]['process'].stdin.write(command_text + '\n')
                cmd_sessions[chat_id]['process'].stdin.flush()
                bot.reply_to(message, f"⌨ Команда отправлена: {command_text}")
            except Exception as e:
                bot.reply_to(message, f"⚠️ Ошибка отправки команды: {str(e)}")
        else:
            bot.reply_to(message, "ℹ️ Сессия активна. Отправьте команду текстом или используйте /newcmd")
        return

    # Создание новой сессии
    shell_cmd = ['cmd.exe'] if os.name == 'nt' else ['/bin/bash']
    try:
        proc = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            encoding=get_encoding(),
            errors='replace'
        )
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка запуска оболочки: {str(e)}")
        return

    msg = bot.reply_to(message, "⌛ Запуск командной сессии...")
    session = {
        'process': proc,
        'last_message_id': msg.message_id,
        'active': True
    }
    cmd_sessions[chat_id] = session

    thread = threading.Thread(
        target=session_output_reader,
        args=(chat_id, msg.message_id, proc)
    )
    thread.daemon = True
    thread.start()
    session['thread'] = thread

    if command_text:
        try:
            proc.stdin.write(command_text + '\n')
            proc.stdin.flush()
        except Exception as e:
            bot.reply_to(message, f"⚠️ Ошибка отправки команды: {str(e)}")

@bot.message_handler(commands=['newcmd'])
def handle_newcmd(message):
    if not is_user_allowed(message.from_user.id):
        return

    chat_id = message.chat.id
    # Завершение текущей сессии
    if chat_id in cmd_sessions:
        session = cmd_sessions[chat_id]
        if session['active']:
            try:
                session['process'].terminate()
                session['process'].wait(timeout=2)
            except Exception:
                try:
                    session['process'].kill()
                except Exception:
                    pass
            session['active'] = False

    # Запуск новой сессии
    handle_cmd(message)

@bot.message_handler(commands=['end_session'])
def handle_end_session(message):
    if not is_user_allowed(message.from_user.id):
        return

    chat_id = message.chat.id
    if chat_id in cmd_sessions:
        session = cmd_sessions[chat_id]
        if session['active']:
            try:
                session['process'].terminate()
                session['process'].wait(timeout=2)
            except Exception:
                try:
                    session['process'].kill()
                except Exception:
                    pass
            session['active'] = False
            bot.reply_to(message, "⛔ Сессия завершена")
        else:
            bot.reply_to(message, "ℹ️ Нет активной сессии")
    else:
        bot.reply_to(message, "ℹ️ Нет активной сессии")

@bot.message_handler(func=lambda message:
    not message.text.startswith('/') and
    message.chat.id in cmd_sessions and
    cmd_sessions[message.chat.id]['active'] and
    message.content_type == 'text'
)
def handle_session_text(message):
    chat_id = message.chat.id
    session = cmd_sessions[chat_id]
    try:
        session['process'].stdin.write(message.text + '\n')
        session['process'].stdin.flush()
        bot.reply_to(message, f"⌨ Команда отправлена: {message.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка отправки команды: {str(e)}")


def execute_command(command, chat_id, message_id):
    encoding = get_encoding()
    full_output = ""
    start_time = time.time()
    last_update = start_time
    line_buffer = ""
    line_count = 0

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            encoding=encoding,
            errors='replace'
        )

        # Формируем статус-бар
        status_bar = "🟢 Выполняется..."
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"<code>{status_bar}\n{'-'*20}</code>",
            parse_mode='HTML'
        )

        while True:
            char = process.stdout.read(1)
            if not char and process.poll() is not None:
                break

            if char:
                full_output += char
                line_buffer += char

                # Обновляем при новой строке или каждые 0.2 сек
                current_time = time.time()
                if char == '\n' or current_time - last_update > 0.2:
                    line_count += 1
                    elapsed = int(current_time - start_time)

                    # Форматируем вывод
                    status_bar = f"⏱️ {elapsed}s | 📜 {line_count} lines"
                    formatted_output = html.escape(line_buffer[-1000:])

                    # Собираем сообщение
                    message_content = (
                        f"<code>{status_bar}\n"
                        f"{'-'*20}\n"
                        f"{formatted_output}</code>"
                    )

                    # Обновляем сообщение
                    try:
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=message_content,
                            parse_mode='HTML'
                        )
                    except Exception:
                        pass

                    line_buffer = ""
                    last_update = current_time

    except Exception as e:
        error_msg = f"⚠️ Ошибка: {str(e)}"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"<code>{html.escape(error_msg)}</code>",
            parse_mode='HTML'
        )
    finally:
        # Финализируем вывод
        exit_code = process.poll()
        elapsed = int(time.time() - start_time)
        status = "✅ Успешно" if exit_code == 0 else f"❌ Ошибка (код: {exit_code})"

        result_message = (
            f"<code>{status} | ⏱️ {elapsed}s | 📜 {line_count} lines\n"
            f"{'-'*20}\n"
            f"{html.escape(full_output[-3000:])}</code>"
        )

        # Отправляем полный вывод файлом если нужно
        if len(full_output) > 3000:
            result_message += "\n\n📄 Полный вывод отправлен файлом"
            file_io = io.BytesIO(full_output.encode(encoding))
            file_io.name = 'command_output.txt'
            bot.send_document(chat_id, file_io)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=result_message,
            parse_mode='HTML'
        )

        del cmd_tasks[(chat_id, message_id)]

def update_command_output(chat_id, message_id, new_output):
    if (chat_id, message_id) not in cmd_tasks:
        return

    task = cmd_tasks[(chat_id, message_id)]
    task["output"] += new_output

    display_output = task["output"]
    if len(display_output) > 4000:
        display_output = "[...]\n" + display_output[-4000:]

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"<code>{html.escape(display_output)}</code>",
            parse_mode='HTML'
        )
    except Exception:
        pass

@bot.message_handler(commands=['on'])
def handle_on(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        examples = (
            "Примеры использования:\n"
            "/on EvilBot\n"
            "/on \"C:/my bot.py\" --debug\n"
            "/on notepad.exe C:/file.txt\n"
            "/on hidden:EvilBot_ALT\n"
            "/on admin:cmd.exe\n"
            "/on explorer.exe C:/Windows"
        )
        bot.reply_to(message, f"❌ Укажите имя бота или путь к файлу\n\n{examples}")
        return

    input_arg = args[1].strip()
    hidden_mode = False
    admin_mode = False
    arguments = []

    if input_arg.startswith("hidden:"):
        hidden_mode = True
        input_arg = input_arg[7:]
    elif input_arg.startswith("admin:"):
        admin_mode = True
        input_arg = input_arg[6:]

    if ' ' in input_arg:
        parts = input_arg.split(' ', 1)
        input_arg = parts[0]
        arguments = shlex.split(parts[1]) if ' ' in parts[1] else [parts[1]]

    file_path = None
    custom_path = False
    process_key = None
    new_path_found = False

    if input_arg in PATHS:
        if input_arg == "8k":
            for path in PATHS["8k"]:
                if os.path.exists(path):
                    file_path = path
                    break
        else:
            file_path = PATHS.get(input_arg)
        process_key = input_arg
    else:
        if not os.path.isabs(input_arg):
            input_arg = os.path.abspath(input_arg)

        if os.path.exists(input_arg):
            file_path = input_arg
            custom_path = True
            process_key = os.path.abspath(file_path)
            new_path_found = True
        else:
            found = False
            for path_dir in os.environ["PATH"].split(os.pathsep):
                candidate = os.path.join(path_dir.strip('"'), input_arg)
                if os.path.exists(candidate):
                    file_path = candidate
                    custom_path = True
                    process_key = os.path.abspath(file_path)
                    found = True
                    new_path_found = True
                    break

            if not found:
                bot.reply_to(message, f"❌ Файл не найден: {input_arg}")
                return

    if process_key in active_processes:
        proc = active_processes[process_key]
        if proc.poll() is None:
            bot.reply_to(message, f"ℹ️ Процесс уже запущен: {process_key}")
            return
        del active_processes[process_key]

    working_dir = os.path.dirname(file_path)
    cmd = []
    creationflags = 0

    try:
        if os.name == 'nt':
            if hidden_mode:
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = subprocess.CREATE_NEW_CONSOLE

            if admin_mode:
                if file_path.lower().endswith('.py'):
                    cmd = ["runas", "/user:Administrator", sys.executable, file_path]
                else:
                    cmd = ["runas", "/user:Administrator", file_path]
                cmd.extend(arguments)
            else:
                if file_path.lower().endswith('.py'):
                    cmd = [sys.executable, file_path]
                    cmd.extend(arguments)
                else:
                    cmd = [file_path]
                    cmd.extend(arguments)
        else:
            if file_path.lower().endswith('.py'):
                cmd = [sys.executable, file_path]
            else:
                cmd = [file_path]
            cmd.extend(arguments)

            if admin_mode:
                cmd = ["sudo"] + cmd

        proc = subprocess.Popen(
            cmd,
            cwd=working_dir,
            creationflags=creationflags
        )

        active_processes[process_key] = proc
        reply_msg = f"✅ Успешно запущен: {os.path.basename(file_path)}"

        if custom_path:
            reply_msg += f"\n📁 Путь: {file_path}"
        if arguments:
            reply_msg += f"\n⚙️ Аргументы: {' '.join(arguments)}"
        if hidden_mode:
            reply_msg += "\n👻 Режим: скрытый"
        if admin_mode:
            reply_msg += "\n🛡️ Режим: администратор"

        # Предложить сохранить новый путь
        if new_path_found and input_arg not in PATHS:
            markup = types.InlineKeyboardMarkup()
            btn_save = types.InlineKeyboardButton(
                "💾 Сохранить путь", 
                callback_data=f"save_path:{input_arg}:{file_path}"
            )
            markup.add(btn_save)
            bot.reply_to(message, reply_msg, reply_markup=markup)
        else:
            bot.reply_to(message, reply_msg)

    except Exception as e:
        error_msg = f"⚠️ Ошибка запуска: {str(e)}"
        if os.name == 'nt':
            if "не является приложением Win32" in str(e):
                try:
                    os.startfile(file_path)
                    bot.reply_to(message, f"✅ Запущено через ассоциированную программу: {file_path}")
                    return
                except Exception as startfile_error:
                    error_msg += f"\nℹ️ Ошибка при запуске через ассоциацию: {startfile_error}"
            elif admin_mode and "The operation was canceled by the user" in str(e):
                error_msg += "\nℹ️ Пользователь отменил запрос UAC"

        bot.reply_to(message, error_msg)

@bot.message_handler(commands=['processes'])
def handle_processes(message):
    if not is_user_allowed(message.from_user.id):
        return

    if not active_processes:
        bot.reply_to(message, "ℹ️ Нет активных процессов")
        return

    response = "🖥️ Активные процессы:\n\n"
    for name, proc in active_processes.items():
        status = "🟢 Активен" if proc.poll() is None else "⚪ Завершен"
        pid_line = f"PID: {proc.pid}" if proc.pid else "PID: N/A"

        response += (
            f"🔹 <b>{os.path.basename(name)}</b>\n"
            f"• Статус: {status}\n"
            f"• {pid_line}\n"
            f"• Путь: {name}\n\n"
        )

    bot.reply_to(message, response, parse_mode='HTML')

@bot.message_handler(commands=['off'])
def handle_off(message):
    if not is_user_allowed(message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2:
        # Показать список активных процессов
        active_list = []
        for name, proc in active_processes.items():
            status = "🟢 Активен" if proc.poll() is None else "⚪ Завершен"
            active_list.append(f"- {name} ({status})")

        response = "📋 Активные процессы:\n" + "\n".join(active_list) if active_list else "ℹ️ Нет активных процессов"
        response += "\n\nℹ️ Используйте /off <имя> или /off all"
        bot.reply_to(message, response)
        return

    target = args[1].strip()

    # Остановка всех процессов
    if target.lower() == "all":
        stopped = []
        failed = []

        for name, proc in list(active_processes.items()):
            if proc.poll() is None:
                try:
                    # Завершаем весь процесс и его потомки
                    subprocess.call(f'taskkill /F /T /PID {proc.pid}', shell=True)
                    stopped.append(name)
                except Exception as e:
                    failed.append(f"{name}: {str(e)}")
                finally:
                    del active_processes[name]

        response = "⛔ Остановлены:\n" + "\n".join(stopped) if stopped else "ℹ️ Нет процессов для остановки"
        if failed:
            response += "\n\n❌ Ошибки:\n" + "\n".join(failed)

        bot.reply_to(message, response)
        return

    # Поиск процесса по имени или PID
    matched_proc = None
    matched_name = None

    # Попытка найти по PID
    if target.isdigit():
        pid = int(target)
        for name, proc in active_processes.items():
            if proc.pid == pid:
                matched_proc = proc
                matched_name = name
                break

    # Поиск по имени (без учета регистра)
    if not matched_proc:
        target_lower = target.lower()
        for name, proc in active_processes.items():
            if name.lower() == target_lower:
                matched_proc = proc
                matched_name = name
                break

    if not matched_proc:
        bot.reply_to(message, f"❌ Процесс '{target}' не найден")
        return

    if matched_proc.poll() is not None:
        del active_processes[matched_name]
        bot.reply_to(message, f"ℹ️ Процесс '{matched_name}' уже завершен")
        return

    try:
        # Принудительное завершение с дочерними процессами
        subprocess.call(f'taskkill /F /T /PID {matched_proc.pid}', shell=True)

        # Двойная проверка завершения
        time.sleep(1)
        if matched_proc.poll() is None:
            matched_proc.kill()

        del active_processes[matched_name]
        bot.reply_to(message, f"⛔ Процесс '{matched_name}' (PID: {matched_proc.pid}) остановлен")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка остановки: {str(e)}")

@bot.message_handler(commands=['reload'])
def handle_reload(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        bot.reply_to(message, "🔄 Система перезагружается...")
        if os.name == 'nt':
            os.system("shutdown /r /t 0")
        else:
            os.system("sudo reboot")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка перезагрузки: {str(e)}")

@bot.message_handler(commands=['screen'])
def handle_screen(message):
    if not is_user_allowed(message.from_user.id):
        return

    # Игнорируем аргументы, если есть
    if len(message.text.split()) > 1:
        bot.reply_to(message, "⚠️ Выбор конкретного окна не поддерживается. Делаю скриншот всего экрана.")

    try:
        screenshot = pyautogui.screenshot()
    except Exception as e_main:
        try:
            screenshot = ImageGrab.grab()
        except Exception as e_fallback:
            error_msg = (
                f"⚠️ Ошибка создания скриншота:\n"
                f"• PyAutoGUI: {str(e_main)}\n"
                f"• ImageGrab: {str(e_fallback)}"
            )
            bot.reply_to(message, error_msg)
            return

    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    bot.send_photo(message.chat.id, img_byte_arr, caption="Весь экран")

@bot.message_handler(commands=['tasklist'])
def handle_tasklist(message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        # Получаем имя текущего пользователя
        username = os.getenv('USERNAME')

        # Получаем список только пользовательских процессов
        command = f'tasklist /FI "USERNAME eq {username}" /FO TABLE /NH'
        output = subprocess.check_output(
            command,
            shell=True,
            text=True,
            encoding=get_encoding()
        )

        # Парсим и форматируем вывод
        summary = {}
        detailed_lines = []

        for line in output.split('\n'):
            if not line.strip():
                continue

            # Разбиваем строку на компоненты
            parts = line.split()
            if len(parts) < 5:
                continue

            # Извлекаем имя процесса (может содержать пробелы)
            process_name = ' '.join(parts[:-4])
            pid = parts[-4]
            session = parts[-3]
            num = parts[-2]
            mem = parts[-1]

            # Группируем по имени процесса
            if process_name not in summary:
                summary[process_name] = {
                    'count': 0,
                    'total_mem': 0,
                }

            # Преобразуем использование памяти
            try:
                mem_kb = int(mem.replace(',', '').replace('K', ''))
            except:
                mem_kb = 0

            summary[process_name]['count'] += 1
            summary[process_name]['total_mem'] += mem_kb

            # Форматируем строку для детализации
            detailed_lines.append(
                f"{process_name}\n"
                f"<code>PID: {pid} | Сессия: {session} | #{num} | Память: {mem}</code>"
            )

        # Создаем сводку
        response = "🖥️ <b>Сводка по процессам:</b>\n"
        sorted_processes = sorted(
            summary.items(),
            key=lambda x: x[1]['total_mem'],
            reverse=True
        )

        for process, data in sorted_processes[:10]:  # Только топ-10 процессов
            mem_mb = data['total_mem'] / 1024
            response += (
                f"\n• {process}: "
                f"{data['count']} экз., "
                f"{mem_mb:.1f} MB"
            )

        # Отправляем сводку
        bot.send_message(message.chat.id, response, parse_mode='HTML')

        # Отправляем детализацию как файл
        if detailed_lines:
            detailed_text = "\n\n".join(detailed_lines)
            file_io = io.BytesIO(detailed_text.encode('utf-8'))
            file_io.name = 'process_details.txt'
            bot.send_document(
                message.chat.id,
                file_io,
                caption="📋 Детальный список процессов"
            )
        else:
            bot.send_message(message.chat.id, "❌ Не найдено активных процессов")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('save_path'))
def handle_save_path_callback(call):
    """Обработка сохранения нового пути"""
    if not is_user_allowed(call.from_user.id):
        return
        
    _, name, path = call.data.split(':', 2)
    PATHS[name] = path
    save_paths(PATHS)
    
    bot.edit_message_text(
        f"✅ Путь сохранен: {name} → {path}",
        call.message.chat.id,
        call.message.message_id
    )

if __name__ == "__main__":
    import signal
    
    # Обработчик сигналов для корректного завершения
    def signal_handler(signum, frame):
        print(f"\nПолучен сигнал {signum}, завершение работы...")
        shutdown_procedures()
        sys.exit(0)
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Процедуры экстренного завершения
    def shutdown_procedures():
        print("Завершение фоновых процессов...")
        file_monitor.stop()
        
        # Остановка RDP-сессий
        for chat_id, session in list(RDP_SESSIONS.items()):
            try:
                session['stop_event'].set()
                session['thread'].join(timeout=2.0)
            except Exception as e:
                print(f"Ошибка остановки RDP: {e}")
        
        # Завершение командных сессий
        for chat_id, session in list(cmd_sessions.items()):
            try:
                if session['active']:
                    session['process'].terminate()
            except Exception as e:
                print(f"Ошибка остановки CMD: {e}")
        
        print("Все фоновые процессы остановлены")
    
    # Запуск мониторинга файлов
    file_monitor.start()
    
    backoff_time = 1  # Начальная задержка
    max_backoff = 60  # Максимальная задержка (1 минута)
    consecutive_errors = 0  # Счетчик последовательных ошибок
    
    while True:
        try:
            print(f"Запуск бота (попытка {consecutive_errors + 1})...")
            
            # Пытаемся отправить уведомление о запуске
            for user_id in ALLOWED_USER_IDS:
                try:
                    bot.send_message(
                        user_id, 
                        f"🟢 <b>Бот запущен</b>\nПопытка: {consecutive_errors + 1}", 
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Не удалось отправить уведомление: {str(e)}")
            
            print("Начало основного цикла...")
            bot.infinity_polling(
                timeout=90,
                long_polling_timeout=90,
                restart_on_change=True,
                skip_pending=True
            )
            
            # Сброс счетчика при успешном запуске
            consecutive_errors = 0
            backoff_time = 1
            
        except KeyboardInterrupt:
            print("Остановка по запросу пользователя")
            shutdown_procedures()
            break
            
        except Exception as e:
            error_msg = f"Критическая ошибка: {e}"
            print(error_msg)
            consecutive_errors += 1
            
            # Остановка фоновых процессов при сбое
            try:
                # RDP-сессии
                for chat_id, session in list(RDP_SESSIONS.items()):
                    try:
                        session['stop_event'].set()
                        session['thread'].join(timeout=1.0)
                    except:
                        pass
                    del RDP_SESSIONS[chat_id]
                
                # Командные сессии
                for chat_id, session in list(cmd_sessions.items()):
                    try:
                        if session['active']:
                            session['process'].terminate()
                    except:
                        pass
                cmd_sessions.clear()
                
            except Exception as inner_e:
                print(f"Ошибка при очистке: {inner_e}")
            
            # Экспоненциальная задержка с ограничением
            sleep_time = min(backoff_time, max_backoff)
            print(f"Повторный запуск через {sleep_time} сек. (ошибок подряд: {consecutive_errors})")
            time.sleep(sleep_time)
            
            # Увеличиваем задержку для следующей попытки
            backoff_time *= 2
            if backoff_time > max_backoff:
                backoff_time = max_backoff

    print("Работа бота завершена")