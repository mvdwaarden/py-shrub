import logging
import re

from shrub_devops.python.project import Project
from shrub_devops.python.repository import Repository
from shrub_devops.template.config import Config
from shrub_devops.template.generic import Generic
from shrub_devops.java.environment import Environment

usage = """
    Shrubbery DevOPS utilities, assumes:
    - DEVOPS_CONFIG_ROOT environment variable is set 
    - or -config-root argument is defined  
    - or {{sys.prefix}}/data/shrub_devops folder exists
    The variable points to a folder which contains the following folders:
    - templates
    --- builtin
    --- init_project
    --- init_repo
    - meta_data 
    --- init_project.yaml
    --- init_repo.yaml
    Parameters:    
    - create: <repo|project|venv>    
    - prepare-release: <major|minor|patch|build>
    - dry-run: check configuration
    - help: this text
     
    Mode - create
    - Create Repository     
    - Create Project
    - Create virtual environment
    Parameters:
    - name: name of the project/repository
    - description: description of the project/repository
    - venv-type: type of virtual environment <java> (default = java)
    
    Mode - prepare-release
"""

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
    elif create == "venv":
        jdk = Config.get_arg("jdk", )
        maven = Config.get_arg("maven")
        gradle = Config.get_arg("gradle")
        environment_type = Config.get_arg("venv-type", "java")
        Environment(name=name, description=description, environment_type=environment_type,
                    maven=maven, gradle=gradle, jdk=jdk).create()


    elif prepare_release is not None:
        Repository(name=name, description=description).prepare_release(prepare_release)
    elif get_version is not None:
        for package_info_file, project_info in Repository().list_package_info():
            if re.search(get_version, package_info_file):
                filename = "shrub_devops.out" if file is None else file
                with open(filename, "w") as ofd:
                    ofd.write(project_info.version.semantic_version)
                break
