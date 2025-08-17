# utils/logger.py
import logging
from PySide6.QtCore import QObject, Signal
from datetime import datetime
import sys # Make sure sys is imported

from utils.database import db_manager

class QtLogHandler(logging.Handler, QObject):
    new_log_record = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)
        self.database_log_level = logging.INFO 

    def emit(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        msg = self.format(record)

        self.new_log_record.emit(record.levelname, timestamp, msg)

        if record.levelno >= self.database_log_level:
            try:
                db_manager.add_log_entry(record.levelname, timestamp, msg)
            except Exception as e:
                print(f"ERROR: Failed to save log entry to database: {e}")


class AppLogger:
    _instance = None
    _logger = None
    _handler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._logger = logging.getLogger("NexusApp")
            cls._logger.setLevel(logging.DEBUG) # Keep logger level at DEBUG to capture all for UI
            cls._handler = QtLogHandler()
            formatter = logging.Formatter('%(message)s')
            cls._handler.setFormatter(formatter)
            if not any(isinstance(h, QtLogHandler) for h in cls._logger.handlers):
                cls._logger.addHandler(cls._handler)

            # --- ENSURE THIS IS PRESENT ---
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler.setLevel(logging.DEBUG) # Set to DEBUG to see all messages
            cls._logger.addHandler(console_handler)
            # --- END ENSURE ---

        return cls._instance

    def get_logger(self):
        return self._logger

    def get_handler(self):
        return self._handler

app_logger = AppLogger()