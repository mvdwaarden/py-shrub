import os
import shutil

from jinja2 import Environment, FileSystemLoader

import shrub_util.core.logging as logging


class CloneObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class CloneDirectoryTemplateRenderer:
    def __init__(self, basepath: str = None):
        self.basepath = basepath
        self.environment = None

    def snake_to_camel(self, value):
        return "".join(part.capitalize() or "_" for part in value.split("_"))

    def to_upper(self,  value):
        return value.upper() if isinstance(value, str) else str(value).upper() if value else ""

    def snake_get_first(self, value):
        if isinstance(value, str):
            idx = value.find("_")
            if idx >=0:
                return value[:idx]
        return value


    def render(self, template, **kwargs):
        """Render the template
        template: template to use
        kwargs: template context variables
        """
        if self.environment is None:
            self.environment = Environment(
                loader=FileSystemLoader(
                    searchpath="" if self.basepath is None else self.basepath,
                    followlinks=False,
                )
            )
            self.environment.filters["snake_to_camel"] = self.snake_to_camel
            self.environment.filters["upper"] = self.to_upper
            self.environment.filters["snake_get_first"] = self.snake_get_first
        return self.environment.get_template(template).render(**kwargs)


def clone_directory(src_dir, target_dir=None, dry_run=False, **kwargs):
    fq_src_dir = src_dir
    if target_dir is None:
        target_dir = os.getcwd()
    logging.get_logger().info(f"clone directory from {fq_src_dir} -> {target_dir}")
    renderer = CloneDirectoryTemplateRenderer(fq_src_dir)
    for src_root, src_subdirs, src_files in os.walk(fq_src_dir):
        if len(src_root) > len(fq_src_dir):
            src_reldir = src_root[len(fq_src_dir) + 1:]
        else:
            src_reldir = ""
        dest_root = os.path.join(target_dir, src_reldir)
        for src_subdir in src_subdirs:
            dest_dir = os.path.join(dest_root, src_subdir)
            dest_dir = dest_dir.format(**kwargs)
            if not os.path.exists(dest_dir):
                logging.get_logger().info(f"makedirs({dest_dir})")
                if not dry_run:
                    os.makedirs(dest_dir)
        for src_file in src_files:
            fq_src_file = os.path.join(src_root, src_file)
            src_filename, src_fileext = os.path.splitext(src_file)
            if src_fileext is not None and src_fileext.lower() == ".j2":
                fq_dest_file = os.path.join(dest_root, src_filename)
                fq_dest_file = fq_dest_file.format(**kwargs)
                template_file = os.path.join(src_reldir, src_file).replace("\\", "/")
                result = renderer.render(template_file, **kwargs)
                logging.get_logger().info(f"write to ({fq_dest_file},{result})")
                if not dry_run:
                    with open(fq_dest_file, "w", encoding="utf-8") as ofd:
                        ofd.write(result)
            else:
                fq_dest_file = os.path.join(dest_root, src_file)
                fq_dest_file = fq_dest_file.format(**kwargs)
                logging.get_logger().info(f"copy({fq_src_file},{fq_dest_file})")
                if not dry_run:
                    shutil.copyfile(fq_src_file, fq_dest_file)
