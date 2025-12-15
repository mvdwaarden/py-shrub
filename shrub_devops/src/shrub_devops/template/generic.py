import logging

import yaml

from shrub_devops.template.config import Config
from shrub_devops.template.build_object import BuildObject


class Generic(BuildObject):
    def __init__(self, meta_data_file):
        super().__init__()
        self.meta_data_file = meta_data_file

    def create(self):
        meta_data = None
        with open(self.meta_data_file) as ifd:
            meta_data = yaml.safe_load(ifd)
            if "template_dir" not in meta_data:
                logging.error(
                    f"{self.meta_data_file} may not be a generic build meta data file"
                )

        if meta_data is not None:
            if "dry_run" in meta_data:
                Config.dry_run = meta_data["dry_run"]
            self.clone_directory(
                template_dir=meta_data["template_dir"],
                build_object=Dict2Object(meta_data)
            )


PACKAGE_INFO_TEMPLATE = "./builtin/package_info.py.j2"


class Dict2Object:
    def __init__(self, the_dict):
        self.__dict__ = the_dict
