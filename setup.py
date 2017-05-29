#!/usr/bin/env python3

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
    name="guesslang",
    author="Y. SOMDA",
    version=version('guesslang'),
    url="https://github.com/yoeo/guesslang",
    description="Detect the programming language of a source code",
    long_description=long_description(
        'docs/index.rst', 'end-description',
        'https://guesslang.readthedocs.io/en/latest/'),
    license="MIT",
    install_requires=Path('requirements.txt').read_text(),
    packages=find_packages(exclude=['tests', 'tools']),
    data_files=[
        ('config', [
            str(filename) for filename in Path('config').glob('**/*')
            if filename.is_file()])],
    setup_requires=['pytest-runner'],
    tests_require=Path('requirements-dev.txt').read_text(),
    platforms='any',
    zip_safe=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
        'console_scripts': ['guesslang = guesslang.__main__:main']
    },
)
