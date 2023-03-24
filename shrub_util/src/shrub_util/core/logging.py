import io
import logging as pylogging
import logging.config as pylogconfig
import os
import re
import traceback

import yaml


def _get_module(path: str):
    # check for explicit logger
    if path is not None and path.startswith("@"):
        module = path[1:]
    else:
        if path is None:
            path = __file__

        found = False
        # look backward from path parts and check for root folder
        # -> this is the module name
        for part in os.path.normpath(path).replace("\\", "/").split("/")[::-1]:
            if part == "src" or part == "site-packages":
                found = True
                break
            module = part

        if not found:
            print(f"logger: defaulting to root for {path}")
            module = "root"

    return module


class LogDecorator:
    g_error_handler = None
    g_verbose = True

    def __init__(self, logger, verbose: bool = True):
        self.logger = logger
        self.verbose = verbose

    def getChild(self, suffix):
        return LogDecorator(self.logger.getChild(suffix))

    def log(self, level, msg, *args, **kwargs):
        self.logger.log(level, msg, *args, **kwargs)

    def error(
        self,
        msg,
        err_context: str = None,
        err_no: int = None,
        ex: Exception = None,
        *args,
        **kwargs,
    ):
        if LogDecorator.g_verbose:
            trace_file = io.StringIO()
            trace_file.write(" verbose : ")
        else:
            trace_file = None
        traceback.print_stack(file=trace_file)
        if isinstance(ex, Exception):
            try:
                traceback.print_exc(file=trace_file)
            except Exception as ex:
                print(f"error printing exception info {ex}")
        if LogDecorator.g_error_handler is not None:
            LogDecorator.g_error_handler(err_context, err_no, ex, *args, **kwargs)
        if trace_file is not None:
            exception_info = trace_file.getvalue()
        else:
            exception_info = ""
        self.logger.error(f"{msg}{exception_info}", *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


def get_logger(path=None) -> LogDecorator:
    return LogDecorator(logger=pylogging.getLogger(_get_module(path)))


def get_audit_logger() -> LogDecorator:
    return LogDecorator(logger=pylogging.getLogger("audit"))


def get_log_config(filename=None, place_holders=None):
    log_config = None
    try:
        with open(filename) as lcif:
            content = lcif.read()
            if place_holders is not None:
                content = content.format(**place_holders)
            log_config = yaml.safe_load(content)
    except Exception as ex:
        pylogging.error(f"unable to read log configuration {filename} {str(ex)}")

    return log_config


def configure(filename, place_holders=None, error_handler=None, verbose=True):
    if not os.path.exists("log"):
        os.mkdir("log")
    pylogconfig.dictConfig(get_log_config(filename, place_holders))
    set_error_handler(error_handler)
    set_verbose(verbose)


def set_error_handler(error_handler):
    """The error handler is called when ever an error is logged.
    The signature is the same as the error() method:
      LogDecorator.g_error_handler(err_context, err_no, ex, *args, **kwargs)

    """
    LogDecorator.g_error_handler = error_handler


def set_verbose(verbose):
    """sets the logging verbosity of ONLY errors.
    - true: adds the stack trace to the error log
    - false: prints the errors as is

    """
    LogDecorator.g_verbose = verbose


def configure_console(verbose=True):
    console_config = """
version: 1
formatters:
    default:
        format: '%(asctime)s - %(levelname)s - %(process)d - %(thread)d %(message)s'
        datefmt: '%Y-%m-%d %H:%M:%S'
handlers:
    console:
        level: INFO
        class: logging.StreamHandler
        formatter: default
        stream: ext://sys.stdout
loggers:
    shrub_util:
        level: INFO
        handlers: [console]
        propagate: True
    root:
        level: INFO
        handlers: [console]
        propagate: True
disable_existing_loggers: False
    """
    pylogconfig.dictConfig(yaml.safe_load(console_config))
    set_verbose(verbose)


def trace_message(context: str, message: str, headers: dict):
    def obfuscate_header(key, value):
        if key in ["Authorization"]:
            return "***OBFUSCATED***"
        else:
            return value

    def obfuscate_message(message):
        if message is None:
            return ""
        if type(message) is bytes:
            message = str(message, "utf-8")
        for tag in ["Password", "BSN"]:
            message = re.sub(
                f"{tag}([^>].*)>[^<]*<\\/([^:]*):{tag}",
                f"{tag}\g<1>>***OBFUSCATED***</\g<2>:{tag}",
                message,
            )
        return message

    try:
        if headers is None:
            headers = {}
        header_info = ";".join(
            [f"{key}={obfuscate_header(key, value)}" for key, value in headers.items()]
        )
        log_message = obfuscate_message(message)
        get_logger("@archi_message_trace").info(
            f"{context} -  http-headers {header_info}"
            f" - length {len(log_message)}"
            f" - message {log_message}"
        )
    except Exception as ex:
        get_logger().error("problem obfuscating message for logging", ex=ex)
        return "obfuscation error"
