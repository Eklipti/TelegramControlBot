# Telegram Control Bot
# Copyright (C) 2025 Eklipti
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

def main() -> None:
    from app.config import get_settings
    settings = get_settings()
    project_root = settings.get_project_root()
    
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    (project_root / "data").mkdir(parents=True, exist_ok=True)
    (project_root / "exports").mkdir(parents=True, exist_ok=True)
    (project_root / "jsons").mkdir(parents=True, exist_ok=True)

    from app.core.logging import init_logging, info, critical
    init_logging(
        logs_dir=str(project_root / "logs"),
        log_level=settings.log_level,
    )

    info("Инициализация TelegramControlBot завершена", "main")

    try:
        from app.app import main as run_aiogram
        info("Тяжелые модули импортированы успешно", "main")
        run_aiogram()
    except Exception as e:
        critical(f"Критическая ошибка при запуске приложения: {e}", "main")
        raise

if __name__ == "__main__":
    main()

