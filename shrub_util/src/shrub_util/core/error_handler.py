import threading
import traceback
from enum import Enum

import shrub_util.core.logging as logging
from shrub_util.core.logging import LogDecorator


class ErrorType(Enum):
    Technical = "technical"
    Functional = "functional"

    def from_str(value: str):
        if value == ErrorType.Technical.value:
            return ErrorType.Technical
        elif value == ErrorType.Functional.value:
            return ErrorType.Functional


class Error:
    g_error_number = 0

    def __init__(self, error_type, error_description, error_cause, error_tries):
        Error.g_error_number += 1
        self.error_number = Error.g_error_number
        self.error_thread_id = threading.current_thread().ident
        self.error_type = error_type
        self.error_description = error_description
        self.error_cause = error_cause
        self.error_tries = error_tries


class ErrorHandler:
    DEFAULT_LOGGER = "@error_handler"
    g_dispatch_table = {}
    g_default_handler = None
    g_logger = None

    def __init__(self, logger=DEFAULT_LOGGER):
        ErrorHandler.g_dispatch_table = {}
        ErrorHandler.g_default_handler = ErrorHandler.handle_default
        ErrorHandler.g_logger = logger

    @staticmethod
    def get_logger() -> LogDecorator:
        return logging.get_logger(path=ErrorHandler.DEFAULT_LOGGER)

    @staticmethod
    def handle_error(error: Error):
        ErrorHandler.get_logger().error(f"{error}", ex=error.error_cause)
        if type(error) in ErrorHandler.g_dispatch_table:
            do_exit, exit_code = ErrorHandler.g_dispatch_table[type(error)](error)
        elif ErrorHandler.g_default_handler is not None:
            do_exit, exit_code = ErrorHandler.g_default_handler(error)
        else:
            do_exit = False
        if do_exit is True:
            ErrorHandler.exit(exit_code)

    @staticmethod
    def exit(exit_code: int):
        exit(exit_code if exit_code is not None else 0)

    @staticmethod
    def register(error_type, handler):
        ErrorHandler.g_dispatch_table[error_type] = handler

    @staticmethod
    def set_default_handler(handler):
        ErrorHandler.g_default_handler = handler

    @staticmethod
    def handle_default(error):
        pass
