#!/usr/bin/env python

import os
import re
import sys
from setuptools import setup
import setuptools

"""
py -m pip install twine  # 您将需要它来将您的项目分发上传到PyPI
# 打包为 whl文件
py -m build --wheel
"""

_version_re = re.compile(r"__version__\s+=\s+(.*)")

PY_VER = sys.version_info

if PY_VER < (3, 6):
    raise RuntimeError("Yjsdl doesn't support Python version prior 3.6")


def read_version():
    regexp = re.compile(r'^__version__\W*=\W*"([\d.abrc]+)"')
    init_py = os.path.join(os.path.dirname(__file__), "Yjsdl", "__init__.py")
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)


def read(file_name):
    with open(
            os.path.join(os.path.dirname(__file__), file_name), mode="r", encoding="utf-8"
    ) as f:
        return f.read()


packages = setuptools.find_packages()
packages.extend([
    "Yjsdl",
    "Yjsdl.templates",
    "Yjsdl.templates.project_template",
    "Yjsdl.templates.project_template.spiders"
])

setup(
    name="Yjsdl",
    version=read_version(),
    author="Yjsdl",
    description="平生一顾，至此终年",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author_email="yj160521@163.com",
    python_requires=">=3.6",
    install_requires=["aiohttp>=3.5.4", "lxml", 'aiofiles', 'aiocsv'],
    packages=packages,
    package_data={
        "tmpl": ["./*.tmpl"],
    },
    url="https://github.com/yjsdl",
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    extras_require={"uvloop": ["uvloop"]},
    entry_points={"console_scripts": ["yjsdl = Yjsdl.extend.cmd.cmdline:execute",
                                      "Yjsdl = Yjsdl.extend.cmd.cmdline:execute"]}

)
