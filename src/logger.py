import logging
from logging import StreamHandler, FileHandler, Formatter
from pathlib import Path

FORMATTER = Formatter(" %(levelname)s | %(module)s:%(funcName)s:line%(lineno)d - %(message)s")

class Logger:
    def __init__(
        self,
        level: int = logging.DEBUG,
        log_file: str | None = None,
        handlers: list[logging.Handler] | None = None,
        formatter: Formatter = FORMATTER
    ):
        self.level = level
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False   # evita log duplicado no root logger
        self.formatter = formatter

        default_handlers: list[logging.Handler] = [self._create_console_handler()]

        if log_file is not None:
            default_handlers.append(self._create_file_handler())  # <- sem parâmetro

        self.handlers = handlers or default_handlers
        self._setup_logger()

    def _create_console_handler(self) -> StreamHandler:
        handler = StreamHandler()
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        return handler

    def _create_file_handler(self) -> FileHandler:
        path = Path(self.log_file)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        # mode="w" => sobrescreve o arquivo a cada execução
        handler = FileHandler(path, mode="w", encoding="utf-8")
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        return handler
    
    def add_handler(self, handler: logging.Handler) -> None:
        self.logger.addHandler(handler)

    def _setup_logger(self) -> None:
        if self.logger.handlers:
            self.logger.handlers.clear()

        for handler in self.handlers:
            self.add_handler(handler)

        self.logger.setLevel(self.level)

    def get_logger(self) -> logging.Logger:
        return self.logger

logger = Logger(log_file="app.log").get_logger()
