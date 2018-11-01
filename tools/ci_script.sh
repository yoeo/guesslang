#/bin/bash

STATUS=0

# install dependencies
pip install -r requirements-dev.txt || STATUS=$?

# run tests
python setup.py test || STATUS=$?

# check static types
mypy --strict --ignore-missing-imports guesslang/ || STATUS=$?

# check code quality (pylint is disabled for now...)
#   pylint guesslang/ || STATUS=$?
flake8 guesslang/ || STATUS=$?

# propagate execution status
exit $STATUS
