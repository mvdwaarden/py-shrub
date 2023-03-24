from configparser import NoOptionError

import shrub_util.core.logging as logging

from .arguments import Arguments
from .config import Config


class Secrets(Config):
    """Purpose: secrets implementation. Separation of secrets and standard configuration
    Author: Mando van der Waarden
    Date: 2020/05/15
    """

    def __init__(self, args=Arguments(), secretsfile=None):
        if secretsfile is None:
            filename = Config(args=args).get_setting("Secrets", "Filename")
        else:
            filename = secretsfile
        super().__init__(args=args, filename=filename, context=__name__)

    def get_secret(self, section, key, no_warn=True):
        try:
            value = self.get_setting(section, key, no_warn=True)
            logging.get_audit_logger().info(
                f"read secret {section}/{key}:{value is not None}"
            )
            return value
        except NoOptionError as ex:
            if not no_warn:
                # decision to log on debug level, warnings on functional level!
                logging.get_logger().debug(
                    f"unable to read secret {section}/{key}: {ex}"
                )
        except Exception as ex:
            logging.get_logger().error(
                f"unable to read secret {section}/{key}: {ex}", ex=ex
            )
        return None
