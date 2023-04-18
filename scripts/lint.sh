#!/usr/bin/env bash

set -x

mypy src
black src --check
isort --recursive --check-only src
flake8
