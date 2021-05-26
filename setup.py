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


def version(base_module: str) -> str:
    version_pattern = r'__version__\s+=\s+(.*)'
    init_path = Path(Path(__file__).parent, base_module, '__init__.py')
    found = re.search(version_pattern, init_path.read_text())
    if not found:
        raise RuntimeError(f'{base_module} version not found')

    repr_value = found.group(1)
    return str(ast.literal_eval(repr_value))


def long_description(filename: str, end_tag: str, doc_url: str) -> str:
    lines = []
    for line in Path(filename).read_text().splitlines():
        if end_tag in line:
            break

        lines.append(line)

    lines.append('Full documentation at {}'.format(doc_url))
    return '\n'.join(lines)


setup(
    # Package info
    name='guesslang',
    author='Y. SOMDA',
    url='https://github.com/yoeo/guesslang',
    description='Detect the programming language of a source code',
    long_description=long_description(
        'docs/contents.rst',
        'end-description',
        'https://guesslang.readthedocs.io/en/latest/',
    ),
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    # Install setup
    version=version('guesslang'),
    platforms='any',
    packages=find_packages(exclude=['tests', 'tools']),
    install_requires=Path('requirements.txt').read_text(),
    zip_safe=False,
    include_package_data=True,
    scripts=['bin/guesslang'],
    # Test setup
    tests_require=Path('requirements-dev.txt').read_text(),
    setup_requires=['pytest-runner']
)
