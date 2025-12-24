"""
Система логирования для TelegramControlBot v2.

Уровни логирования:
- CRITICAL: ошибки, которые приводят к аварийному завершению работы программы
- ERROR: ошибки, которые могут повлиять на функциональность, но приложение продолжает работать
- WARNING: предупреждения о ситуациях, которые могут привести к ошибке в будущем, но не влияют на текущую работу программы
- INFO: обычная информация о работе программы, которая помогает понять его функционирование
- DEBUG: подробная информация для отладки, полезная разработчикам при поиске и устранении ошибок
- TRACE: подробный уровень, записывающий всю информацию о выполнении, включая детали о вызовах методов и потоках
"""

import logging
import asyncio
import functools
from pathlib import Path

from .centralized_handler import CentralizedLoggingHandler


class TraceLogger(logging.Logger):
    """Кастомный логгер для уровня TRACE."""

    def trace(self, msg, *args, **kwargs):
        """Логирование на уровне TRACE."""
        if self.isEnabledFor(5):  # 5 = TRACE level
            self._log(5, msg, args, **kwargs)


class LoggingSystem:
    """Система логирования с поддержкой всех уровней."""

    def __init__(self, logs_dir: str = "./logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)

        logging.addLevelName(5, "TRACE")
        logging.addLevelName(50, "CRITICAL")

        logging.setLoggerClass(TraceLogger)

        self._setup_loggers()

    def _setup_loggers(self):
        """Настройка всех логгеров и обработчиков."""

        self.centralized_handler = CentralizedLoggingHandler()

        self.main_logger = self._create_logger(
            name="main",
            level=logging.DEBUG,
            filename="all.log",
            format_string="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )

    def _create_logger(self, name: str, level: int, filename: str, format_string: str) -> logging.Logger:
        """Создание логгера с файловым обработчиком и централизованным handler."""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        logger.handlers.clear()

        file_path = self.logs_dir / filename
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level)

        formatter = logging.Formatter(format_string)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        
        logger.addHandler(self.centralized_handler)

        logger.propagate = False

        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """Получение логгера с именем."""
        return logging.getLogger(name)

    def critical(self, message: str, logger_name: str = "main", **kwargs):
        """Логирование критической ошибки."""
        logger = self.get_logger(logger_name)
        logger.critical(message, **kwargs)

    def error(self, message: str, logger_name: str = "main", **kwargs):
        """Логирование ошибки."""
        logger = self.get_logger(logger_name)
        logger.error(message, **kwargs)

    def warning(self, message: str, logger_name: str = "main", **kwargs):
        """Логирование предупреждения."""
        logger = self.get_logger(logger_name)
        logger.warning(message, **kwargs)

    def info(self, message: str, logger_name: str = "main", **kwargs):
        """Логирование информации."""
        logger = self.get_logger(logger_name)
        logger.info(message, **kwargs)

    def debug(self, message: str, logger_name: str = "main", **kwargs):
        """Логирование отладочной информации."""
        logger = self.get_logger(logger_name)
        logger.debug(message, **kwargs)

    def trace(self, message: str, logger_name: str = "main", **kwargs):
        """Логирование детальной информации."""
        logger = self.get_logger(logger_name)
        if hasattr(logger, "trace"):
            logger.trace(message, **kwargs)
        else:
            logger.log(5, message, **kwargs)

    def trace_function_entry(
        self, function_name: str, args: tuple = None, kwargs: dict = None, logger_name: str = "main"
    ):
        """Логирование входа в функцию для уровня TRACE."""
        args_str = f"args={args}" if args else ""
        kwargs_str = f"kwargs={kwargs}" if kwargs else ""
        params = ", ".join(filter(None, [args_str, kwargs_str]))

        message = f"ENTER: {function_name}({params})"
        self.trace(message, logger_name)

    def trace_function_exit(self, function_name: str, result: any = None, logger_name: str = "main"):
        """Логирование выхода из функции для уровня TRACE."""
        result_str = f" -> {result}" if result is not None else ""
        message = f"EXIT:  {function_name}{result_str}"
        self.trace(message, logger_name)

    def trace_step(self, step: str, logger_name: str = "main"):
        """Логирование шага выполнения для уровня TRACE."""
        message = f"STEP:  {step}"
        self.trace(message, logger_name)


# Глобальный экземпляр системы логирования
logging_system: LoggingSystem | None = None


def init_logging(logs_dir: str = "./logs", log_level: str = "INFO") -> LoggingSystem:
    """
    Единая инициализация системы логирования.

    Args:
        logs_dir: Директория для файлов логов
        log_level: Уровень логирования (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Экземпляр системы логирования
    """
    global logging_system

    if logging_system is not None:
        return logging_system

    logs_path = Path(logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)

    # Очищаем файл all.log при каждом новом запуске
    all_log_path = logs_path / "all.log"
    if all_log_path.exists():
        all_log_path.unlink()

    logging_system = LoggingSystem(str(logs_path))

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.getLogger().setLevel(numeric_level)

    main_logger = logging_system.get_logger("main")
    main_logger.setLevel(numeric_level)

    logging_system.centralized_handler.setLevel(numeric_level)

    logging_system.info(f"Система логирования инициализирована. Уровень: {log_level}, Директория: {logs_path.absolute()}")

    return logging_system


def get_logging_system() -> LoggingSystem:
    """Получить глобальный экземпляр системы логирования."""
    global logging_system
    if logging_system is None:
        # Инициализируем с настройками по умолчанию, если не была вызвана init_logging
        logging_system = LoggingSystem()
    return logging_system


# Удобные функции для быстрого доступа
def critical(message: str, logger_name: str = "main", **kwargs):
    """Логирование критической ошибки."""
    get_logging_system().critical(message, logger_name, **kwargs)


def error(message: str, logger_name: str = "main", **kwargs):
    """Логирование ошибки."""
    get_logging_system().error(message, logger_name, **kwargs)


def warning(message: str, logger_name: str = "main", **kwargs):
    """Логирование предупреждения."""
    get_logging_system().warning(message, logger_name, **kwargs)


def info(message: str, logger_name: str = "main", **kwargs):
    """Логирование информации."""
    get_logging_system().info(message, logger_name, **kwargs)


def debug(message: str, logger_name: str = "main", **kwargs):
    """Логирование отладочной информации."""
    get_logging_system().debug(message, logger_name, **kwargs)


def trace(message: str, logger_name: str = "main", **kwargs):
    """Логирование детальной информации."""
    get_logging_system().trace(message, logger_name, **kwargs)


def trace_function_entry(function_name: str, args: tuple = None, kwargs: dict = None, logger_name: str = "main"):
    """Логирование входа в функцию."""
    get_logging_system().trace_function_entry(function_name, args, kwargs, logger_name)


def trace_function_exit(function_name: str, result: any = None, logger_name: str = "main"):
    """Логирование выхода из функции."""
    get_logging_system().trace_function_exit(function_name, result, logger_name)


def trace_step(step: str, logger_name: str = "main"):
    """Логирование шага выполнения."""
    get_logging_system().trace_step(step, logger_name)

def log_call(logger_name: str = "main"):
    """
    Декоратор: логирует вход/выход функции на уровне TRACE.
    Применим как к обычным, так и к async функциям.
    """
    def decorator(func):
        qualname = getattr(func, "__qualname__", getattr(func, "__name__", "func"))
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                trace_function_entry(qualname, args=args, kwargs=kwargs, logger_name=logger_name)
                try:
                    return await func(*args, **kwargs)
                finally:
                    trace_function_exit(qualname, logger_name=logger_name)
            return async_wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                trace_function_entry(qualname, args=args, kwargs=kwargs, logger_name=logger_name)
                try:
                    return func(*args, **kwargs)
                finally:
                    trace_function_exit(qualname, logger_name=logger_name)
            return wrapper
    return decorator
