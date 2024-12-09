import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import TextIO, override

logger: logging.Logger = logging.getLogger(name="pytools.logger")


class CustomFormatter(logging.Formatter):
    """
    Custom log formatter with ANSI color codes for different log levels.
    """

    grey: str = "\x1b[38;20m"
    yellow: str = "\x1b[33;20m"
    red: str = "\x1b[31;20m"
    bold_red: str = "\x1b[31;1m"
    reset: str = "\x1b[0m"

    # Fixed-width log level (8 characters for alignment)
    log_format: str = "%(asctime)s.%(msecs)03d || %(levelname)-8s || %(module)s:%(funcName)s:%(lineno)d || %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    FORMATS: dict[int, str] = {
        logging.DEBUG: grey + log_format + reset,
        logging.INFO: grey + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: bold_red + log_format + reset,
    }

    @override
    def format(self, record: logging.LogRecord) -> str:
        log_fmt: str | None = self.FORMATS.get(record.levelno)
        formatter: logging.Formatter = logging.Formatter(
            fmt=log_fmt, datefmt=self.date_format
        )
        return formatter.format(record)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON log formatter.
    """

    @override
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """
        Format the time with microseconds.
        """
        from datetime import datetime

        # Get the time from the record as seconds since the epoch
        record_time: datetime = datetime.fromtimestamp(
            timestamp=record.created
        ).astimezone(tz=timezone.utc)

        # Format the time with microseconds if requested
        if datefmt:
            return record_time.strftime(format=datefmt)
        return record_time.isoformat()

    @override
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON object.
        """
        log_record: dict[str, str | int] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S.%f"),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        return json.dumps(obj=log_record, ensure_ascii=False)


class JSONFileHandler(logging.FileHandler):
    """
    Custom FileHandler to write logs as a valid JSON array.
    """

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: str | None = None,
        delay: bool = False,
    ) -> None:
        super().__init__(filename, mode, encoding, delay)
        self._first_log: bool = (
            not os.path.exists(path=filename) or os.path.getsize(filename) == 0
        )

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """
        Write log records to a file as part of a JSON array.
        """
        if self._first_log:
            # Start the JSON array if this is the first log
            _ = self.stream.write("[\n")
            self._first_log = False
        else:
            # Add a comma separator for subsequent logs
            _ = self.stream.write(",\n")

        # Write the formatted log record
        _ = self.stream.write(self.format(record))
        self.flush()

    @override
    def close(self) -> None:
        """
        Close the JSON array properly when the handler is closed.
        """
        if not self._first_log:
            _ = self.stream.write("\n]\n")
        super().close()


def setup_logging(log_to_file: bool = False, log_level: int = logging.INFO) -> None:
    """
    Configures logging to stdout and optionally to a file.

    Args:
        log_to_file (bool): If True, logs will also be written to a file.
        log_level (int): Minimum log level to display
    """
    # Create logger
    logger: logging.Logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(level=log_level)

    # Clear existing handlers (important if reconfiguring logging)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create console handler
    console_handler: logging.StreamHandler[TextIO] = logging.StreamHandler()
    console_handler.setLevel(level=log_level)
    console_handler.setFormatter(fmt=CustomFormatter())
    logger.addHandler(hdlr=console_handler)

    # Create file handler if logging to file
    if log_to_file:
        # make a logs folder if it doesn't exist
        if not os.path.exists(path="logs"):
            os.makedirs(name="logs")

        # Create file handler
        dt: str = datetime.now(timezone.utc).strftime(format="%Y-%m-%d_%H-%M-%S")
        file_handler: JSONFileHandler = JSONFileHandler(
            filename=f"logs/{sys.argv[0].split(sep='/')[-1]}_{dt}_UTC.json"
        )
        file_handler.setLevel(level=log_level)
        file_handler.setFormatter(fmt=JSONFormatter())
        logger.addHandler(hdlr=file_handler)
