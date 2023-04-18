#!/bin/bash

# Path to the virtual environment
VENV_PATH="/path/to/your/venv"

# Activate the virtual environment
source "${VENV_PATH}/bin/activate"

# Run pytest or any other test command
exec python -m pytest "$@"
