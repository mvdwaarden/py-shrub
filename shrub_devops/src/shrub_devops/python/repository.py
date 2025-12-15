import os
import re

from shrub_devops.template.config import Config
from shrub_devops.python.project import Project
from shrub_devops.template.build_object import BuildObject


class Repository(BuildObject):
    def __init__(self, name=None, description=None):
        super().__init__(name, description)
        self.applications = {}

    def create(self):
        self.clone_directory("init_repo")

    def list_package_info(self):
        for root, dirs, files in os.walk(".", followlinks=False):
            for file in [
                f
                for f in files
                if re.match(".*[\\\\/]src[\\\\/].*", root) is not None
                   and f == "package_info.py"
            ]:
                package_info_file = os.path.join(root, file)
                project_info = None
                with open(package_info_file) as ofd:
                    package_info = {}
                    exec(ofd.read(), package_info)
                    project_info = Project().from_package_info_dict(package_info)
                yield package_info_file, project_info

    def prepare_release(self, part):
        for package_info_file, project_info in self.list_package_info():
            print(f"increment {part} of {package_info_file}")
            if not Config.dry_run:
                project_info.version.increment(part)
                project_info.write_to_package_info(package_info_file)
