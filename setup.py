#!/usr/bin/env python3
"""
Setup Guesslang

* Install with pip (recommended):
    pip install .

* Install with setuptools:
    pip install -r requirements.txt
    python setup.py install

* Run tests:
    python setup.py pytest

"""

import ast
from pathlib import Path
import re

from setuptools import setup, find_packages


def version(base_module):
    version_pattern = r'__version__\s+=\s+(.*)'
    init_path = Path(Path(__file__).parent, base_module, '__init__.py')
    repr_value = re.search(version_pattern, init_path.read_text()).group(1)
    return ast.literal_eval(repr_value)


def long_description(filename, end_tag, doc_url):
    lines = []
    for line in Path('docs/index.rst').read_text().splitlines():
        if end_tag in line:
            break

        lines.append(line)

    lines.append("Full documentation at {}".format(doc_url))
    return '\n'.join(lines)


setup(
    # Package info
    name="guesslang",
    author="Y. SOMDA",
    url="https://github.com/yoeo/guesslang",
    description="Detect the programming language of a source code",
    long_description=long_description(
        'docs/index.rst', 'end-description',
        "https://guesslang.readthedocs.io/en/latest/"
    ),
    license="MIT",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    # Install setup
    version=version('guesslang'),
    platforms='any',
    packages=find_packages(exclude=['tests', 'tools']),
    install_requires=Path('requirements.txt').read_text(),
    zip_safe=True,
    include_package_data=True,
    package_data={
        '': ['requirements*.txt'],
        'docs': ['docs/index.rst'],
        'guesslang/data': ['guesslang/data/*'],
        'guesslang/data/model': ['guesslang/data/model/*']
    },
    entry_points={
        'console_scripts': ['guesslang = guesslang.__main__:main']
    },
    # Test setup
    tests_require=Path('requirements-dev.txt').read_text(),
    setup_requires=['pytest-runner']
)
