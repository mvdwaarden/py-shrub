from setuptools import setup, find_namespace_packages
import os
from pathlib import Path
import re


parent_dir = Path(__file__).parent

# Get the version info in package_info.py
full_filename = parent_dir / "src" / "shrub_services" / "package_info.py"
default_requirements = parent_dir / "requirements" / "default.txt"

package_info_vars = {}
with full_filename.open("r", encoding="utf-8") as f:
    exec(f.read(), package_info_vars)

with default_requirements.open("r", encoding="utf-8") as f:
    requires = f.read().splitlines()

def get_files(folder, pattern=".*"):
    regex = re.compile(pattern, re.RegexFlag.IGNORECASE)
    result = []
    for entry in os.listdir(folder):
        fq_entry = os.path.join(folder, entry)
        if os.path.isfile(fq_entry) and regex.fullmatch(entry):
            result.append(fq_entry)

    return result

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
    python_requires='>=3.6',
     data_files=[
        (
            "sbin",
            [
                "sbin/startup.cmd"
            ],
        ),
        (
            f"data/{package_info_vars['__package_name__']}",
            get_files(f"data/{package_info_vars['__package_name__']}")
        )
    ]
)



