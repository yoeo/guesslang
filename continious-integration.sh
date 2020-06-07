#/bin/bash

set -ex

# install dependencies
pip install -r requirements-dev.txt

# run tests
python setup.py test

# check static types
mypy --strict --ignore-missing-imports guesslang/

# check code quality (pylint is disabled for now...)
#   pylint guesslang/
flake8 guesslang/
