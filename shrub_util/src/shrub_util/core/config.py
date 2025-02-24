import os
from configparser import ConfigParser, NoOptionError, NoSectionError

import shrub_util.core.file as file
import shrub_util.core.logging as logging

from .arguments import Arguments


class Config:
    """Purpose: configuration implementation.
    Author: Mando van der Waarden
    Date: 2020/05/19

    The configuration file can be explicitly define by:
    - Environment variable: {self.ENV_CONFIG_INI}
    - Commandline argument: {self.ARG_CONFIG_INI}
    Precedence is: [Commandline argument, Environment variable]
    """
    ARG_CONFIG_INI = "config-ini"
    ENV_CONFIG_INI = "SHRUB_CONFIG_INI"

    def __init__(self, filename=None, args=None, context=__name__):
        self.sections = {}
        self.context = context
        self.config: ConfigParser = None
        if args is None:
            self.args = Arguments()
        else:
            self.args = args
        if filename is None:
            self.filename = self.args.get_arg(Config.ARG_CONFIG_INI)
            if self.filename is None and Config.ENV_CONFIG_INI in os.environ:
                self.filename = os.environ[Config.ENV_CONFIG_INI]
        else:
            self.filename = filename
        if self.filename is None:
            self.filename = os.path.join(".")

    def __get_config(self, no_warn=False):
        if self.config is not None:
            return self.config
        try:
            self.config = ConfigParser()
            if no_warn and not file.file_exists(self.context, self.filename):
                logging.get_logger().info(
                    f"unable to find config file {self.filename}, use"
                    f" ARG:{self.ARG_CONFIG_INI} or"
                    f" ENV:{self.ENV_CONFIG_INI}"
                )
                return self.config
            self.config.read_string(file.file_read_file(self.context, self.filename))
            self.path = os.path.dirname(self.filename)
            self.startup_dir = os.getcwd()
            logging.get_logger().debug(
                f"read config file {self.filename} "
                f"with sections {self.config.sections()}"
            )
        except Exception as ex:
            if no_warn is False:
                logging.get_logger().error(
                    f"unable to read config file {self.filename}, use"
                    f" ARG:{self.ARG_CONFIG_INI} or"
                    f" ENV:{self.ENV_CONFIG_INI} {ex}",
                    ex=ex,
                )
            else:
                logging.get_logger().info(
                    f"unable to read config file {self.filename}, use"
                    f" ARG:{self.ARG_CONFIG_INI} or"
                    f" ENV:{self.ENV_CONFIG_INI} {ex}"
                )
        return self.config

    def get_global_setting(self, key, default_value=None, no_warn=False):
        return self.get_setting("Global", key, default_value, no_warn)

    def get_setting(self, section, key, default_value=None, no_warn=False):
        try:
            value = (
                self.__get_config(no_warn=no_warn)
                .get(section, key)
                .format(config_path=self.path, startup_dir=self.startup_dir)
            )
            logging.get_logger().debug(
                f"read configuration value {section}/{key}:{value is not None}"
            )
            if type(default_value) is int:
                return int(value)
            elif type(default_value) is float:
                return float(value)
            elif type(default_value) is bool:
                if value.lower() in ["false", "disabled", "no"]:
                    return False
                elif value.lower() in ["true", "enabled", "yes"]:
                    return True
                logging.get_logger().warning(
                    f"returning false for {section}/{key}: {value}"
                    f" from {self.filename}"
                )
                return False
            else:
                return value
        except (NoOptionError, NoSectionError) as ex:
            if not no_warn:
                # decision to log on debug level, warnings on functional level!
                logging.get_logger().debug(
                    f"unable to read configuration value {section}/{key}: {ex}"
                    f" from {self.filename}"
                )
        except Exception as ex:
            logging.get_logger().error(
                f"unable to read configuration {section}/{key}: {ex}", ex=ex
            )
        return default_value

    def get_section(self, section) -> "ConfigSection":
        if section not in self.sections:
            self.sections[section] = ConfigSection(self, section)
        return self.sections[section]

    # TODO: remove in future version
    # def __getattr__(self, section):
    #     return self.get_section(section)
    #
    # def __getitem__(self, section):
    #     return self.get_section(section)

    """ Purpose: Get dictionary from a configuration section
        Configuration sample
        [SectionPrefix-Instance]        
        Administrator.GetUsers=/users/get
        Administrator.GetGroups=/groups/get
    
        Python code:
        the_dict = Config().get_section_dictionary("SectionPrefix-Instance","Administrator.")
        
        Where the dictionary the_dict contains: {
            "GetUsers": "/users/get",
            "GetGroups": "/groups/get"
        }
    """

    def get_settings_dictionary(self, section, key_prefix: str, no_warn=False) -> dict:
        result = {}
        try:
            for key in self.__get_config(config_parser_transformation=lambda x: x)[
                section
            ]:
                if key.startswith(key_prefix):
                    result[key] = self.get_setting(section, key, no_warn=no_warn)
        except KeyError as ex:
            if not no_warn:
                # decision to log on debug level, warnings on functional level!
                logging.get_logger().debug(
                    f"unable to read configuration value dictionary {section}/{key_prefix}: {ex}"
                    f" from {self.filename}"
                )
        return result


class ConfigSection:
    def __init__(self, config: Config, section):
        self.config = config
        self.section = section

    def get_setting(self, key, default_value=None, no_warn=False):
        return self.config.get_setting(self.section, key, default_value, no_warn)

    """ Purpose: standardize secret reference
        
        The secret reference can be either absolute or relative
        Absolute secret reference sample
        -   Configuration file: 
            [SectionPrefix-Instance]
            SecretReference = @AbsoluteSecretSection
        -   Secrets file:
            [AbsoluteSecretSection]
            key1=secret1
            ...
        Relative secret reference sample
        -   Configuration file: 
            [SectionPrefix-Instance]
            SecretReference = RelativeSecretSection
        -   Secrets file:
            [SectionPrefix-Instance-RelativeSecretSection]
            key1=secret1
            ...
        """

    def get_secret_reference(self) -> str:
        raw_secret_reference = self.get_setting("SecretReference")
        if not raw_secret_reference:
            logging.get_logger().error(
                f"no SecretReference found for [{self.section}] check configuration"
            )
            secret_reference = None
        elif raw_secret_reference[0] == "@":
            secret_reference = raw_secret_reference[1:]
        else:
            secret_reference = f"{self.section}-{raw_secret_reference}"
        return secret_reference
