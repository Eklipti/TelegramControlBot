# Telegram Control Bot
# Copyright (C) 2025-2026 Eklipti
#
# Этот проект — свободное программное обеспечение: вы можете
# распространять и/или изменять его на условиях
# Стандартной общественной лицензии GNU (GNU GPL)
# третьей версии, опубликованной Фондом свободного ПО.
#
# Программа распространяется в надежде, что она будет полезной,
# но БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ; даже без подразумеваемой гарантии
# ТОВАРНОГО СОСТОЯНИЯ или ПРИГОДНОСТИ ДЛЯ КОНКРЕТНОЙ ЦЕЛИ.
# Подробности см. в Стандартной общественной лицензии GNU.
#
# Вы должны были получить копию Стандартной общественной
# лицензии GNU вместе с этой программой. Если это не так,
# см. <https://www.gnu.org/licenses/>.

"""
Обработчики команд для просмотра статистики и метрик.
"""

import json
from datetime import datetime
from pathlib import Path

from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..core.logging import error, info, trace_function_entry, trace_function_exit
from ..core.metrics_decorator import track_command_metrics
from ..router import router
from ..services.metrics import get_metrics_collector


@router.message(Command("stats"))
@track_command_metrics("stats")
async def handle_stats(message: Message) -> None:
    """Показывает общую статистику бота."""
    trace_function_entry(
        "handle_stats",
        args=(message.chat.id,),
        kwargs={"user_id": message.from_user.id, "username": message.from_user.username},
        logger_name="stats_handler",
    )

    user_id = message.from_user.id
    username = message.from_user.username or "без username"

    info(f"Пользователь {user_id} ({username}) запросил общую статистику", "stats_handler")

    try:
        metrics = get_metrics_collector()
        performance = metrics.get_performance_metrics()
        command_stats = metrics.get_command_statistics()
        metrics.get_user_statistics()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("📊 Команды", callback_data="exec:/stats_commands"),
                    InlineKeyboardButton("👥 Пользователи", callback_data="exec:/stats_users"),
                ],
                [
                    InlineKeyboardButton("⚡ Производительность", callback_data="exec:/stats_performance"),
                    InlineKeyboardButton("📈 Паттерны", callback_data="exec:/stats_patterns"),
                ],
                [
                    InlineKeyboardButton("🔍 Аудит", callback_data="exec:/stats_audit"),
                    InlineKeyboardButton("💾 Экспорт", callback_data="exec:/stats_export"),
                ],
            ]
        )

        stats_text = f"""
📊 <b>Общая статистика TelegramControlBot</b>

⏱️ <b>Время работы:</b> {performance["uptime_human"]}
👥 <b>Активных пользователей:</b> {performance["total_users"]}
🔄 <b>Активных сессий:</b> {performance["active_sessions"]}
📝 <b>Всего команд:</b> {performance["total_commands"]}

⚡ <b>Производительность:</b>
• Среднее время ответа: {performance["avg_response_time"]}s
• Минимальное время: {performance["min_response_time"]}s
• Максимальное время: {performance["max_response_time"]}s
• Процент ошибок: {performance["error_rate_percent"]}%

📈 <b>Топ команд:</b>
"""

        sorted_commands = sorted(command_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
        for i, (cmd, stats) in enumerate(sorted_commands, 1):
            stats_text += f"{i}. <code>{cmd}</code> - {stats['count']} раз\n"

        stats_text += f"\n🕐 <i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>"

        await message.answer(stats_text, reply_markup=keyboard)
        trace_function_exit("handle_stats", result="success", logger_name="stats_handler")

    except Exception as e:
        error(f"Ошибка получения статистики: {e}", "stats_handler")
        await message.answer(f"❌ Ошибка получения статистики: {e}")
        trace_function_exit("handle_stats", result=f"error: {e}", logger_name="stats_handler")


@router.message(Command("stats_commands"))
@track_command_metrics("stats_commands")
async def handle_stats_commands(message: Message) -> None:
    """Показывает детальную статистику команд."""
    trace_function_entry(
        "handle_stats_commands",
        args=(message.chat.id,),
        kwargs={"user_id": message.from_user.id},
        logger_name="stats_handler",
    )

    try:
        metrics = get_metrics_collector()
        command_stats = metrics.get_command_statistics()

        if not command_stats:
            await message.answer("📊 Статистика команд пуста")
            trace_function_exit("handle_stats_commands", result="empty", logger_name="stats_handler")
            return

        stats_text = "📊 <b>Детальная статистика команд</b>\n\n"

        sorted_commands = sorted(command_stats.items(), key=lambda x: x[1]["count"], reverse=True)

        for cmd, stats in sorted_commands:
            stats_text += f"<b>🔹 {cmd}</b>\n"
            stats_text += f"• Использований: {stats['count']}\n"
            stats_text += f"• Среднее время: {stats['avg_time']}s\n"
            stats_text += f"• Уникальных пользователей: {stats['unique_users']}\n"
            stats_text += f"• Процент ошибок: {stats['error_rate']}%\n"
            if stats["last_used"]:
                last_used = datetime.fromisoformat(stats["last_used"])
                stats_text += f"• Последнее использование: {last_used.strftime('%d.%m.%Y %H:%M')}\n"
            stats_text += "\n"

        if len(stats_text) > 4000:
            stats_text = stats_text[:4000] + "\n... (показаны первые команды)"

        await message.answer(stats_text)
        trace_function_exit("handle_stats_commands", result="success", logger_name="stats_handler")

    except Exception as e:
        error(f"Ошибка получения статистики команд: {e}", "stats_handler")
        await message.answer(f"❌ Ошибка получения статистики команд: {e}")
        trace_function_exit("handle_stats_commands", result=f"error: {e}", logger_name="stats_handler")


@router.message(Command("stats_users"))
@track_command_metrics("stats_users")
async def handle_stats_users(message: Message) -> None:
    """Показывает статистику пользователей."""
    trace_function_entry(
        "handle_stats_users",
        args=(message.chat.id,),
        kwargs={"user_id": message.from_user.id},
        logger_name="stats_handler",
    )

    try:
        metrics = get_metrics_collector()
        user_stats = metrics.get_user_statistics()

        if not user_stats:
            await message.answer("👥 Статистика пользователей пуста")
            trace_function_exit("handle_stats_users", result="empty", logger_name="stats_handler")
            return

        stats_text = "👥 <b>Статистика пользователей</b>\n\n"

        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["commands_used"], reverse=True)

        for user_id_str, stats in sorted_users[:10]:  # Показываем топ-10
            status = "🟢 Активен" if stats["is_active"] else "⚪ Неактивен"
            stats_text += f"<b>🔹 Пользователь {user_id_str}</b> {status}\n"
            stats_text += f"• Команд использовано: {stats['commands_used']}\n"
            stats_text += f"• Сессий: {stats['sessions']}\n"
            stats_text += f"• Среднее время на команду: {stats['avg_time_per_command']}s\n"
            if stats["favorite_command"]:
                stats_text += f"• Любимая команда: <code>{stats['favorite_command']}</code>\n"
            if stats["last_activity"]:
                last_activity = datetime.fromisoformat(stats["last_activity"])
                stats_text += f"• Последняя активность: {last_activity.strftime('%d.%m.%Y %H:%M')}\n"
            stats_text += "\n"

        if len(sorted_users) > 10:
            stats_text += f"... и еще {len(sorted_users) - 10} пользователей"

        await message.answer(stats_text)
        trace_function_exit("handle_stats_users", result="success", logger_name="stats_handler")

    except Exception as e:
        error(f"Ошибка получения статистики пользователей: {e}", "stats_handler")
        await message.answer(f"❌ Ошибка получения статистики пользователей: {e}")
        trace_function_exit("handle_stats_users", result=f"error: {e}", logger_name="stats_handler")


@router.message(Command("stats_performance"))
@track_command_metrics("stats_performance")
async def handle_stats_performance(message: Message) -> None:
    """Показывает метрики производительности."""
    trace_function_entry(
        "handle_stats_performance",
        args=(message.chat.id,),
        kwargs={"user_id": message.from_user.id},
        logger_name="stats_handler",
    )

    try:
        metrics = get_metrics_collector()
        performance = metrics.get_performance_metrics()

        stats_text = f"""
⚡ <b>Метрики производительности</b>

⏱️ <b>Время работы:</b>
• Общее время: {performance["uptime_human"]}
• В секундах: {performance["uptime_seconds"]}s

📊 <b>Статистика команд:</b>
• Всего выполнено: {performance["total_commands"]}
• Уникальных пользователей: {performance["total_users"]}
• Активных сессий: {performance["active_sessions"]}

⚡ <b>Время ответа:</b>
• Среднее: {performance["avg_response_time"]}s
• Минимальное: {performance["min_response_time"]}s
• Максимальное: {performance["max_response_time"]}s

❌ <b>Ошибки:</b>
• Процент ошибок: {performance["error_rate_percent"]}%

🕐 <i>Обновлено: {datetime.now().strftime("%H:%M:%S")}</i>
"""

        await message.answer(stats_text)
        trace_function_exit("handle_stats_performance", result="success", logger_name="stats_handler")

    except Exception as e:
        error(f"Ошибка получения метрик производительности: {e}", "stats_handler")
        await message.answer(f"❌ Ошибка получения метрик производительности: {e}")
        trace_function_exit("handle_stats_performance", result=f"error: {e}", logger_name="stats_handler")


@router.message(Command("stats_patterns"))
@track_command_metrics("stats_patterns")
async def handle_stats_patterns(message: Message) -> None:
    """Показывает паттерны использования."""
    trace_function_entry(
        "handle_stats_patterns",
        args=(message.chat.id,),
        kwargs={"user_id": message.from_user.id},
        logger_name="stats_handler",
    )

    try:
        metrics = get_metrics_collector()
        patterns = metrics.get_usage_patterns()

        stats_text = "📈 <b>Паттерны использования</b>\n\n"

        if patterns["most_used_commands"]:
            stats_text += "<b>🔥 Топ команд:</b>\n"
            for i, (cmd, count) in enumerate(patterns["most_used_commands"][:5], 1):
                stats_text += f"{i}. <code>{cmd}</code> - {count} раз\n"
            stats_text += "\n"

        if patterns["peak_hours"]:
            stats_text += "<b>⏰ Пиковые часы:</b>\n"
            for i, (hour, count) in enumerate(patterns["peak_hours"][:5], 1):
                stats_text += f"{i}. {hour} - {count} команд\n"
            stats_text += "\n"

        daily_usage = patterns["daily_usage"]
        if daily_usage:
            stats_text += "<b>📅 Активность по дням (последние 7 дней):</b>\n"
            sorted_days = sorted(daily_usage.items(), reverse=True)[:7]
            for day, count in sorted_days:
                day_date = datetime.fromisoformat(day).strftime("%d.%m")
                stats_text += f"• {day_date}: {count} команд\n"

        await message.answer(stats_text)
        trace_function_exit("handle_stats_patterns", result="success", logger_name="stats_handler")

    except Exception as e:
        error(f"Ошибка получения паттернов использования: {e}", "stats_handler")
        await message.answer(f"❌ Ошибка получения паттернов использования: {e}")
        trace_function_exit("handle_stats_patterns", result=f"error: {e}", logger_name="stats_handler")


@router.message(Command("stats_audit"))
@track_command_metrics("stats_audit")
async def handle_stats_audit(message: Message) -> None:
    """Показывает аудит-трейлы."""
    trace_function_entry(
        "handle_stats_audit",
        args=(message.chat.id,),
        kwargs={"user_id": message.from_user.id},
        logger_name="stats_handler",
    )

    try:
        metrics = get_metrics_collector()
        audit_trails = metrics.get_audit_trails(limit=20)  # Последние 20 событий

        if not audit_trails:
            await message.answer("🔍 Аудит-трейлы пусты")
            trace_function_exit("handle_stats_audit", result="empty", logger_name="stats_handler")
            return

        stats_text = "🔍 <b>Последние события аудита</b>\n\n"

        for trail in reversed(audit_trails):  # Показываем в обратном порядке (новые сверху)
            timestamp = datetime.fromisoformat(trail["timestamp"])
            event_type = trail.get("event_type", "unknown")

            stats_text += f"<b>🔹 {event_type}</b>\n"
            stats_text += f"• Время: {timestamp.strftime('%H:%M:%S')}\n"

            if "user_id" in trail:
                stats_text += f"• Пользователь: {trail['user_id']}\n"

            if "command" in trail:
                stats_text += f"• Команда: <code>{trail['command']}</code>\n"

            if "execution_time" in trail:
                stats_text += f"• Время выполнения: {trail['execution_time']:.3f}s\n"

            if "success" in trail:
                status = "✅" if trail["success"] else "❌"
                stats_text += f"• Статус: {status}\n"

            if trail.get("error_msg"):
                stats_text += f"• Ошибка: {trail['error_msg'][:100]}...\n"

            stats_text += "\n"

        if len(stats_text) > 4000:
            stats_text = stats_text[:4000] + "\n... (показаны последние события)"

        await message.answer(stats_text)
        trace_function_exit("handle_stats_audit", result="success", logger_name="stats_handler")

    except Exception as e:
        error(f"Ошибка получения аудит-трейлов: {e}", "stats_handler")
        await message.answer(f"❌ Ошибка получения аудит-трейлов: {e}")
        trace_function_exit("handle_stats_audit", result=f"error: {e}", logger_name="stats_handler")


@router.message(Command("stats_export"))
@track_command_metrics("stats_export")
async def handle_stats_export(message: Message) -> None:
    """Экспортирует статистику в JSON файл."""
    trace_function_entry(
        "handle_stats_export",
        args=(message.chat.id,),
        kwargs={"user_id": message.from_user.id},
        logger_name="stats_handler",
    )

    try:
        metrics = get_metrics_collector()

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "performance_metrics": metrics.get_performance_metrics(),
            "command_statistics": metrics.get_command_statistics(),
            "user_statistics": metrics.get_user_statistics(),
            "usage_patterns": metrics.get_usage_patterns(),
            "audit_trails": metrics.get_audit_trails(limit=1000),
        }

        import tempfile

        from aiogram.types import FSInputFile

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            temp_file_path = f.name

        file_input = FSInputFile(
            temp_file_path, filename=f"TelegramControlBot_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        await message.answer_document(file_input, caption="📊 Экспорт статистики TelegramControlBot")

        Path(temp_file_path).unlink()

        info(f"Статистика экспортирована пользователем {message.from_user.id}", "stats_handler")
        trace_function_exit("handle_stats_export", result="success", logger_name="stats_handler")

    except Exception as e:
        error(f"Ошибка экспорта статистики: {e}", "stats_handler")
        await message.answer(f"❌ Ошибка экспорта статистики: {e}")
        trace_function_exit("handle_stats_export", result=f"error: {e}", logger_name="stats_handler")
