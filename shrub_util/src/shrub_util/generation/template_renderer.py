from jinja2 import BaseLoader, Environment, FileSystemLoader, DictLoader


def get_loader(basepath):
    return FileSystemLoader(
        searchpath="" if basepath is None else basepath, followlinks=False
    )


def get_dictionary_loader(templates: dict):
    return DictLoader(templates)


class TemplateRenderer:
    SECTION_PREFIX = "Renderer"
    LOADER_KEY = "Loader"

    def __init__(self, basepath: str = None, get_loader=None):
        self.basepath = basepath
        self.environment = None
        self.get_loader = get_loader

    def render(self, template, **kwargs):
        """Render the template
        template: template to use
        kwargs: template context variables
        """
        if self.environment is None:
            self.environment = Environment(loader=self.__get_loader()(self.basepath))
        return self.environment.get_template(template).render(**kwargs)

    def __get_loader(self):
        if self.get_loader is None:
            return get_loader
        else:
            return self.get_loader
