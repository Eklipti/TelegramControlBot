# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

def main() -> None:
    # Используем Pydantic Settings как единый источник правды
    from app.config import get_settings
    settings = get_settings()
    settings.ensure_directories()

    # Инициализируем логирование согласно Settings
    from app.core.logging import init_logging, info, critical
    init_logging(
        logs_dir=str(settings.get_logs_directory()),
        log_level=settings.log_level,  # теперь поддерживает TRACE (см. патч ниже)
    )

    info("Инициализация ControlBot завершена", "main")

    try:
        from app.app import main as run_aiogram
        info("Тяжелые модули импортированы успешно", "main")
        run_aiogram()
    except Exception as e:
        critical(f"Критическая ошибка при запуске приложения: {e}", "main")
        raise

if __name__ == "__main__":
    main()
