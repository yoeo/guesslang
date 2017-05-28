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


setup(
    name="guesslang",
    author="Y. SOMDA",
    version=version('guesslang'),
    url="https://github.com/yoeo/guesslang",
    description="Guess a source code programming language",
    long_description=Path('README.md').read_text(),
    license="MIT",
    install_requires=Path('requirements.txt').read_text(),
    packages=find_packages(exclude=['tests', 'tools']),
    data_files=[('config', Path('config').glob('**/*'))],
    setup_requires=['pytest-runner'],
    tests_require=Path('requirements-test.txt').read_text(),
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
