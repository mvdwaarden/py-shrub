from setuptools import setup, find_namespace_packages
from pathlib import Path

parent_dir = Path(__file__).parent

# Get the version info in package_info.py
full_filename = parent_dir / "src" / "shrub_util" / "package_info.py"
default_requirements = parent_dir / "requirements" / "default.txt"

package_info_vars = {}
with full_filename.open("r", encoding="utf-8") as f:
    exec(f.read(), package_info_vars)

with default_requirements.open("r", encoding="utf-8") as f:
    requires = f.read().splitlines()

setup(
    name=package_info_vars["__title__"],
    version=package_info_vars["__version__"],
    description=package_info_vars["__description__"],
    author=package_info_vars["__author__"],
    install_requires=requires,
    author_email=package_info_vars["__author_email__"],
    package_dir={"": "src"},
    include_package_data=True,
    packages=find_namespace_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    # disable until setuptools_scm version check is fixed or we have implemented a work-around
    # use_scm_version={
    #    "root": "..",
    #    "relative_to": __file__
    # },
    # setup_requires=['setuptools_scm'],
    python_requires='>=3.6'
)




