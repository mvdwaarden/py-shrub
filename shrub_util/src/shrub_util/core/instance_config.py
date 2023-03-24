from abc import ABC, abstractmethod

from .config import Config
from .secrets import Secrets


class InstanceConfig(ABC):
    """Purpose : Base class for instance configuration
    Author : Mando van der Waarden
    Date : 2021/05/10
    """

    def __init__(self, instance_name):
        self._instance_name = instance_name

    def get_secret(self, secret):
        """ Use this method for retrieving API specific secrets"""
        secrets_ref = self.get_setting("SecretReference", no_warn=True)
        secrets = self._get_secrets()
        if secrets_ref is not None:
            section = self.get_config_prefix() + "-" + secrets_ref
        else:
            section = self.get_config_prefix() + "-" + self._instance_name

        return secrets.get_secret(section, secret)

    def get_setting(self, setting, default_value=None, no_warn=False):
        """ Use this method for retrieving API specific settings"""
        config = self._get_config()
        section = self.get_config_prefix() + "-" + self._instance_name

        return config.get_setting(section, setting, default_value, no_warn=no_warn)

    def _get_secrets(self):
        return Secrets()

    def _get_config(self):
        return Config()

    @abstractmethod
    def get_config_prefix(self) -> str:
        pass
