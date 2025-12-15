import logging
import os
import sys


class Config:
    ENVIRONMENT_VAR = "DEVOPS_CONFIG_ROOT"
    ARG_VAR = "config-root"
    dry_run = False

    @staticmethod
    def get_config_root():
        result = None
        if Config.ENVIRONMENT_VAR in os.environ:
            result = os.environ[Config.ENVIRONMENT_VAR]
            logging.info(f"use os.environ[{Config.ENVIRONMENT_VAR}]")

        if result is None:
            result = Config.get_arg(Config.ARG_VAR)
            if result is not None:
                logging.info(f"used sys.argv[{Config.ARG_VAR}]")

        if result is None:
            result = os.path.join(sys.prefix, "data", "shrub_devops")
            logging.info(f"use sys.prefix/data/shrub_devops")

        logging.info(f"use configuration at [{result}]")

        if not os.path.exists(result):
            logging.error(f"directory {result} does not exits")
            exit(-2)
        return result

    @staticmethod
    def get_arg(name, default_value=None):
        result = default_value
        i = 0
        for arg in sys.argv:
            if arg == f"-{name}":
                try:
                    result = sys.argv[i + 1]
                except Exception:
                    logging.error(f"argument -{name} found, but no value defined")
                break
            else:
                i += 1

        return result

    @staticmethod
    def has_arg(name):
        return f"-{name}" in sys.argv
