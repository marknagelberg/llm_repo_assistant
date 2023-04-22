#!/bin/bash

# Path to the virtual environment
VENV_PATH="/path/to/your/venv"

# Activate the virtual environment
source "${VENV_PATH}/bin/activate"

TEST_DIRECTORY="./top/dir/where/tests/live"

# Run pytest or any other test command
exec python -m pytest $(TEST_DIRECTORY) "$@"
