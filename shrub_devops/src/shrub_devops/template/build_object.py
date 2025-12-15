import os
from abc import ABC, abstractmethod

from shrub_devops.template.config import Config
from shrub_util.generation.clone_dir import clone_directory
from shrub_util.generation.template_renderer import TemplateRenderer


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
