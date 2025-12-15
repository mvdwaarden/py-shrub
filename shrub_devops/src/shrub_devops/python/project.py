import re
from typing import Dict

from shrub_devops.template.generic import PACKAGE_INFO_TEMPLATE
from shrub_devops.template.config import Config
from shrub_devops.template.build_object import BuildObject


class Project(BuildObject):
    def __init__(self, name=None, description=None, author=None, author_email=None):
        super().__init__(name, description)
        self.author = author
        self.author_email = author_email
        self.version = Version()

    def from_package_info_dict(self, package_info):
        self.name = package_info["__title__"]
        self.description = package_info["__description__"]
        self.author = package_info["__author__"]
        self.author_email = package_info["__author_email__"]
        self.version = Version().from_package_info_dict(package_info)
        return self

    def write_to_package_info(self, file):
        renderer = self.get_renderer()
        result = renderer.render(PACKAGE_INFO_TEMPLATE, build_object=self)
        print(result)
        if not Config.dry_run:
            with open(file, "w") as ofd:
                ofd.write(result)

    def create(self):
        self.clone_directory("init_project")


class Version:
    def __init__(self, semantic_version=None, build=None):
        self.major = self.minor = 0
        self.build = self.patch = 1
        if semantic_version is not None:
            self.set_from_semantic_version(semantic_version)
        if build is not None:
            self.build = int(build)

    def from_package_info_dict(self, package_info):
        self.set_from_semantic_version(package_info["__version__"])
        self.build = int(package_info["__build__"])
        return self

    def set_from_semantic_version(self, semver):
        pattern = re.compile("([^\\.]*).([^\\.]*).([^\\.]*)")
        match_result = pattern.match(semver)
        self.major = int(match_result.group(1))
        self.minor = int(match_result.group(2))
        self.patch = int(match_result.group(3))

    def increment(self, part):
        if part.lower() == "major":
            self.increment_major()
        elif part.lower() == "minor":
            self.increment_minor()
        elif part.lower() == "patch":
            self.increment_patch()
        elif part.lower() == "build":
            self.increment_build()

    def increment_major(self):
        self.major += 1
        self.minor = 0
        self.patch = 0
        return self

    def increment_minor(self):
        self.minor += 1
        self.patch = 0
        return self

    def increment_patch(self):
        self.patch += 1
        return self

    def increment_build(self):
        self.build += 1
        return self

    @property
    def semantic_version(self):
        return f"{self.major}.{self.minor}.{self.patch}"


ProjectDict = Dict[str, Project]
