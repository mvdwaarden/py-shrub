import logging
import os
import re
import sys
from shrub_util.generation.clone_dir import clone_directory
from shrub_util.generation.template_renderer import TemplateRenderer
from abc import ABC, abstractmethod
from typing import Dict

usage = """
    Shrubbery DevOPS utilities, assumes:
    - SHRUB_DEVOPS_CONFIG_ROOT environment variable is set 
    - or shrub-devops-config-root argument is defined  
    - or {{sys.prefix}}/data/shrub_devops folder exists
    Parameters:    
    - create: <repo|project>    
    - prepare-release: <major|minor|patch|build>
    - dry-run: check configuration
    - help: this text
     
    Mode - create
    - Create Repository     
    - Create Project
    Parameters:
    - name: name of the project/repository
    - description: description of the project/repository
    
    Mode - prepare-release
"""

PACKAGE_INFO_TEMPLATE = "./builtin/package_info.py.j2"


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


class Config:
    ENVIRONMENT_VAR = "SHRUB_DEVOPS_CONFIG_ROOT"
    ARG_VAR = "shrub-devops-config-root"
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


class BuildObject(ABC):
    def __init__(self, name=None, description=None):
        self.name = name
        self.description = description
        self.__template_root = os.path.join(Config.get_config_root(), "templates")

    def clone_directory(self, template_dir, build_object=None):
        fq_src_dir = os.path.join(self.__template_root, template_dir)
        clone_directory(src_dir=fq_src_dir, build_object=self)

    def get_renderer(self):
        return TemplateRenderer(self.__template_root)

    @abstractmethod
    def create(self):
        pass


class Dict2Object:
    def __init__(self, the_dict):
        self.__dict__ = the_dict


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
                build_object=Dict2Object(meta_data),
            )


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


ProjectDict = Dict[str, Project]


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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)


    def do_print_usage():
        print(usage)


    file = Config.get_arg("file")
    name = Config.get_arg("name")
    description = Config.get_arg("description")
    create = Config.get_arg("create")
    help = Config.has_arg("help")
    prepare_release = Config.get_arg("prepare-release")
    get_version = Config.get_arg("get-version", ".*")
    Config.dry_run = Config.has_arg("dry-run")

    if help:
        do_print_usage()
    elif file is not None:
        Generic(meta_data_file=file).create()
    elif create == "project":
        Project(name=name, description=description).create()
    elif create == "repo":
        Repository(name=name, description=description).create()
    elif prepare_release is not None:
        Repository(name=name, description=description).prepare_release(prepare_release)
    elif get_version is not None:
        for package_info_file, project_info in Repository().list_package_info():
            if re.search(get_version, package_info_file):
                filename = "shrub_devops.out" if file is None else file
                with open(filename, "w") as ofd:
                    ofd.write(project_info.version.semantic_version)
                break
