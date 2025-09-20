# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Обработчики команд для экспорта логов в разные форматы.
"""

import asyncio
from datetime import datetime, timedelta

from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..core.logging import debug, error, info, trace, trace_function_entry, trace_function_exit
from ..core.metrics_decorator import track_command_metrics
from ..router import router
from ..services.centralized_logging import get_centralized_logger


@router.message(Command("logs_export"))
@track_command_metrics("logs_export")
async def handle_logs_export(message: Message) -> None:
    """Показывает меню экспорта логов."""
    trace_function_entry("handle_logs_export", 
                       args=(message.chat.id,), 
                       kwargs={"user_id": message.from_user.id, "username": message.from_user.username},
                       logger_name="logs_export_handler")
    
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    
    info(f"Пользователь {user_id} ({username}) запросил экспорт логов", "logs_export_handler")
    
    try:
        centralized_logger = get_centralized_logger()
        log_stats = centralized_logger.get_log_statistics()
        
        # Создаем клавиатуру для выбора формата экспорта
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("📄 JSON", callback_data="export_json"),
                    InlineKeyboardButton("📊 CSV", callback_data="export_csv")
                ],
                [
                    InlineKeyboardButton("🔧 XML", callback_data="export_xml"),
                    InlineKeyboardButton("📝 TXT", callback_data="export_txt")
                ],
                [
                    InlineKeyboardButton("🔍 Фильтры", callback_data="export_filters"),
                    InlineKeyboardButton("📈 Статистика", callback_data="export_stats")
                ]
            ]
        )
        
        stats_text = f"""
📋 <b>Экспорт логов ControlBot</b>

📊 <b>Статистика логов:</b>
• Всего логов: {log_stats.get('total_logs', 0)}
• Ошибок: {log_stats.get('errors_count', 0)}
• Предупреждений: {log_stats.get('warnings_count', 0)}

📈 <b>По уровням:</b>
"""
        
        for level, count in log_stats.get('logs_by_level', {}).items():
            stats_text += f"• {level}: {count}\n"
        
        stats_text += f"\n📝 <b>По логгерам:</b>\n"
        for logger_name, count in list(log_stats.get('logs_by_logger', {}).items())[:5]:
            stats_text += f"• {logger_name}: {count}\n"
        
        if len(log_stats.get('logs_by_logger', {})) > 5:
            stats_text += f"• ... и еще {len(log_stats['logs_by_logger']) - 5} логгеров\n"
        
        stats_text += f"\n🕐 <i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>"
        
        await message.answer(stats_text, reply_markup=keyboard)
        trace_function_exit("handle_logs_export", result="success", logger_name="logs_export_handler")
        
    except Exception as e:
        error(f"Ошибка получения статистики логов: {e}", "logs_export_handler")
        await message.answer(f"❌ Ошибка получения статистики логов: {e}")
        trace_function_exit("handle_logs_export", result=f"error: {e}", logger_name="logs_export_handler")


@router.message(Command("logs_export_json"))
@track_command_metrics("logs_export_json")
async def handle_logs_export_json(message: Message) -> None:
    """Экспортирует логи в JSON формате."""
    trace_function_entry("handle_logs_export_json", 
                       args=(message.chat.id,), 
                       kwargs={"user_id": message.from_user.id},
                       logger_name="logs_export_handler")
    
    try:
        centralized_logger = get_centralized_logger()
        
        # Показываем процесс экспорта
        processing_msg = await message.answer("⏳ Экспорт логов в JSON...")
        
        # Экспортируем логи
        export_path = await centralized_logger.export_to_json()
        
        # Отправляем файл
        from aiogram.types import FSInputFile
        file_input = FSInputFile(export_path, filename=f"controlbot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        await message.answer_document(file_input, caption="📄 Экспорт логов в JSON формате")
        
        # Удаляем сообщение о процессе
        await processing_msg.delete()
        
        info(f"Логи экспортированы в JSON пользователем {message.from_user.id}", "logs_export_handler")
        trace_function_exit("handle_logs_export_json", result="success", logger_name="logs_export_handler")
        
    except Exception as e:
        error(f"Ошибка экспорта логов в JSON: {e}", "logs_export_handler")
        await message.answer(f"❌ Ошибка экспорта логов в JSON: {e}")
        trace_function_exit("handle_logs_export_json", result=f"error: {e}", logger_name="logs_export_handler")


@router.message(Command("logs_export_csv"))
@track_command_metrics("logs_export_csv")
async def handle_logs_export_csv(message: Message) -> None:
    """Экспортирует логи в CSV формате."""
    trace_function_entry("handle_logs_export_csv", 
                       args=(message.chat.id,), 
                       kwargs={"user_id": message.from_user.id},
                       logger_name="logs_export_handler")
    
    try:
        centralized_logger = get_centralized_logger()
        
        processing_msg = await message.answer("⏳ Экспорт логов в CSV...")
        
        export_path = await centralized_logger.export_to_csv()
        
        from aiogram.types import FSInputFile
        file_input = FSInputFile(export_path, filename=f"controlbot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        await message.answer_document(file_input, caption="📊 Экспорт логов в CSV формате")
        
        await processing_msg.delete()
        
        info(f"Логи экспортированы в CSV пользователем {message.from_user.id}", "logs_export_handler")
        trace_function_exit("handle_logs_export_csv", result="success", logger_name="logs_export_handler")
        
    except Exception as e:
        error(f"Ошибка экспорта логов в CSV: {e}", "logs_export_handler")
        await message.answer(f"❌ Ошибка экспорта логов в CSV: {e}")
        trace_function_exit("handle_logs_export_csv", result=f"error: {e}", logger_name="logs_export_handler")


@router.message(Command("logs_export_xml"))
@track_command_metrics("logs_export_xml")
async def handle_logs_export_xml(message: Message) -> None:
    """Экспортирует логи в XML формате."""
    trace_function_entry("handle_logs_export_xml", 
                       args=(message.chat.id,), 
                       kwargs={"user_id": message.from_user.id},
                       logger_name="logs_export_handler")
    
    try:
        centralized_logger = get_centralized_logger()
        
        processing_msg = await message.answer("⏳ Экспорт логов в XML...")
        
        export_path = await centralized_logger.export_to_xml()
        
        from aiogram.types import FSInputFile
        file_input = FSInputFile(export_path, filename=f"controlbot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")
        await message.answer_document(file_input, caption="🔧 Экспорт логов в XML формате")
        
        await processing_msg.delete()
        
        info(f"Логи экспортированы в XML пользователем {message.from_user.id}", "logs_export_handler")
        trace_function_exit("handle_logs_export_xml", result="success", logger_name="logs_export_handler")
        
    except Exception as e:
        error(f"Ошибка экспорта логов в XML: {e}", "logs_export_handler")
        await message.answer(f"❌ Ошибка экспорта логов в XML: {e}")
        trace_function_exit("handle_logs_export_xml", result=f"error: {e}", logger_name="logs_export_handler")


@router.message(Command("logs_export_txt"))
@track_command_metrics("logs_export_txt")
async def handle_logs_export_txt(message: Message) -> None:
    """Экспортирует логи в текстовом формате."""
    trace_function_entry("handle_logs_export_txt", 
                       args=(message.chat.id,), 
                       kwargs={"user_id": message.from_user.id},
                       logger_name="logs_export_handler")
    
    try:
        centralized_logger = get_centralized_logger()
        
        processing_msg = await message.answer("⏳ Экспорт логов в TXT...")
        
        export_path = await centralized_logger.export_to_text()
        
        from aiogram.types import FSInputFile
        file_input = FSInputFile(export_path, filename=f"controlbot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        await message.answer_document(file_input, caption="📝 Экспорт логов в текстовом формате")
        
        await processing_msg.delete()
        
        info(f"Логи экспортированы в TXT пользователем {message.from_user.id}", "logs_export_handler")
        trace_function_exit("handle_logs_export_txt", result="success", logger_name="logs_export_handler")
        
    except Exception as e:
        error(f"Ошибка экспорта логов в TXT: {e}", "logs_export_handler")
        await message.answer(f"❌ Ошибка экспорта логов в TXT: {e}")
        trace_function_exit("handle_logs_export_txt", result=f"error: {e}", logger_name="logs_export_handler")


@router.message(Command("logs_filter"))
@track_command_metrics("logs_filter")
async def handle_logs_filter(message: Message) -> None:
    """Показывает фильтрованные логи."""
    trace_function_entry("handle_logs_filter", 
                       args=(message.chat.id,), 
                       kwargs={"user_id": message.from_user.id},
                       logger_name="logs_export_handler")
    
    try:
        # Парсим аргументы команды
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if not args:
            help_text = """
🔍 <b>Фильтрация логов</b>

<b>Использование:</b>
<code>/logs_filter [опции]</code>

<b>Опции:</b>
• <code>--level ERROR</code> - только ошибки
• <code>--logger auth</code> - только логи авторизации
• <code>--hours 24</code> - за последние N часов
• <code>--limit 100</code> - максимум записей

<b>Примеры:</b>
<code>/logs_filter --level ERROR --hours 1</code>
<code>/logs_filter --logger auth --limit 50</code>
"""
            await message.answer(help_text)
            trace_function_exit("handle_logs_filter", result="help", logger_name="logs_export_handler")
            return
        
        # Парсим параметры
        level = None
        logger_name = None
        hours = None
        limit = 100
        
        i = 0
        while i < len(args):
            if args[i] == "--level" and i + 1 < len(args):
                level = args[i + 1].upper()
                i += 2
            elif args[i] == "--logger" and i + 1 < len(args):
                logger_name = args[i + 1]
                i += 2
            elif args[i] == "--hours" and i + 1 < len(args):
                try:
                    hours = int(args[i + 1])
                except ValueError:
                    await message.answer("❌ Неверное значение для --hours")
                    return
                i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                except ValueError:
                    await message.answer("❌ Неверное значение для --limit")
                    return
                i += 2
            else:
                i += 1
        
        # Применяем фильтры
        centralized_logger = get_centralized_logger()
        
        start_time = None
        if hours:
            start_time = datetime.now() - timedelta(hours=hours)
        
        filtered_logs = centralized_logger.get_logs(
            level=level,
            logger_name=logger_name,
            start_time=start_time,
            limit=limit
        )
        
        if not filtered_logs:
            await message.answer("🔍 Логи не найдены по заданным фильтрам")
            trace_function_exit("handle_logs_filter", result="empty", logger_name="logs_export_handler")
            return
        
        # Формируем сообщение с логами
        logs_text = f"🔍 <b>Отфильтрованные логи ({len(filtered_logs)} записей)</b>\n\n"
        
        for log in filtered_logs[-20:]:  # Показываем последние 20
            timestamp = datetime.fromisoformat(log['timestamp']).strftime('%H:%M:%S')
            logs_text += f"<b>[{timestamp}]</b> {log['level']} | {log['logger_name']}\n"
            logs_text += f"{log['message']}\n\n"
        
        if len(filtered_logs) > 20:
            logs_text += f"... и еще {len(filtered_logs) - 20} записей"
        
        await message.answer(logs_text)
        trace_function_exit("handle_logs_filter", result=f"{len(filtered_logs)} logs", logger_name="logs_export_handler")
        
    except Exception as e:
        error(f"Ошибка фильтрации логов: {e}", "logs_export_handler")
        await message.answer(f"❌ Ошибка фильтрации логов: {e}")
        trace_function_exit("handle_logs_filter", result=f"error: {e}", logger_name="logs_export_handler")


@router.message(Command("logs_cleanup"))
@track_command_metrics("logs_cleanup")
async def handle_logs_cleanup(message: Message) -> None:
    """Очищает старые файлы экспорта."""
    trace_function_entry("handle_logs_cleanup", 
                       args=(message.chat.id,), 
                       kwargs={"user_id": message.from_user.id},
                       logger_name="logs_export_handler")
    
    try:
        # Парсим аргументы
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        days_to_keep = 30  # По умолчанию 30 дней
        
        if args and args[0].isdigit():
            days_to_keep = int(args[0])
        
        centralized_logger = get_centralized_logger()
        
        processing_msg = await message.answer(f"⏳ Очистка файлов экспорта старше {days_to_keep} дней...")
        
        await centralized_logger.cleanup_old_exports(days_to_keep)
        
        await processing_msg.edit_text(f"✅ Очистка завершена. Удалены файлы старше {days_to_keep} дней")
        
        info(f"Очистка файлов экспорта выполнена пользователем {message.from_user.id}", "logs_export_handler")
        trace_function_exit("handle_logs_cleanup", result="success", logger_name="logs_export_handler")
        
    except Exception as e:
        error(f"Ошибка очистки файлов экспорта: {e}", "logs_export_handler")
        await message.answer(f"❌ Ошибка очистки файлов экспорта: {e}")
        trace_function_exit("handle_logs_cleanup", result=f"error: {e}", logger_name="logs_export_handler")
